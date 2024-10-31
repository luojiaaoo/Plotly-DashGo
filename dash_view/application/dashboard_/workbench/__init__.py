from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from common.utilities.util_menu_access import enter_access_check
from flask_babel import gettext as _  # noqa


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('工作台')


icon = None
order = 1
logger = Log.get_logger(__name__)


@enter_access_check
def render_content(menu_access: MenuAccess, **kwargs):
    access_metas: List[str] = menu_access.get_access_metas(__name__)
    # 获取权限元，根据权限元，用户自定义渲染UI
    access_metas: List[str] = menu_access.get_access_metas(__name__)
    logger.debug(
        f'用户：{menu_access.user_name}，访问：{__name__}，参数列表：{kwargs}，权限元：{access_metas}'
    )
    return str(kwargs)
