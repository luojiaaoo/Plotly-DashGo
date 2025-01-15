from database.sql_db.conn import db
from typing import Dict, List, Set, Union, Optional, Iterator
from itertools import chain, repeat
from dataclasses import dataclass
from datetime import datetime
from common.utilities import util_menu_access
import json
import hashlib
from peewee import DoesNotExist, fn, MySQLDatabase, SqliteDatabase
from common.utilities.util_logger import Log
from common.utilities.util_menu_access import get_menu_access
from ..entity.table_user import SysUser, SysRoleAccessMeta, SysUserRole

logger = Log.get_logger(__name__)


class Status:
    ENABLE = 1
    DISABLE = 0


def exists_user_name(user_name: str) -> bool:
    """是否存在这个用户名"""
    try:
        SysUser.get(SysUser.user_name == user_name)
        return True
    except DoesNotExist:
        return False


def user_password_verify(user_name: str, password_sha256: str) -> bool:
    """密码校验，排除未启用账号"""
    try:
        SysUser.get((SysUser.user_name == user_name) & (SysUser.password_sha256 == password_sha256) & (SysUser.user_status == Status.ENABLE))
        return True
    except DoesNotExist:
        return False


def get_all_access_meta_for_setup_check() -> List[str]:
    """获取所有权限，对应用权限检查"""
    query: Iterator[SysRoleAccessMeta] = SysRoleAccessMeta.select(SysRoleAccessMeta.access_meta)
    return [role.access_meta for role in query]


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


def get_user_info(user_names: Optional[List[str]] = None, exclude_role_admin=False, exclude_disabled=True) -> List[UserInfo]:
    """获取用户信息对象"""
    database = db()
    if isinstance(database, MySQLDatabase):
        user_roles_agg = (fn.JSON_ARRAYAGG(SysUserRole.role_name).alias('user_roles'),)
        having_exclude_role_admin = fn.JSON_SEARCH(fn.JSON_ARRAYAGG(SysUserRole.role_name), 'one', 'admin').is_null() if exclude_role_admin else (1 == 1)
    elif isinstance(database, SqliteDatabase):
        user_roles_agg = fn.GROUP_CONCAT(SysUserRole.role_name).alias('user_roles')
        having_exclude_role_admin = fn.INSTR(fn.GROUP_CONCAT(SysUserRole.role_name), 'admin') == 0 if exclude_role_admin else (1 == 1)
    else:
        raise NotImplementedError
    query = (
        SysUser.select(
            SysUser.user_name,
            SysUser.user_full_name,
            SysUser.user_status,
            SysUser.user_sex,
            SysUser.user_email,
            SysUser.phone_number,
            SysUser.update_datetime,
            SysUser.update_by,
            SysUser.create_datetime,
            SysUser.create_by,
            SysUser.user_remark,
            user_roles_agg,
        )
        .join(SysUserRole, join_type='LEFT OUTER', on=(SysUser.user_name == SysUserRole.user_name))
        .where(SysUser.user_name.in_(user_names) if user_names is not None else (1 == 1))
        .where(SysUser.user_status == Status.ENABLE if exclude_disabled is not None else (1 == 1))
        .group_by(
            SysUser.user_name,
            SysUser.user_full_name,
            SysUser.user_status,
            SysUser.user_sex,
            SysUser.user_email,
            SysUser.phone_number,
            SysUser.update_datetime,
            SysUser.update_by,
            SysUser.create_datetime,
            SysUser.create_by,
            SysUser.user_remark,
        )
        .having(having_exclude_role_admin)
    )

    user_infos = []
    for user in query.dicts():
        user['user_roles'] = [role for role in json.loads(user['user_roles']) if role]
        if isinstance(database, MySQLDatabase):
            user['user_roles'] = json.loads(user['user_roles'])
        elif isinstance(database, SqliteDatabase):
            user['user_roles'] = user['user_roles'].split(',') if user['user_roles'] else []
        else:
            raise NotImplementedError
        user_infos.append(UserInfo(**user))

    return user_infos


