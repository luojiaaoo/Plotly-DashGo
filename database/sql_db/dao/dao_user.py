from database.sql_db.conn import pool
from typing import Dict, List, Set, Union, Optional
from itertools import chain, repeat
from dataclasses import dataclass
from datetime import datetime
from common.utilities import util_menu_access
import json
from common.utilities.util_logger import Log
from common.utilities.util_menu_access import get_menu_access

logger = Log.get_logger(__name__)


class Status:
    ENABLE = 1
    DISABLE = 0


def exists_user_name(user_name: str) -> bool:
    """是否存在这个用户名"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT user_name FROM sys_user WHERE user_name = %s;""",
            (user_name,),
        )
        result = cursor.fetchone()
        return result is not None


def user_password_verify(user_name: str, password_sha256: str) -> bool:
    """密码校验，排除未启用账号"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT user_name FROM sys_user WHERE user_name = %s and password_sha256 = %s and user_status = %s;""",
            (user_name, password_sha256, Status.ENABLE),
        )
        result = cursor.fetchone()
        return result is not None


def get_all_access_meta_for_setup_check() -> Set[str]:
    """获取所有权限，对应用权限检查"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""SELECT access_metas FROM sys_role;""")
        result = cursor.fetchall()
        return set(chain(*[json.loads(per_rt[0]) for per_rt in result]))


########################### 用户
@dataclass
class UserInfo:
    user_name: str
    user_full_name: str
    user_status: str
    user_sex: str
    user_roles: List
    user_email: str
    phone_number: str
    update_datetime: datetime
    update_by: str
    create_datetime: datetime
    create_by: str
    user_remark: str


def get_user_info(user_names: Optional[List] = None, exclude_role_admin=False, exclude_disabled=False) -> List[UserInfo]:
    """获取用户信息对象"""
    heads = [
        'user_name',
        'user_full_name',
        'user_status',
        'user_sex',
        'user_email',
        'phone_number',
        'update_datetime',
        'update_by',
        'create_datetime',
        'create_by',
        'user_remark',
    ]
    with pool.get_connection() as conn, conn.cursor() as cursor:
        sql = f"""
            SELECT {','.join(['u.'+i for i in heads])}, JSON_ARRAYAGG(ur.user_role) as user_roles
            FROM sys_user u JOIN sys_user_role ur 
            on u.user_name = ur.user_name
        """
        sql_place = []
        if user_names is not None:
            sql += f" WHERE user_name in ({','.join(['%s']*len(user_names))})"
            sql_place.extend(user_names)
        if exclude_role_admin:
            sql += " AND JSON_SEARCH(user_roles, 'one', %s) IS NULL"
            sql_place.append('admin')
        if exclude_disabled:
            sql += ' AND user_status=%s'
            sql_place.append(Status.ENABLE)
        cursor.execute(sql, sql_place)
        user_infos = []
        result = cursor.fetchall()
        for per in result:
            user_dict = dict(zip(heads + ['user_roles'], per))
            user_dict.update(
                {
                    'user_roles': json.loads(user_dict['user_roles']),
                },
            )
            user_infos.append(UserInfo(**user_dict))
        return user_infos


