from database.sql_db.conn import pool
from typing import Dict, List, Set, Union


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


def get_user_info(user_name: str) -> Dict:
    heads = (
        'user_name',
        'user_full_name',
        'password_sha256',
        'status',
        'sex',
        'avatar_path',
        'groups',
        'type',
        'email',
        'phone_number',
        'create_by',
        'create_datatime',
        'remark',
    )
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            f"""SELECT {','.join(heads)} FROM sys_user WHERE user_name = %s;""",
            (user_name,),
        )
        result = cursor.fetchone()
        return dict(zip(heads, result))


def get_roles_from_user_name(user_name: str) -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT role FROM sys_user_role WHERE user_name = %s;""",
            (user_name,),
        )
        result = cursor.fetchall()
        return set([per_rt[0] for per_rt in result])


def get_menu_item_and_access_meta_from_user_name(user_name: str) -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT access_meta FROM sys_user_access_meta WHERE user_name = %s;""",
            (user_name,),
        )
        result = cursor.fetchall()
        return set([per_rt[0] for per_rt in result])


def get_menu_item_and_access_meta_from_roles(roles: Union[List[str], Set[str]]) -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            f"""SELECT access_meta FROM sys_role WHERE role_name in ({','.join(['%s']*len(roles))});""",
            tuple(roles),
        )
        result = cursor.fetchall()
        return set([per_rt[0] for per_rt in result])


def get_all_menu_item_and_access_meta(user_name: str) -> Set[str]:
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """
                SELECT access_meta
                FROM sys_user_access_meta
                WHERE user_name = %s
                UNION
                SELECT access_meta
                FROM sys_role
                WHERE role_name IN 
                    (SELECT role
                    FROM sys_user_role
                    WHERE user_name = %s);
            """,
            (user_name, user_name),
        )
        result = cursor.fetchall()
        return set([per_rt[0] for per_rt in result])
