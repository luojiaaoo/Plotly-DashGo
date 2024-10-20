from common.utilities.util_jwt import jwt_decode_from_session
from common.entity.sys_user import UserInfoFromSession


def user_login(user_name: str, password_sha256: str) -> bool:
    print(user_name, password_sha256)
    if (
        user_name == 'admin'
        and password_sha256 == 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'
    ):
        from common.utilities.util_jwt import jwt_encode_save_access_to_session

        jwt_encode_save_access_to_session({'user_name': user_name,'user_id':1,'user_department':'dep1'}, session_permanent=True)
        print(get_user_info_from_session())
        return True
    return False


def get_user_info_from_session() -> UserInfoFromSession:
    return UserInfoFromSession(**jwt_decode_from_session())
