def user_login(user_name: str, password_sha256: str) -> bool:
    from database.sql_db.dao.user import user_password_verify
    from common.utilities.util_jwt import jwt_encode_save_access_to_session

    if user_password_verify(user_name=user_name, password_sha256=password_sha256):
        jwt_encode_save_access_to_session({'user_name': user_name}, session_permanent=True)
        return True
    return False
