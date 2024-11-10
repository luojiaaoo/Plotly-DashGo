from dash_components.feedback import MessageManager, NotificationManager
from common.utilities.util_logger import Log
from functools import partial
from i18n import translator

_ = partial(translator.t)

logger = Log.get_logger(__name__)


class NotFoundUserException(Exception):
    """
    找不到该用户
    """

    def __init__(self, data: str = None, message: str = None):
        self.data = data
        self.message = message

    def __str__(self):
        return self.message + f'; data: {self.data}' if self.data else ''


class AuthException(Exception):
    """
    jwt令牌授权异常
    """

    def __init__(self, data: str = None, message: str = None):
        self.data = data
        self.message = message

    def __str__(self):
        return self.message + f'; data: {self.data}' if self.data else ''


def global_exception_handler(error):
    if isinstance(error, NotFoundUserException) or isinstance(error, AuthException):
        from dash import set_props
        from common.utilities import util_jwt

        util_jwt.clear_access_token_from_session()
        MessageManager.error(content=error)
        set_props('global-token-err-modal', {'visible': True})
    else:
        logger.exception(f'[exception]{error}')
        NotificationManager.error(description=str(error), message='系统异常')
