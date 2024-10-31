class AttackException(Exception):
    """
    攻击异常
    """
    def __init__(self, message):
        super().__init__(message)