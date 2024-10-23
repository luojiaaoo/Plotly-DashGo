from database.sql_db.conn import pool
from typing import Dict, List, Set, Union


def get_user_info(user_name: str) -> Dict:
    heads = (
        'user_name',
        'user_full_name',
        'user_password_sha256',
        'user_status',
        'user_sex',
        'user_avatar_path',
        'user_groups',
        'user_type',
        'user_roles',
        'user_access_items',
        'user_email',
        'user_phone_number',
        'user_create_by',
        'user_create_datatime',
        'user_remark',
    )
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            f"""SELECT {','.join(heads)} FROM sys_user where user_name = %s;""",
            (user_name,),
        )
        result = cursor.fetchone()
        return dict(zip(heads, result))


def get_roles_from_user_name(user_name: str) -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT user_roles FROM sys_user where user_name = %s;""",
            (user_name,),
        )
        result = cursor.fetchone()
        return set(result[0].split(','))


def get_access_items_from_user_name(user_name: str) -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT user_access_items FROM sys_user where user_name = %s;""",
            (user_name,),
        )
        result = cursor.fetchone()
        return set(result[0].split(','))


def get_access_items_from_roles(roles: Union[List[str], Set[str]]) -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """select role_access_items from sys_role where role_name in %s;""",
            (roles,),
        )
        access_items = set()
        while True:
            result = cursor.fetchone()
            if result is None:
                break
            access_items.update(result[0].split(','))
        return access_items


def get_all_access_items(user_name: str):
    access_items_from_role = get_access_items_from_roles(get_roles_from_user_name(user_name))
    access_items_own = get_access_items_from_user_name(user_name)
    return access_items_own.union(access_items_from_role)