def add_role_for_user(user_name: str, role_name: str):
    """给用户添加权限"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            is_ok = True
            # 给sys_role表加锁，保证加入的角色都存在
            if is_ok:
                cursor.execute(
                    'select * from sys_role r join sys_role_access_meta ram on r.role_name=ram.role_name WHERE r.role_name = %s for update;',
                    (role_name,),
                )
                if cursor.fetchall()[0][0] != 1:
                    is_ok = False
            if is_ok:
                cursor.execute(
                    'insert into sys_user_role(user_name,role_name) values(%s,%s);',
                    (user_name, role_name),
                )
        except Exception:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}给用户{user_name}添加角色{role_name}时，出现异常', exc_info=True)
            conn.rollback()
            return False
        else:
            conn.commit()
            return is_ok


def del_role_for_user(user_name, role_name):
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            cursor.execute(
                'delete from sys_user_role where role_name=%s and user_name=%s',
                (role_name, user_name),
            )
        except Exception:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}给用户{user_name}删除角色{role_name}时，出现异常', exc_info=True)
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


def update_user(user_name, user_full_name, password, user_status: bool, user_sex, user_roles, user_email, phone_number, user_remark):
    from hashlib import sha256

    user_name_op = util_menu_access.get_menu_access(only_get_user_name=True)
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            is_ok = True
            # 给sys_role表加锁，保证加入的角色和团队都存在
            if is_ok and user_roles:
                cursor.execute(
                    f'select r.role_name from sys_role r join sys_role_access_meta ram on r.role_name=ram.role_name group by r.role_name having r.role_name in ({','.join(['%s']*len(user_roles))}) for update;',
                    tuple(user_roles),
                )
                if len(list(cursor.fetchall())) != len(user_roles):
                    is_ok = False
            if is_ok:
                cursor.execute(
                    f"""
                    update sys_user 
                    set 
                    user_full_name=%s,{'password_sha256=%s,' if password else ''} user_status=%s, user_sex=%s, user_email=%s,
                    phone_number=%s, update_by=%s, update_datetime=%s, user_remark=%s where user_name=%s;""",
                    (
                        user_full_name,
                        *([sha256(password.encode('utf-8')).hexdigest()] if password else []),
                        user_status,
                        user_sex,
                        user_email,
                        phone_number,
                        user_name_op,
                        datetime.now(),
                        user_remark,
                        user_name,
                    ),
                )
                cursor.execute('delete from sys_user_role where user_name = %s', (user_name,))
                cursor.execute(f'INSERT INTO sys_user_role (user_name, role_name) VALUES {','.join(['(%s,%s)']*len(user_roles))}', chain(*zip(repeat(user_name), user_roles)))
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新用户{user_name}时，出现异常', exc_info=True)
            conn.rollback()
            return False
        else:
            conn.commit()
            return is_ok


def add_user(
    user_name: str,
    user_full_name: str,
    password: str,
    user_status: bool,
    user_sex: str,
    user_roles: List[str],
    user_email: str,
    phone_number: str,
    user_remark: str,
) -> bool:
    """新建用户"""
    import hashlib

    if not user_name or not user_full_name:
        return False
    password = password.strip()
    user_name_op = util_menu_access.get_menu_access().user_name
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            is_ok = True
            # 给sys_role表加锁，保证加入的角色都存在
            if is_ok and user_roles:
                cursor.execute(
                    f"""SELECT count(1) FROM sys_role WHERE role_name in ({','.join(['%s']*len(user_roles))}) for update;""",
                    tuple(user_roles),
                )
                if cursor.fetchall()[0][0] != len(user_roles):
                    is_ok = False
            if is_ok:
                cursor.execute(
                    """
                    INSERT INTO sys_user (user_name, user_full_name ,password_sha256, user_status, user_sex, user_roles, user_email, phone_number, create_by, create_datetime, update_by, update_datetime, user_remark) 
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    ;""",
                    (
                        user_name,
                        user_full_name,
                        hashlib.sha256(password.encode('utf-8')).hexdigest(),
                        get_status_str(user_status),
                        user_sex,
                        json.dumps(user_roles, ensure_ascii=False),
                        user_email,
                        phone_number,
                        user_name_op,
                        datetime.now(),
                        user_name_op,
                        datetime.now(),
                        user_remark,
                    ),
                )
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            return is_ok


def delete_user(user_name: str) -> bool:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            # 删除用户行
            cursor.execute(
                """delete FROM sys_user where user_name=%s;""",
                (user_name,),
            )
            # 删除团队的用户
            cursor.execute(
                """
                UPDATE sys_group
                SET group_users = JSON_REMOVE(group_users, JSON_UNQUOTE(JSON_SEARCH(group_users, 'one', %s)))
                WHERE JSON_SEARCH(group_users, 'one', %s) IS NOT NULL;
                """,
                (user_name,),
            )
            # 删除团队的管理员用户
            cursor.execute(
                """
                UPDATE sys_group
                SET group_admin_users = JSON_REMOVE(group_admin_users, JSON_UNQUOTE(JSON_SEARCH(group_admin_users, 'one', %s)))
                WHERE JSON_SEARCH(group_admin_users, 'one', %s) IS NOT NULL;
                """,
                (user_name,),
            )
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


def filter_users_enabled(user_names):
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            f"""SELECT user_name FROM sys_user WHERE user_name in ({','.join(['%s']*len(user_names))}) and user_status = %s;""",
            (*(user_names), get_status_str(True)),
        )
        return [i[0] for i in cursor.fetchall()]


########################################## 角色


def get_roles_from_user_name(user_name: str, exclude_disabled=False) -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        if exclude_disabled:
            cursor.execute(
                """SELECT user_roles FROM sys_user WHERE user_name = %s and user_status = %s;""",
                (user_name, get_status_str(True)),
            )
        else:
            cursor.execute(
                """SELECT user_roles FROM sys_user WHERE user_name = %s;""",
                (user_name,),
            )
        result = cursor.fetchone()
        role_names = json.loads(result[0])
        return set(filter_roles_enabled(role_names) if exclude_disabled else role_names)


def filter_roles_enabled(role_names):
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            f"""SELECT role_name FROM sys_role WHERE role_name in ({','.join(['%s']*len(role_names))}) and role_status = %s;""",
            (*(role_names), get_status_str(True)),
        )
        return [i[0] for i in cursor.fetchall()]


def get_access_meta_from_roles(role_names: Union[List[str], Set[str]], exclude_disabled=False) -> Set[str]:
    if role_names:
        with pool.get_connection() as conn, conn.cursor() as cursor:
            if exclude_disabled:
                cursor.execute(
                    f"""SELECT access_metas FROM sys_role WHERE role_name in ({','.join(['%s']*len(role_names))}) and role_status = %s;""",
                    (*(role_names), get_status_str(True)),
                )
            else:
                cursor.execute(
                    f"""SELECT access_metas FROM sys_role WHERE role_name in ({','.join(['%s']*len(role_names))});""",
                    tuple(role_names),
                )
            result = cursor.fetchall()
            return set(chain(*[json.loads(per_rt[0]) for per_rt in result]))
    else:
        return set()


def get_user_access_meta_plus_role(user_name: str) -> Set[str]:
    role_names = get_roles_from_user_name(user_name, exclude_disabled=True)
    return get_access_meta_from_roles(role_names, exclude_disabled=True)


@dataclass
class RoleInfo:
    role_name: str
    access_metas: List[str]
    role_status: bool
    update_datetime: datetime
    update_by: str
    create_datetime: datetime
    create_by: str
    role_remark: str


def get_role_info(role_name: str = None, exclude_role_admin=False, exclude_disabled=False) -> List[RoleInfo]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        heads = (
            'role_name',
            'access_metas',
            'role_status',
            'update_datetime',
            'update_by',
            'create_datetime',
            'create_by',
            'role_remark',
        )
        if role_name is None:
            cursor.execute(f"""SELECT {','.join(heads)} FROM sys_role;""")
        else:
            cursor.execute(
                f"""SELECT {','.join(heads)} FROM sys_role where role_name=%s;""",
                (role_name,),
            )
        role_infos = []
        result = cursor.fetchall()
        for per in result:
            role_dict = dict(zip(heads, per))
            role_dict.update(
                {
                    'access_metas': json.loads(role_dict['access_metas']),
                    'role_status': get_status_bool(role_dict['role_status']),
                },
            )
            if exclude_disabled and not role_dict['role_status']:
                continue
            if exclude_role_admin and 'admin' == role_dict['role_name']:
                continue
            role_infos.append(RoleInfo(**role_dict))
        return role_infos


def delete_role(role_name: str) -> bool:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            # 删除角色
            cursor.execute(
                """delete FROM sys_role where role_name=%s;""",
                (role_name,),
            )
            # 删除用户角色
            cursor.execute(
                """
                UPDATE sys_user
                SET user_roles = JSON_REMOVE(user_roles, JSON_UNQUOTE(JSON_SEARCH(user_roles, 'one', %s)))
                WHERE JSON_SEARCH(user_roles, 'one', %s) IS NOT NULL;
                """,
                (role_name, role_name),
            )
            # 删除团队角色
            cursor.execute(
                """
                UPDATE sys_group
                SET group_roles = JSON_REMOVE(group_roles, JSON_UNQUOTE(JSON_SEARCH(group_roles, 'one', %s)))
                WHERE JSON_SEARCH(group_roles, 'one', %s) IS NOT NULL;
                """,
                (role_name, role_name),
            )
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


def add_role(role_name, role_status: bool, role_remark, access_metas):
    if not role_name:
        return False
    user_name_op = util_menu_access.get_menu_access().user_name
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            cursor.execute(
                """
                INSERT INTO sys_role ( role_name, access_metas, role_status, update_datetime, update_by, create_datetime, create_by, role_remark )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s);""",
                (
                    role_name,
                    json.dumps(access_metas, ensure_ascii=False),
                    get_status_str(role_status),
                    datetime.now(),
                    user_name_op,
                    datetime.now(),
                    user_name_op,
                    role_remark,
                ),
            )
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


def exists_role_name(role_name):
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT count(1) FROM sys_role WHERE role_name = %s;""",
            (role_name,),
        )
        result = cursor.fetchone()
        return bool(result[0])


