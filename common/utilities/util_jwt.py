from config.dash_melon_conf import JwtConf
from typing import Dict, Union
from datetime import timedelta, datetime, timezone
import jwt


def jwt_encode(data: Dict, expires_delta: Union[timedelta, bool] = True):
    """
    生成JWT编码的数据。

    参数:
    - data: Dict, 要编码的数据。
    - expires_delta: Union[timedelta, bool], 过期时间的增量。如果为布尔值True，则使用默认的过期时间；
                    如果为timedelta实例，则使用该实例指定的过期时间。默认为True。

    返回值:
    - encoded_jwt: 编码后的JWT字符串。
    """
    to_encode = data.copy()
    if isinstance(expires_delta, bool) and expires_delta:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JwtConf.JWT_EXPIRE_MINUTES)
        to_encode.update({'exp': expire})
    elif expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({'exp': expire})

    encoded_jwt = jwt.encode(to_encode, JwtConf.JWT_SECRET_KEY, algorithm=JwtConf.JWT_ALGORITHM)

    return encoded_jwt


def jwt_decode(token, verify_exp: bool = True):
    """
    解码JWT令牌。

    本函数使用PyJWT库对JWT令牌进行解码。您可以指定是否验证令牌的过期时间。

    参数:
    - token: 待解码的JWT令牌字符串。
    - verify_exp: 布尔值，指示是否验证令牌的过期时间，默认为True。

    返回:
    - 解码后的令牌负载（payload）。
    """
    payload = jwt.decode(
        token,
        JwtConf.JWT_SECRET_KEY,
        algorithms=[JwtConf.JWT_ALGORITHM],
        options={'verify_exp': verify_exp},
    )
    return payload
