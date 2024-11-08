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


def get_all_access_meta_for_setup_check() -> List[str]:
    """获取所有权限，对应用权限检查"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""SELECT access_metas FROM sys_role;""")
        result = cursor.fetchall()
        return chain(*[json.loads(per_rt[0]) for per_rt in result])


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


def get_user_info(user_names: Optional[List] = None, exclude_role_admin=False, exclude_disabled=True) -> List[UserInfo]:
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
            SELECT {','.join(['u.'+i for i in heads])},JSON_ARRAYAGG(ur.user_role) as user_roles
            FROM sys_user u JOIN sys_user_role ur 
            on u.user_name = ur.user_name
        """
        condition = []
        sql_place = []
        if user_names is not None:
            condition.append(f"u.user_name in ({','.join(['%s']*len(user_names))})")
            sql_place.extend(user_names)
        if exclude_role_admin:
            condition.append("JSON_SEARCH(user_roles,'one',%s) IS NULL")
            sql_place.append('admin')
        if exclude_disabled:
            condition.append('u.user_status=%s')
            sql_place.append(Status.ENABLE)
        cursor.execute(f'{sql} where {" and ".join(condition)}', sql_place)
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
    """添加用户角色"""
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
    """删除用户角色"""
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
    """更新用户信息"""
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
                    user_full_name=%s,{'password_sha256=%s,' if password else ''} user_status=%s,user_sex=%s,user_email=%s,
                    phone_number=%s,update_by=%s,update_datetime=%s,user_remark=%s where user_name=%s;""",
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
                if user_roles:
                    cursor.execute(f'INSERT INTO sys_user_role (user_name,role_name) VALUES {','.join(['(%s,%s)']*len(user_roles))}', chain(*zip(repeat(user_name), user_roles)))
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新用户{user_name}时，出现异常', exc_info=True)
            conn.rollback()
            return False
        else:
            conn.commit()
            return is_ok


def create_user(
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
                    """
                    INSERT INTO sys_user (user_name,user_full_name,password_sha256,user_status,user_sex,user_email,phone_number,create_by,create_datetime,update_by,update_datetime,user_remark) 
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                    ;""",
                    (
                        user_name,
                        user_full_name,
                        hashlib.sha256(password.encode('utf-8')).hexdigest(),
                        user_status,
                        user_sex,
                        user_email,
                        phone_number,
                        user_name_op,
                        datetime.now(),
                        user_name_op,
                        datetime.now(),
                        user_remark,
                    ),
                )
                if user_roles:
                    cursor.execute(f'INSERT INTO sys_user_role (user_name,role_name) VALUES {','.join(['(%s,%s)']*len(user_roles))}', chain(*zip(repeat(user_name), user_roles)))
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}添加用户{user_name}时，出现异常', exc_info=True)
            conn.rollback()
            return False
        else:
            conn.commit()
            return is_ok


def delete_user(user_name: str) -> bool:
    """删除用户"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            # 删除用户行
            cursor.execute(
                """delete FROM sys_user where user_name=%s;""",
                (user_name,),
            )
            # 删除用户角色表
            cursor.execute(
                """delete FROM sys_user_role where user_name=%s;""",
                (user_name,),
            )
            # 删除团队的用户
            cursor.execute(
                """delete FROM sys_group_user where user_name=%s;""",
                (user_name,),
            )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}删除用户{user_name}时，出现异常', exc_info=True)
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


def get_roles_from_user_name(user_name: str, exclude_disabled=True) -> List[str]:
    """根据用户查询角色"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        sql = (
            'SELECT JSON_ARRAYAGG(r.role_name) FROM sys_user u JOIN sys_user_role ur on u.user_name=ur.user_name join sys_role r on ur.user_role = r.role_name where u.user_name=%s'
        )
        sql_place = [user_name]
        if exclude_disabled:
            sql += ' and u.user_status=%s and r.role_status=%s'
            sql_place.extend([Status.ENABLE, Status.ENABLE])
        cursor.execute(sql, sql_place)
        result = cursor.fetchone()
        role_names = json.loads(result[0])
        return role_names