def update_role(role_name, role_status: bool, role_remark, access_metas: List[str]):
    user_name_op = util_menu_access.get_menu_access().user_name
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            cursor.execute(
                """
                update sys_role set access_metas=%s, role_status=%s, update_datetime=%s, update_by=%s, role_remark=%s where role_name=%s;""",
                (json.dumps(access_metas, ensure_ascii=False), get_status_str(role_status), datetime.now(), user_name_op, role_remark, role_name),
            )
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


#################################### 团队


@dataclass
class GroupInfo:
    group_name: str
    group_roles: List[str]
    group_status: bool
    group_users: List[str]
    group_admin_users: List[str]
    update_datetime: datetime
    update_by: str
    create_datetime: datetime
    create_by: str
    group_remark: str


def get_group_info(group_name: str = None) -> List[GroupInfo]:
    heads = (
        'group_name',
        'group_status',
        'group_roles',
        'group_users',
        'group_admin_users',
        'update_datetime',
        'update_by',
        'create_datetime',
        'create_by',
        'group_remark',
    )
    with pool.get_connection() as conn, conn.cursor() as cursor:
        if group_name is None:
            cursor.execute(f"""SELECT {','.join(heads)} FROM sys_group;""")
        else:
            cursor.execute(
                f"""SELECT {','.join(heads)} FROM sys_group WHERE group_name = %s;""",
                (group_name,),
            )
        group_infos = []
        result = cursor.fetchall()
        for per in result:
            group_dict = dict(zip(heads, per))
            group_dict.update(
                {
                    'group_status': get_status_bool(group_dict['group_status']),
                    'group_roles': json.loads(group_dict['group_roles']),
                    'group_users': json.loads(group_dict['group_users']),
                    'group_admin_users': json.loads(group_dict['group_admin_users']),
                },
            )
            group_infos.append(GroupInfo(**group_dict))
        return group_infos


