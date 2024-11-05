from database.sql_db.conn import pool
from typing import Dict, List, Set, Union
from itertools import chain
from dataclasses import dataclass
from datetime import datetime
from common.utilities import util_menu_access
import json


def get_status_str(status):
    return '启用' if status == 1 else '禁用'


def get_status_bool(status: str):
    return True if status == '启用' else False


def exists_user_name(user_name: str) -> bool:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT user_name FROM sys_user WHERE user_name = %s;""",
            (user_name,),
        )
        result = cursor.fetchone()
        return result is not None


def user_password_verify(user_name: str, password_sha256: str) -> bool:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT user_name FROM sys_user WHERE user_name = %s and password_sha256 = %s;""",
            (user_name, password_sha256),
        )
        result = cursor.fetchone()
        return result is not None


def get_all_access_meta_for_setup_check() -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT access_metas FROM sys_role
            """
        )
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


def get_user_info(user_name: str = None) -> List[UserInfo]:
    heads = (
        'user_name',
        'user_full_name',
        'user_status',
        'user_sex',
        'user_roles',
        'user_email',
        'phone_number',
        'update_datetime',
        'update_by',
        'create_datetime',
        'create_by',
        'user_remark',
    )
    with pool.get_connection() as conn, conn.cursor() as cursor:
        if user_name is None:
            cursor.execute(f"""SELECT {','.join(heads)} FROM sys_user;""")
        else:
            cursor.execute(
                f"""SELECT {','.join(heads)} FROM sys_user WHERE user_name = %s;""",
                (user_name,),
            )
        user_infos = []
        result = cursor.fetchall()
        for per in result:
            user_dict = dict(zip(heads, per))
            user_dict.update(
                {
                    'user_status': get_status_bool(user_dict['user_status']),
                    'user_roles': json.loads(user_dict['user_roles']),
                },
            )
            user_infos.append(UserInfo(**user_dict))
        return user_infos


def update_user(user_name, user_full_name, password, user_status: bool, user_sex, user_roles, user_email, phone_number, user_remark):
    import hashlib

    user_name_op = util_menu_access.get_menu_access().user_name
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            is_ok = True
            is_finish = False
            # 给sys_role表加锁，保证加入的角色和团队都存在
            if is_ok and user_roles:
                cursor.execute(
                    f"""SELECT count(1) FROM sys_role WHERE role_name in ({','.join(['%s']*len(user_roles))}) for update;""",
                    tuple(user_roles),
                )
                if cursor.fetchall()[0][0] != len(user_roles):
                    is_ok = False
            if is_ok:
                cursor.execute(
                    f"""
                    update sys_user 
                    set 
                    user_full_name=%s,{'password_sha256=%s,' if password else ''} user_status=%s, user_sex=%s,
                    user_roles=%s, user_email=%s,
                    phone_number=%s, update_by=%s, update_datetime=%s, user_remark=%s where user_name=%s;""",
                    (
                        user_full_name,
                        *([hashlib.sha256(password.encode('utf-8')).hexdigest()] if password else []),
                        get_status_str(user_status),
                        user_sex,
                        json.dumps(user_roles, ensure_ascii=False),
                        user_email,
                        phone_number,
                        user_name_op,
                        datetime.now(),
                        user_remark,
                        user_name,
                    ),
                )
                is_finish = True
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            if is_finish:
                return True
            else:
                return False


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
            is_finish = False
            # 给sys_role表加锁，保证加入的角色和团队都存在
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
                is_finish = True
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            if is_finish:
                return True
            else:
                return False


def delete_user(user_name: str) -> bool:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            cursor.execute(
                """delete FROM sys_user where user_name=%s;""",
                (user_name,),
            )
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


########################################## 角色


def get_roles_from_user_name(user_name: str) -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT user_roles FROM sys_user WHERE user_name = %s;""",
            (user_name,),
        )
        result = cursor.fetchone()
        return set(json.loads(result[0]))


def get_access_meta_from_roles(roles: Union[List[str], Set[str]]) -> Set[str]:
    if roles:
        with pool.get_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                f"""SELECT access_metas FROM sys_role WHERE role_name in ({','.join(['%s']*len(roles))});""",
                tuple(roles),
            )
            result = cursor.fetchall()
            return set(chain(*[json.loads(per_rt[0]) for per_rt in result]))
    else:
        return set()


def get_user_access_meta_plus_role(user_name: str) -> Set[str]:
    roles = get_roles_from_user_name(user_name)
    return get_access_meta_from_roles(roles)


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


def get_role_info(role_name: str = None) -> List[RoleInfo]:
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
            role_infos.append(RoleInfo(**role_dict))
        return role_infos


def delete_role(role_name: str) -> bool:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        try:
            cursor.execute(
                """delete FROM sys_role where role_name=%s;""",
                (role_name,),
            )
            cursor.execute(
                """UPDATE sys_user
SET user_roles = JSON_REMOVE(user_roles, JSON_UNQUOTE(JSON_SEARCH(user_roles, 'one', %s)))
WHERE JSON_SEARCH(user_roles, 'one', %s) IS NOT NULL;
                """,
                (
                    role_name,
                    role_name,
                ),
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