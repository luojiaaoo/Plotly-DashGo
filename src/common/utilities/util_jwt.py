from config.dashgo_conf import JwtConf
from typing import Dict, Union, Optional
from datetime import timedelta, datetime, timezone
import jwt
from dash import set_props
import dash
from enum import Enum
from flask import request


class AccessFailType(Enum):
    EXPIRED = 0
    INVALID = 1
    NO_ACCESS = 2


def jwt_encode(data: Dict, expires_delta: Optional[timedelta] = None):
    """
    生成JWT编码的数据。

    复制原始数据字典以避免修改输入参数，并根据过期时间增量设置过期时间。

    参数:
    - data: Dict, 要编码的数据。
    - expires_delta: Optional[timedelta], 过期时间增量。如果未提供，则使用默认的过期时间。

    返回:
    - encoded_jwt: 编码后的JWT字符串。

    异常:
    - ValueError: 如果expires_delta不是timedelta类型或None。
    """
    to_encode = data.copy()
    if expires_delta is None:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JwtConf.JWT_EXPIRE_MINUTES)
        to_encode.update({'exp': expire})
    elif expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({'exp': expire})
    else:
        raise ValueError('expires_delta must be a timedelta or None')
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


def jwt_encode_save_access_to_session(data: Dict, expires_delta: Optional[timedelta] = None, session_permanent: bool = False) -> None:
    """
    生成JWT访问令牌并将其保存到会话中。

    该函数通过提供的数据生成一个JWT访问令牌，并将该令牌保存到用户会话中。
    它还允许通过设置session_permanent参数来确定会话是否应被视为永久的。

    参数:
    - data: Dict, 用于生成JWT访问令牌的载荷数据。
    - expires_delta: Optional[timedelta], 可选参数，指定令牌的过期时间。
    - session_permanent: bool, 可选参数，指示会话是否为永久会话。

    返回:
    - NoReturn, 该函数不返回任何值。
    """
    access_token = jwt_encode(data, expires_delta=expires_delta)
    dash.ctx.response.set_cookie('Authorization', f'Bearer {access_token}', max_age=3600 * 24 * 365 if session_permanent else None)


def jwt_decode_from_session(verify_exp: bool = True) -> Union[Dict, AccessFailType]:
    """
    从会话中解码JWT（JSON Web Token）。

    根据会话中的授权信息解码JWT，以获取访问令牌的数据部分。
    如果验证失败或令牌过期，则返回相应的错误类型。

    参数:
    - verify_exp (bool): 是否验证JWT的过期时间，默认为True。

    返回:
    - Union[Dict, AccessFailType]: 解码后的JWT数据（字典类型），
      或者访问失败的错误类型（AccessFailType枚举）。
    """
    from jwt.exceptions import ExpiredSignatureError
    # 因为不是每个组件都能加headers，所以还是也校验cookies中的token
    access_token_ = token_ if (token_:=request.headers.get('Authorization')) else request.cookies.get('Authorization')
    if not access_token_:
        return AccessFailType.NO_ACCESS
    else:
        if 'Bearer' in access_token_:
            access_token = access_token_.split()[1]
        else:
            # TODO: 未来可能会支持其他类型的令牌
            raise NotImplementedError('Unsupported token type')
        try:
            access_data = jwt_decode(access_token, verify_exp=verify_exp)
        except ExpiredSignatureError:
            return AccessFailType.EXPIRED
        except Exception:
            return AccessFailType.INVALID
        return access_data


def clear_access_token_from_session() -> None:
    """
    从会话中清除访问令牌。

    该函数从用户会话中删除访问令牌，以注销用户。

    返回:
    - None, 该函数不返回任何值。
    """
    dash.ctx.response.set_cookie('Authorization', '', expires=0)