def get_user_access_meta(user_name: str, exclude_disabled=True) -> Set[str]:
    """根据用户名查询权限元"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        sql = 'SELECT JSON_ARRAYAGG(ram.access_meta) FROM sys_user u JOIN sys_user_role ur on u.user_name=ur.user_name join sys_role r on ur.user_role = r.role_name join sys_role_access_meta ram on r.role_name = ram.role_name where u.user_name = %s'
        sql_place = [user_name]
        if exclude_disabled:
            sql += ' and u.user_status=%s and r.role_status=%s'
            sql_place.extend([Status.ENABLE, Status.ENABLE])
        cursor.execute(sql, sql_place)
        result = cursor.fetchone()
        access_metas = json.loads(result[0])
        return access_metas


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


def get_role_info(role_names: Optional[List] = None, exclude_role_admin=False, exclude_disabled=True) -> List[RoleInfo]:
    """获取角色信息"""
    heads = (
        'role_name',
        'role_status',
        'update_datetime',
        'update_by',
        'create_datetime',
        'create_by',
        'role_remark',
    )
    with pool.get_connection() as conn, conn.cursor() as cursor:
        sql = f"""
            SELECT {','.join(['u.'+i for i in heads])},JSON_ARRAYAGG(ram.access_meta) as access_metas
            FROM sys_role r JOIN sys_role_access_meta ram
            on r.role_name = ram.role_name
        """
        sql_place = []
        condition = []
        if role_names is not None:
            condition.append(f"r.role_name in ({','.join(['%s']*len(role_names))})")
            sql_place.extend(role_names)
        if exclude_role_admin:
            condition.append('r.role_name != %s')
            sql_place.append('admin')
        if exclude_disabled:
            condition.append('r.role_status=%s')
            sql_place.append(Status.ENABLE)
        cursor.execute(f'{sql} where {" and ".join(condition)}', sql_place)
        role_infos = []
        result = cursor.fetchall()
        for per in result:
            role_dict = dict(zip(heads + ['access_metas'], per))
            role_dict.update(
                {
                    'access_metas': json.loads(role_dict['access_metas']),
                },
            )
            role_infos.append(RoleInfo(**role_dict))
        return role_infos


def delete_role(role_name: str) -> bool:
    """删除角色"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            # 删除角色表
            cursor.execute(
                'delete FROM sys_role where role_name=%s;',
                (role_name,),
            )
            # 删除角色权限表
            cursor.execute(
                'delete FROM sys_role_access_meta where role_name=%s;',
                (role_name,),
            )
            # 删除用户角色表
            cursor.execute(
                'delete FROM sys_user_role where role_name=%s;',
                (role_name,),
            )
            # 删除团队角色表
            cursor.execute(
                'delete FROM sys_group_role where role_name=%s;',
                (role_name,),
            )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}删除角色{role_name}时，出现异常', exc_info=True)
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


def create_role(role_name, role_status: bool, role_remark, access_metas):
    """新建角色"""
    if not role_name:
        return False
    user_name_op = util_menu_access.get_menu_access().user_name
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            cursor.execute(
                """
                INSERT INTO sys_role ( role_name,role_status,update_datetime,update_by,create_datetime,create_by,role_remark)
                VALUES
                (%s,%s,%s,%s,%s,%s,%s);""",
                (
                    role_name,
                    role_status,
                    datetime.now(),
                    user_name_op,
                    datetime.now(),
                    user_name_op,
                    role_remark,
                ),
            )
            if access_metas:
                cursor.execute(
                    f'INSERT INTO sys_role_access_meta (role_name,access_meta) VALUES {','.join(['(%s,%s)']*len(access_metas))}', chain(*zip(repeat(role_name), access_metas))
                )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}创建角色{role_name}时，出现异常', exc_info=True)
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


def exists_role_name(role_name):
    """是否存在角色名称"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT count(1) FROM sys_role WHERE role_name = %s;""",
            (role_name,),
        )
        result = cursor.fetchone()
        return bool(result[0])


def update_role(role_name, role_status: bool, role_remark, access_metas: List[str]):
    """更新角色"""
    user_name_op = util_menu_access.get_menu_access().user_name
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            cursor.execute(
                'update sys_role set role_status=%s,update_datetime=%s,update_by=%s,role_remark=%s where role_name=%s;',
                (role_status, datetime.now(), user_name_op, role_remark, role_name),
            )
            cursor.execute('delete from sys_role_access_meta where role_name = %s', (role_name,))
            if access_metas:
                cursor.execute(f'INSERT INTO role_name (role_name,access_meta) VALUES {','.join(['(%s,%s)']*len(access_metas))}', chain(*zip(repeat(role_name), access_metas)))
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新角色{role_name}时，出现异常', exc_info=True)
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


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