def is_group_admin(user_name) -> bool:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """        
            SELECT count(1)
            FROM sys_group
            WHERE JSON_SEARCH(group_admin_users, 'one', %s) IS NOT NULL and group_status=%s""",
            (user_name, get_status_str(True)),
        )
        result = cursor.fetchone()
        return bool(result[0])


def get_dict_group_name_users_roles(user_name, exclude_disabled=False) -> Dict[str, Union[str, Set]]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """        
            SELECT group_name, group_users, group_roles, group_remark, group_status
            FROM sys_group
            WHERE JSON_SEARCH(group_admin_users, 'one', %s) IS NOT NULL""",
            (user_name,),
        )
        result = cursor.fetchall()
        all_ = []
        for group_name, group_users, group_roles, group_remark, group_status in result:
            group_users = json.loads(group_users)
            group_roles = json.loads(group_roles)
            for user_name in group_users:
                if exclude_disabled and (not group_status or not filter_users_enabled([user_name])):
                    continue
                all_.append(
                    {
                        'group_remark': group_remark,
                        'group_name': group_name,
                        'user_name': user_name,
                        'group_roles': group_roles,
                        'user_roles': list(set(get_roles_from_user_name(user_name, exclude_disabled=True)) & set(group_roles)),
                        'user_full_name': get_user_info(user_name)[0].user_full_name,
                    }
                )
        return all_


