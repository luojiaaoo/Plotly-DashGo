def user_login(username, password_sha256):
    print(username, password_sha256)
    if (
        username == 'admin'
        and password_sha256 == 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'
    ):
        from common.utilities.util_jwt import jwt_encode_save_access_to_session

        jwt_encode_save_access_to_session({'username': username}, session_permanent=True)
        return True
    return False