def get_group_info(group_names: Optional[List] = None, exclude_disabled=True) -> List[GroupInfo]:
    """获取团队信息"""
    heads = [
        'group_name',
        'group_status',
        'update_datetime',
        'update_by',
        'create_datetime',
        'create_by',
        'group_remark',
        'group_roles',
        'user_name_plus',
    ]
    with pool.get_connection() as conn, conn.cursor() as cursor:
        sql = """
            select g.group_name,group_status,update_datetime,update_by,create_datetime,create_by,group_remark,JSON_ARRAYAGG(role_name),JSON_ARRAYAGG(case gu.is_admin WHEN %s then CONCAT(%s,user_name) else user_name end) as user_name_plus 
            from sys_group g JOIN sys_group_role gr on g.group_name = gr.group_name JOIN sys_group_user gu on g.group_name=gu.group_name 
        """
        group_by = 'group by g.group_name,group_status,update_datetime,update_by,create_datetime,create_by,group_remark'
        sql_place = [Status.ENABLE, 'is_admin:']
        condition = []
        if group_names is not None:
            condition.append(f'g.group_name in ({','.join(['%s']*len(group_names))})')
            sql_place.extend(group_names)
        if exclude_disabled:
            condition.append('group_status!=%s')
            sql_place.append(Status.ENABLE)
        cursor.execute(f'{sql} where {" and ".join(condition)} {group_by}', sql_place)
        group_infos = []
        result = cursor.fetchall()
        for per in result:
            group_dict = dict(zip(heads, per))
            group_dict.update(
                {
                    'group_roles': list(set(json.loads(group_dict['group_roles']))),
                    'user_name_plus': set(json.loads(group_dict['user_name_plus'])),
                    'group_users': [i for i in group_dict['user_name_plus'] if not str(i).startswith('is_admin:')],
                    'group_admin_users': [str(i).replace('is_admin:', '') for i in group_dict['user_name_plus'] if str(i).startswith('is_admin:')],
                },
            )
            group_dict.pop('user_name_plus')
            group_infos.append(GroupInfo(**group_dict))
        return group_infos


def is_group_admin(user_name) -> bool:
    """判断是不是团队管理员，排除禁用的团队"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """        
                SELECT
                count(1)
                FROM
                sys_group g
                join sys_group_user gu on g.group_name = gu.group_name
                WHERE
                gu.user_name = %s
                and g.group_status = %s
                and gu.is_admin = %s
            """,
            (user_name, Status.ENABLE, Status.ENABLE),
        )
        result = cursor.fetchone()
        return bool(result[0])


def get_dict_group_name_users_roles(user_name, exclude_disabled=False) -> Dict[str, Union[str, Set]]:
    """根据用户名获取可管理的团队、人员和可管理的角色"""
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """        
                select
                a.group_name,
                a.group_remark,
                a.group_roles,
                b.group_user_names,
                b.group_full_names,
                b.group_user_statuses
                from
                (
                    select
                    g.group_name,
                    g.group_remark,
                    JSON_ARRAYAGG (gr.role_name) as group_roles
                    from
                    sys_group g
                    join sys_group_role gr on g.group_name = gr.group_name
                    JOIN sys_group_user gu on g.group_name = gu.group_name
                    JOIN sys_user u on gu.user_name = u.user_name
                    where
                    gu.user_name = %s
                    and g.group_status = %s
                    and gu.is_admin = %s
                    group by
                    g.group_name,
                    g.group_remark
                ) as a
                join (
                    select
                    gu.group_name,
                    JSON_ARRAYAGG (gu.user_name) as group_user_names,
                    JSON_ARRAYAGG (u.user_status) as group_user_statuses,
                    JSON_ARRAYAGG (u.user_full_name) as group_full_names
                    from
                    sys_group_user gu
                    join sys_user u on gu.user_name = u.user_name
                    group by
                    group_name
                ) b on a.group_name = b.group_name
            """,
            (user_name, Status.ENABLE, Status.ENABLE),
        )
        result = cursor.fetchall()
        all_ = []
        for group_name, group_remark, group_roles, group_user_names, group_user_full_names, group_user_status in result:
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
                    INSERT INTO sys_group (group_name,group_status,group_roles,group_users,group_admin_users,update_datetime,update_by,create_datetime,create_by,group_remark) 
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
                    update sys_group set group_name=%s,group_status=%s,group_roles=%s,group_users=%s,group_admin_users=%s,update_datetime=%s,update_by=%s,group_remark=%s;""",
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