def add_role_for_user(user_name: str, role_name: str):
    """添加用户角色"""
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                'insert into sys_user_role(user_name,role_name) values(%s,%s);',
                (user_name, role_name),
            )
        except Exception:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}给用户{user_name}添加角色{role_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def del_role_for_user(user_name, role_name):
    """删除用户角色"""
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                'delete from sys_user_role where role_name=%s and user_name=%s',
                (role_name, user_name),
            )
        except Exception:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}给用户{user_name}删除角色{role_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user(user_name, user_full_name, password, user_status: bool, user_sex, user_roles, user_email, phone_number, user_remark):
    """更新用户信息"""

    user_name_op = util_menu_access.get_menu_access(only_get_user_name=True)
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                f"""
                    update sys_user 
                    set 
                    user_full_name=%s,{'password_sha256=%s,' if password else ''} user_status=%s,user_sex=%s,user_email=%s,
                    phone_number=%s,update_by=%s,update_datetime=%s,user_remark=%s where user_name=%s;""",
                (
                    user_full_name,
                    *([hashlib.sha256(password.encode('utf-8')).hexdigest()] if password else []),
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
                cursor.execute(f'INSERT INTO sys_user_role (user_name,role_name) VALUES {",".join(["(%s,%s)"]*len(user_roles))}', list(chain(*zip(repeat(user_name), user_roles))))
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新用户{user_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user_full_name(user_name: str, user_full_name: str) -> bool:
    """更新用户全名"""
    user_name_op = util_menu_access.get_menu_access(only_get_user_name=True)
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                """
                    update sys_user 
                    set 
                    user_full_name=%s,update_by=%s,update_datetime=%s where user_name=%s;""",
                (
                    user_full_name,
                    user_name_op,
                    datetime.now(),
                    user_name,
                ),
            )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新用户全名为{user_full_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user_sex(user_name: str, user_sex: str) -> bool:
    """更新用户性别"""
    user_name_op = util_menu_access.get_menu_access(only_get_user_name=True)
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                """
                    update sys_user 
                    set 
                    user_sex=%s,update_by=%s,update_datetime=%s where user_name=%s;""",
                (
                    user_sex,
                    user_name_op,
                    datetime.now(),
                    user_name,
                ),
            )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新用户性别为{user_sex}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user_email(user_name: str, user_email: str) -> bool:
    """更新用户邮箱"""
    user_name_op = util_menu_access.get_menu_access(only_get_user_name=True)
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                """
                    update sys_user 
                    set 
                    user_email=%s,update_by=%s,update_datetime=%s where user_name=%s;""",
                (
                    user_email,
                    user_name_op,
                    datetime.now(),
                    user_name,
                ),
            )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新邮箱为{user_email}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_phone_number(user_name: str, phone_number: str) -> bool:
    """更新用户邮箱"""
    user_name_op = util_menu_access.get_menu_access(only_get_user_name=True)
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                """
                    update sys_user 
                    set 
                    phone_number=%s,update_by=%s,update_datetime=%s where user_name=%s;""",
                (
                    phone_number,
                    user_name_op,
                    datetime.now(),
                    user_name,
                ),
            )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新电话为{phone_number}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user_remark(user_name: str, user_remark: str) -> bool:
    """更新用户描述"""
    user_name_op = util_menu_access.get_menu_access(only_get_user_name=True)
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                """
                    update sys_user 
                    set 
                    user_remark=%s,update_by=%s,update_datetime=%s where user_name=%s;""",
                (
                    user_remark,
                    user_name_op,
                    datetime.now(),
                    user_name,
                ),
            )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新描述为{user_remark}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user_password(user_name: str, new_password: str, old_password: Optional[str] = None):
    if old_password and not user_password_verify(user_name, hashlib.sha256(old_password.encode('utf-8')).hexdigest()):
        return False
    user_name_op = util_menu_access.get_menu_access(only_get_user_name=True)
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                """
                    update sys_user 
                    set 
                    password_sha256=%s,update_by=%s,update_datetime=%s where user_name=%s;""",
                (
                    hashlib.sha256(new_password.encode('utf-8')).hexdigest(),
                    user_name_op,
                    datetime.now(),
                    user_name,
                ),
            )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新密码时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def gen_otp_qrcode(user_name, password: str):
    if not user_password_verify(user_name, password_sha256=hashlib.sha256(password.encode('utf-8')).hexdigest()):
        return False
    import uuid

    otp_secret = str(uuid.uuid4()).replace('-', '')[:16]
    with db().atomic(), db().cursor() as cursor:
        cursor.execute(
            """
                update sys_user
                set 
                otp_secret=%s where user_name=%s;""",
            (
                otp_secret,
                user_name,
            ),
        )
    return otp_secret


