class AttackException(Exception):
    """
    攻击异常
    """

    def __init__(self, data: str = None, message: str = None):
        self.data = data
        self.message = message
