from flask import request, abort, jsonify
from common.constant import HttpStatusConstant
from enum import Enum
from typing import Union, Dict
from .util_jwt import jwt_decode_rt_type, AccessFailType


class AuthType(Enum):
    BEARER = 'Bearer'
    DIGEST = 'Digest'


def auth_validate(verify_exp=True) -> tuple[AuthType, Union[Dict, AccessFailType]]:
    # 因为不是每个组件都能加headers，所以还是也校验cookies中的token
    auth_header = token_ if (token_ := request.headers.get('Authorization')) else request.cookies.get('Authorization')
    if not auth_header:
        return AccessFailType.NO_ACCESS
    auth_info = auth_header.split(' ', 1)
    if len(auth_info) != 2 or not auth_info[0].strip() or not auth_info[1].strip():
        abort(HttpStatusConstant.BAD_REQUEST)
    auth_type, auth_token = auth_info
    if auth_type == AuthType.BEARER.value:
        # jwt验证
        return jwt_decode_rt_type(auth_token, verify_exp=verify_exp)
    elif auth_type == AuthType.DIGEST.value:
        # Basic认证
        return validate_basic(auth_token)
    abort(jsonify({'error': f'Unsupport Type {auth_type}'}), HttpStatusConstant.UNSUPPORTED_TYPE)


# Basic认证
def validate_basic(auth_token):
    import base64
    from database.sql_db.dao import dao_user
    from otpauth import TOTP
    import re

    decoded_token = base64.b64decode(auth_token).decode('utf-8')
    user_name, password = decoded_token.split(':', 1)
    if dao_user.user_password_verify(user_name, password) or (
        (otp_secret := dao_user.get_otp_secret(user_name)) and re.match(r'^\d+$', password) and TOTP(otp_secret.encode()).verify(int(password))
    ):
        return {'user_name': user_name}
    else:
        return AccessFailType.INVALID
