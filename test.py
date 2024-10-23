from database.sql_db.conn import pool


def get_user_info(user_name):
    heads = (
        'user_id',
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


a  = get_user_info('admin')
print(a)
