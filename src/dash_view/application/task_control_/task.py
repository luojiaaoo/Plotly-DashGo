from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
import dash_callback.application.person_.personal_info_c  # noqa


# 二级菜单的标题、图标和显示顺序
title = '任务管理'
icon = None
logger = Log.get_logger(__name__)
order = 1
access_metas = ('任务管理-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return