def get_otp_secret(user_name):
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                """SELECT otp_secret FROM sys_user WHERE user_name = %s and user_status = %s;""",
                (user_name, Status.ENABLE),
            )
            return cursor.fetchone()[0]
        except:
            return None


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

    if not user_name or not user_full_name:
        return False
    password = password.strip()
    user_name_op = util_menu_access.get_menu_access().user_name
    with db().atomic() as txn, db().cursor() as cursor:
        try:
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
                cursor.execute(f'INSERT INTO sys_user_role (user_name,role_name) VALUES {",".join(["(%s,%s)"]*len(user_roles))}', list(chain(*zip(repeat(user_name), user_roles))))
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}添加用户{user_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def delete_user(user_name: str) -> bool:
    """删除用户"""
    with db().atomic() as txn, db().cursor() as cursor:
        try:
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
            # 删除用户行
            cursor.execute(
                """delete FROM sys_user where user_name=%s;""",
                (user_name,),
            )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}删除用户{user_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def get_roles_from_user_name(user_name: str, exclude_disabled=True) -> List[str]:
    """根据用户查询角色"""
    with db().atomic() as txn, db().cursor() as cursor:
        sql = (
            'SELECT JSON_ARRAYAGG(r.role_name) FROM sys_user u JOIN sys_user_role ur on u.user_name=ur.user_name join sys_role r on ur.role_name = r.role_name where u.user_name=%s'
        )
        sql_place = [user_name]
        if exclude_disabled:
            sql += ' and u.user_status=%s and r.role_status=%s'
            sql_place.extend([Status.ENABLE, Status.ENABLE])
        cursor.execute(sql, sql_place)
        result = cursor.fetchone()
        if result[0] is None:
            return []
        role_names = json.loads(result[0])
        return role_names


def get_user_access_meta(user_name: str, exclude_disabled=True) -> Set[str]:
    """根据用户名查询权限元"""
    with db().atomic() as txn, db().cursor() as cursor:
        sql = 'SELECT JSON_ARRAYAGG(ram.access_meta) FROM sys_user u JOIN sys_user_role ur on u.user_name=ur.user_name join sys_role r on ur.role_name = r.role_name join sys_role_access_meta ram on r.role_name = ram.role_name where u.user_name = %s'
        sql_place = [user_name]
        if exclude_disabled:
            sql += ' and u.user_status=%s and r.role_status=%s'
            sql_place.extend([Status.ENABLE, Status.ENABLE])
        cursor.execute(sql, sql_place)
        result = cursor.fetchone()
        if result[0] is None:
            return set()
        access_metas = json.loads(result[0])
        return set(access_metas)


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
    heads = [
        'role_name',
        'role_status',
        'update_datetime',
        'update_by',
        'create_datetime',
        'create_by',
        'role_remark',
    ]
    with db().atomic() as txn, db().cursor() as cursor:
        sql = f"""
            SELECT {','.join(['r.'+i for i in heads])},JSON_ARRAYAGG(ram.access_meta) as access_metas
            FROM sys_role r left JOIN sys_role_access_meta ram
            on r.role_name = ram.role_name
        """
        group_by = 'GROUP BY r.role_name,r.role_status,r.update_datetime,r.update_by,r.create_datetime,r.create_by,r.role_remark'
        sql_place = []
        condition = []
        if role_names is not None:
            condition.append(f'r.role_name in ({",".join(["%s"]*len(role_names))})')
            sql_place.extend(role_names)
        if exclude_role_admin:
            condition.append('r.role_name != %s')
            sql_place.append('admin')
        if exclude_disabled:
            condition.append('r.role_status=%s')
            sql_place.append(Status.ENABLE)
        cursor.execute(f'{sql} {"where" if condition else ""} {" and ".join(condition)} {group_by}', sql_place)
        role_infos = []
        result = cursor.fetchall()
        for per in result:
            role_dict = dict(zip(heads + ['access_metas'], per))
            role_dict.update(
                {
                    'access_metas': [i for i in json.loads(role_dict['access_metas']) if i],
                },
            )
            role_infos.append(RoleInfo(**role_dict))
        return role_infos


def delete_role(role_name: str) -> bool:
    """删除角色"""
    with db().atomic() as txn, db().cursor() as cursor:
        try:
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
            # 删除角色表
            cursor.execute(
                'delete FROM sys_role where role_name=%s;',
                (role_name,),
            )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}删除角色{role_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def create_role(role_name, role_status: bool, role_remark, access_metas):
    """新建角色"""
    if not role_name:
        return False
    user_name_op = util_menu_access.get_menu_access().user_name
    with db().atomic() as txn, db().cursor() as cursor:
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
                    f'INSERT INTO sys_role_access_meta (role_name,access_meta) VALUES {",".join(["(%s,%s)"]*len(access_metas))}', list(chain(*zip(repeat(role_name), access_metas)))
                )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}创建角色{role_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def exists_role_name(role_name):
    """是否存在角色名称"""
    with db().atomic() as txn, db().cursor() as cursor:
        cursor.execute(
            """SELECT count(1) FROM sys_role WHERE role_name = %s;""",
            (role_name,),
        )
        result = cursor.fetchone()
        return bool(result[0])


def update_role(role_name, role_status: bool, role_remark, access_metas: List[str]):
    """更新角色"""
    user_name_op = util_menu_access.get_menu_access().user_name
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                'update sys_role set role_status=%s,update_datetime=%s,update_by=%s,role_remark=%s where role_name=%s;',
                (role_status, datetime.now(), user_name_op, role_remark, role_name),
            )
            cursor.execute('delete from sys_role_access_meta where role_name = %s', (role_name,))
            if access_metas:
                cursor.execute(
                    f'INSERT INTO sys_role_access_meta (role_name,access_meta) VALUES {",".join(["(%s,%s)"]*len(access_metas))}', list(chain(*zip(repeat(role_name), access_metas)))
                )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新角色{role_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
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
    with db().atomic() as txn, db().cursor() as cursor:
        sql = """
            select g.group_name,group_status,update_datetime,update_by,create_datetime,create_by,group_remark,JSON_ARRAYAGG(role_name) as group_roles,JSON_ARRAYAGG(case gu.is_admin WHEN %s then CONCAT(%s,user_name) else user_name end) as user_name_plus 
            from sys_group g 
            left JOIN sys_group_role gr on g.group_name = gr.group_name 
            left JOIN sys_group_user gu on g.group_name=gu.group_name 
        """
        group_by = 'group by g.group_name,group_status,update_datetime,update_by,create_datetime,create_by,group_remark'
        sql_place = [Status.ENABLE, 'is_admin:']
        condition = []
        if group_names is not None:
            condition.append(f'g.group_name in ({",".join(["%s"]*len(group_names))})')
            sql_place.extend(group_names)
        if exclude_disabled:
            condition.append('group_status=%s')
            sql_place.append(Status.ENABLE)
        cursor.execute(f'{sql} {"where" if condition else ""} {" and ".join(condition)} {group_by}', sql_place)
        group_infos = []
        result = cursor.fetchall()
        for per in result:
            group_dict = dict(zip(heads, per))
            group_dict.update(
                {
                    'group_roles': [i for i in set(json.loads(group_dict['group_roles'])) if i],
                    'user_name_plus': [i for i in set(json.loads(group_dict['user_name_plus'])) if i],
                },
            )
            group_dict.update(
                {
                    'group_users': [i for i in group_dict['user_name_plus'] if not str(i).startswith('is_admin:')],
                    'group_admin_users': [str(i).replace('is_admin:', '') for i in group_dict['user_name_plus'] if str(i).startswith('is_admin:')],
                }
            )
            group_dict.pop('user_name_plus')
            group_infos.append(GroupInfo(**group_dict))
        return group_infos


def is_group_admin(user_name) -> bool:
    """判断是不是团队管理员，排除禁用的团队"""
    with db().atomic() as txn, db().cursor() as cursor:
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


def get_dict_group_name_users_roles(user_name) -> Dict[str, Union[str, Set]]:
    """根据用户名获取可管理的团队、人员和可管理的角色，排除禁用的管理员用户"""
    with db().atomic() as txn, db().cursor() as cursor:
        cursor.execute(
            """        
                select
                a.group_name,
                a.group_remark,
                a.group_roles,
                b.group_user_names,
                b.group_full_names,
                b.group_user_statuses,
                b.group_user_roles
                from
                (
                    select
                    g.group_name,
                    g.group_remark,
                    JSON_ARRAYAGG(gr.role_name) as group_roles
                    from
                    sys_group g
                    join sys_group_role gr on g.group_name = gr.group_name
                    JOIN sys_group_user gu on g.group_name = gu.group_name
                    JOIN sys_user u on gu.user_name = u.user_name
                    JOIN sys_role r on gr.role_name = r.role_name
                    where
                    r.role_status = %s
                    and gu.user_name = %s
                    and g.group_status = %s
                    and gu.is_admin = %s
                    group by
                    g.group_name,
                    g.group_remark
                ) as a
                join (
                    select
                    gu.group_name,
                    JSON_ARRAYAGG(gu.user_name) as group_user_names,
                    JSON_ARRAYAGG(u.user_status) as group_user_statuses,
                    JSON_ARRAYAGG(u.user_full_name) as group_full_names,
                    JSON_ARRAYAGG(u.user_roles) as group_user_roles
                    from
                    sys_group_user gu
                    join (
                        select
                        a.user_name,
                        a.user_full_name,
                        a.user_status,
                        b.user_roles
                        from
                        sys_user a
                        left JOIN (
                            select
                            u.user_name,
                            u.user_status,
                            JSON_ARRAYAGG(ur.role_name) as user_roles
                            from
                            sys_user u
                            left JOIN sys_user_role ur on u.user_name = ur.user_name
                            left JOIN sys_role r on ur.role_name = r.role_name
                            WHERE
                            r.role_status = %s
                            or r.role_status is Null
                            group by
                            u.user_name,
                            u.user_status
                        ) b on a.user_name = b.user_name
                    ) u on gu.user_name = u.user_name
                    group by
                    group_name
                ) b on a.group_name = b.group_name
            """,
            (Status.ENABLE, user_name, Status.ENABLE, Status.ENABLE, Status.ENABLE),
        )
        result = cursor.fetchall()
        all_ = []
        for group_name, group_remark, group_roles, group_user_names, group_user_full_names, group_user_statuses, group_user_role_lists in result:
            group_roles = json.loads(group_roles)
            group_user_names = json.loads(group_user_names)
            group_user_full_names = json.loads(group_user_full_names)
            group_user_statuses = json.loads(group_user_statuses)
            group_user_role_lists = json.loads(group_user_role_lists)
            for user_name, user_full_name, user_status, group_user_role_list in zip(group_user_names, group_user_full_names, group_user_statuses, group_user_role_lists):
                all_.append(
                    {
                        'group_remark': group_remark,
                        'group_name': group_name,
                        'user_name': user_name,
                        'group_roles': group_roles,
                        'user_roles': list(set(group_user_role_list) & set(group_roles)) if group_user_role_list is not None else [],
                        'user_full_name': user_full_name,
                        'user_status': user_status,
                    }
                )
        return all_


def update_user_roles_from_group(user_name, group_name, roles_in_range):
    """再团队授权页，更新用户权限"""
    is_ok = True
    user_roles = set(get_roles_from_user_name(user_name, exclude_disabled=False))
    roles_in_range = set(roles_in_range)
    # 新增的权限
    for i in set(roles_in_range) - user_roles:
        is_ok = True and add_role_for_user(user_name, i)
    # 需要删除的权限
    for i in user_roles & (set(get_group_info([group_name])[0].group_roles) - roles_in_range):
        is_ok = True and del_role_for_user(user_name, i)
    return is_ok


def exists_group_name(group_name: str):
    """是否已经存在这个团队名"""
    with db().atomic() as txn, db().cursor() as cursor:
        cursor.execute(
            """SELECT count(1) FROM sys_group WHERE group_name = %s;""",
            (group_name,),
        )
        result = cursor.fetchone()
        return bool(result[0])


def create_group(group_name, group_status, group_remark, group_roles, group_admin_users, group_users):
    """添加团队"""
    if exists_group_name(group_name):
        return False
    user_name_op = util_menu_access.get_menu_access().user_name
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            user_names = set([*group_admin_users, *group_users])
            cursor.execute(
                """
                INSERT INTO sys_group (group_name,group_status,update_datetime,update_by,create_datetime,create_by,group_remark) 
                VALUES 
                (%s,%s,%s,%s,%s,%s,%s);
                """,
                (
                    group_name,
                    group_status,
                    datetime.now(),
                    user_name_op,
                    datetime.now(),
                    user_name_op,
                    group_remark,
                ),
            )
            # 插入团队角色表
            if group_roles:
                cursor.execute(
                    f'INSERT INTO sys_group_role (group_name,role_name) VALUES {",".join(["(%s,%s)"]*len(group_roles))}', list(chain(*zip(repeat(group_name), group_roles)))
                )
            # 插入团队用户表
            if user_names:
                cursor.execute(
                    f'INSERT INTO sys_group_user (group_name,user_name) VALUES {",".join(["(%s,%s)"]*len(user_names))}', list(chain(*zip(repeat(group_name), user_names)))
                )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}添加团队{group_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def delete_group(group_name: str) -> bool:
    """删除团队"""
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            cursor.execute(
                """delete FROM sys_group_role where group_name=%s;""",
                (group_name,),
            )
            cursor.execute(
                """delete FROM sys_group_user where group_name=%s;""",
                (group_name,),
            )
            cursor.execute(
                """delete FROM sys_group where group_name=%s;""",
                (group_name,),
            )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}删除团队{group_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_group(group_name, group_status, group_remark, group_roles, group_admin_users, group_users):
    """更新团队"""
    user_name_op = util_menu_access.get_menu_access().user_name
    with db().atomic() as txn, db().cursor() as cursor:
        try:
            user_names = set([*group_admin_users, *group_users])
            cursor.execute(
                """
                update sys_group set group_status=%s,update_datetime=%s,update_by=%s,group_remark=%s where group_name=%s;""",
                (
                    group_status,
                    datetime.now(),
                    user_name_op,
                    group_remark,
                    group_name,
                ),
            )
            # 插入团队角色表
            cursor.execute('delete from sys_group_role where group_name = %s', (group_name,))
            if group_roles:
                cursor.execute(
                    f'INSERT INTO sys_group_role (group_name,role_name) VALUES {",".join(["(%s,%s)"]*len(group_roles))}', list(chain(*zip(repeat(group_name), group_roles)))
                )
            # 插入团队用户表
            cursor.execute('delete from sys_group_user where group_name = %s', (group_name,))
            if user_names:
                cursor.execute(
                    f'INSERT INTO sys_group_user (group_name,user_name,is_admin) VALUES {",".join(["(%s,%s,%s)"]*len(user_names))}',
                    list(chain(*zip(repeat(group_name), user_names, [(Status.ENABLE if i in group_admin_users else Status.DISABLE) for i in user_names]))),
                )
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}更新团队{group_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True
