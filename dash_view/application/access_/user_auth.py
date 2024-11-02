from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html
from dash import dcc
from database.sql_db.dao import dao_user
import dash_callback.application.person_.personal_info_c  # noqa
from functools import partial
from i18n import translator

_ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('用户权限')


icon = None
logger = Log.get_logger(__name__)
order = 3

access_metas = ('用户权限-页面',)
