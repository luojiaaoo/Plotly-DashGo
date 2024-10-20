from dataclasses import dataclass


@dataclass
class UserInfoFromSession_:
    user_id: int
    user_name: str
    user_department: str


class UserInfoFromSession(UserInfoFromSession_):
    def __init__(self, **kwargs):
        super().__init__(
            user_id=kwargs.get('user_id'),
            user_name=kwargs.get('user_name'),
            user_department=kwargs.get('user_department'),
        )