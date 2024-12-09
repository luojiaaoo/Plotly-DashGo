from common.utilities.util_logger import Log
from i18n import t__other


logger = Log.get_logger(__name__)


class NotFoundUserException(Exception):
    """
    找不到该用户
    """

    def __init__(self, message: str = None, data: str = None):
        self.message = message
        self.data = data


class AuthException(Exception):
    """
    jwt令牌授权异常
    """

    def __init__(self, message: str = None, data: str = None):
        self.message = message
        self.data = data


def global_exception_handler(error):
    from dash import set_props
    from common.utilities import util_jwt
    import feffery_antd_components as fac

    if isinstance(error, NotFoundUserException) or isinstance(error, AuthException):
        util_jwt.clear_access_token_from_session()
        set_props('global-message-container', {'children': fac.AntdMessage(content='AuthException: {}'.format(error.message), type='error')})
        set_props('global-token-err-modal', {'visible': True})
    else:
        logger.exception(f'[exception]{error}')
        set_props('global-notification-container', {'children': fac.AntdNotification(message=t__other('系统异常'), description=str(error), type='error')})
