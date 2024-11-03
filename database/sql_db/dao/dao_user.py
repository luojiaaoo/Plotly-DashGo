from database.sql_db.conn import pool
from typing import Dict, List, Set, Union
from itertools import chain
from dataclasses import dataclass
from datetime import datetime
import json


def get_status_str(status):
    return '启用' if status == 1 else '禁用'


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


@dataclass
class UserInfo:
    user_name: str
    user_full_name: str
    user_status: str
    user_sex: str
    user_roles: List
    user_groups: Dict
    user_email: str
    phone_number: str
    update_datetime: datetime
    create_by: str
    create_datetime: datetime
    user_remark: str


def get_user_info(user_name: str = None) -> List[UserInfo]:
    heads = (
        'user_name',
        'user_full_name',
        'user_status',
        'user_sex',
        'user_roles',
        'user_groups',
        'user_email',
        'phone_number',
        'update_datetime',
        'create_by',
        'create_datetime',
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
                    'user_groups': json.loads(user_dict['user_groups']),
                    'user_roles': json.loads(user_dict['user_roles']),
                },
            )
            user_infos.append(UserInfo(**user_dict))
        return user_infos


def get_roles_from_user_name(user_name: str) -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT user_roles FROM sys_user WHERE user_name = %s;""",
            (user_name,),
        )
        result = cursor.fetchone()
        return set(json.loads(result[0]))


def get_access_meta_from_roles(roles: Union[List[str], Set[str]]) -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            f"""SELECT access_metas FROM sys_role WHERE role_name in ({','.join(['%s']*len(roles))});""",
            tuple(roles),
        )
        result = cursor.fetchall()
        return set(chain(*[json.loads(per_rt[0]) for per_rt in result]))


def get_user_access_meta_plus_role(user_name: str) -> Set[str]:
    roles = get_roles_from_user_name(user_name)
    return get_access_meta_from_roles(roles)


@dataclass
class RoleInfo:
    role_name: str
    role_status: str
    update_datetime: datetime
    update_by: str
    create_datetime: datetime
    create_by: str
    role_remark: str


def get_role_info(role_name: str = None):
    with pool.get_connection() as conn, conn.cursor() as cursor:
        heads = (
            'role_name',
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
        result = cursor.fetchall()
        return [RoleInfo(**dict(zip(heads, per_rt))) for per_rt in result]


def delete_role(role_name: str) -> bool:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        conn.start_transaction()
        try:
            cursor.execute(
                """delete FROM sys_role where role_name=%s;""",
                (role_name,),
            )
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            return True


def add_role(role_name, role_status, role_remark, access_metas):
    from common.utilities import util_menu_access

    user_name = util_menu_access.get_menu_access().user_name
    with pool.get_connection() as conn, conn.cursor() as cursor:
        conn.start_transaction()
        try:
            cursor.execute(
                """
                INSERT INTO `app`.`sys_role` ( `role_name`, `access_metas`, `role_status`, `update_datetime`, `update_by`, `create_datetime`, `create_by`, `role_remark` )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s);""",
                (
                    role_name,
                    json.dumps(access_metas, ensure_ascii=False),
                    get_status_str(role_status),
                    datetime.now(),
                    user_name,
                    datetime.now(),
                    user_name,
                    role_remark,
                ),
            )
        except Exception as e:
            conn.rollback()
            return False
        else:
            conn.commit()
            return True
