from database.sql_db.conn import pool
from typing import Dict, List, Set, Union
from dataclasses import dataclass
from datetime import datetime


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


@dataclass
class UserInfo:
    user_name: str
    user_full_name: str
    status: str
    sex: str
    groups: List
    user_type: str
    email: str
    phone_number: str
    create_by: str
    create_datetime: datetime
    remark: str


def get_user_info(user_name: str) -> UserInfo:
    heads = (
        'user_name',
        'user_full_name',
        'status',
        'sex',
        'groups',
        'user_type',
        'email',
        'phone_number',
        'create_by',
        'create_datetime',
        'remark',
    )
    with pool.get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            f"""SELECT {','.join(heads)} FROM sys_user WHERE user_name = %s;""",
            (user_name,),
        )
        result = cursor.fetchone()
        user_dict = dict(zip(heads, result))
        user_dict.update({'groups': user_dict['groups'].split(',')})
        return UserInfo(**user_dict)


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


def get_user_menu_item_and_access_meta(user_name: str) -> Set[str]:
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