def update_user_roles_from_group(user_name, group_name, roles_in_range):
    is_ok = True
    user_roles = set(get_roles_from_user_name(user_name, exclude_disabled=True))
    roles_in_range = set(roles_in_range)
    # 新增的权限
    for i in set(roles_in_range) - user_roles:
        is_ok = is_ok and add_role2user(user_name, i)
    # 需要删除的权限
    for i in user_roles & (set(get_group_info(group_name)[0].group_roles) - roles_in_range):
        is_ok = is_ok and del_role2user(user_name, i)
    return is_ok


def exists_group_name(group_name: str):
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT count(1) FROM sys_group WHERE group_name = %s;""",
            (group_name,),
        )
        result = cursor.fetchone()
        return bool(result[0])


def add_group(group_name, group_status, group_remark, group_roles, group_admin_users, group_users):
    if exists_group_name(group_name):
        return False
    user_name_op = util_menu_access.get_menu_access().user_name
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            is_ok = True
            # 给sys_role表加锁，保证加入的角色都存在
            if is_ok and group_roles:
                cursor.execute(
                    f"""SELECT count(1) FROM sys_role WHERE role_name in ({','.join(['%s']*len(group_roles))}) for update;""",
                    tuple(group_roles),
                )
                if cursor.fetchall()[0][0] != len(group_roles):
                    is_ok = False
            user_names = (*group_admin_users, *group_users)
            # 给用户表加锁，保证加入的成员和管理员都存在
            if is_ok and user_names:
                cursor.execute(
                    f"""SELECT count(1) FROM sys_user WHERE user_name in ({','.join(['%s']*len(user_names))}) for update;""",
                    tuple(user_names),
                )
                if cursor.fetchall()[0][0] != len(user_names):
                    is_ok = False
            else:
                cursor.execute(
                    """
                    INSERT INTO sys_group (group_name, group_status, group_roles, group_users, group_admin_users, update_datetime, update_by, create_datetime, create_by, group_remark) 
                    VALUES 
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                    """,
                    (
                        group_name,
                        get_status_str(group_status),
                        json.dumps(group_roles, ensure_ascii=False),
                        json.dumps(group_users, ensure_ascii=False),
                        json.dumps(group_admin_users, ensure_ascii=False),
                        datetime.now(),
                        user_name_op,
                        datetime.now(),
                        user_name_op,
                        group_remark,
                    ),
                )
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            return is_ok


def delete_group(group_name: str) -> bool:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            cursor.execute(
                """delete FROM sys_group where group_name=%s;""",
                (group_name,),
            )
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


def update_group(group_name, group_status, group_remark, group_roles, group_admin_users, group_users):
    user_name_op = util_menu_access.get_menu_access().user_name
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            is_ok = True
            # 给sys_role表加锁，保证加入的角色都存在
            if is_ok and group_roles:
                cursor.execute(
                    f"""SELECT count(1) FROM sys_role WHERE role_name in ({','.join(['%s']*len(group_roles))}) for update;""",
                    tuple(group_roles),
                )
                if cursor.fetchall()[0][0] != len(group_roles):
                    is_ok = False
            user_names = set([*group_admin_users, *group_users])
            # 给用户表加锁，保证加入的成员和管理员都存在
            if is_ok and user_names:
                cursor.execute(
                    f"""SELECT count(1) FROM sys_user WHERE user_name in ({','.join(['%s']*len(user_names))}) for update;""",
                    tuple(user_names),
                )
                if cursor.fetchall()[0][0] != len(user_names):
                    is_ok = False
            if is_ok:
                cursor.execute(
                    """
                    update sys_group set group_name=%s, group_status=%s, group_roles=%s, group_users=%s, group_admin_users=%s, update_datetime=%s, update_by=%s, group_remark=%s;""",
                    (
                        group_name,
                        get_status_str(group_status),
                        json.dumps(group_roles, ensure_ascii=False),
                        json.dumps(group_users, ensure_ascii=False),
                        json.dumps(group_admin_users, ensure_ascii=False),
                        datetime.now(),
                        user_name_op,
                        group_remark,
                    ),
                )
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            return is_ok
