class AttackException(Exception):
    """
    攻击异常
    """

    def __init__(self, message):
        super().__init__(message)

class NotFoundUsername(Exception):
    """
    找不到该用户
    """

    def __init__(self, message):
        super().__init__(message)