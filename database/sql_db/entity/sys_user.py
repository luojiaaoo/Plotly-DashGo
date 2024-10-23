from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserInfoFromSession_:
    user_name: str


class UserInfoFromSession(UserInfoFromSession_):
    def __init__(self, **kwargs):
        super().__init__(
            user_name=kwargs.get('user_name'),
        )

@dataclass
class SysUser:
    user_name: int
    user_full_name: str
    user_password_sha256: str
    user_status: str
    user_sex: str
    user_avatar_path: str
    user_groups: dict
    user_type: str
    user_roles: str
    user_access_items: str
    user_email: str
    user_phone_number: str
    user_create_by: str
    user_create_datatime: datetime
    user_remark: str
