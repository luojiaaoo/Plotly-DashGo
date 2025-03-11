from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html
from dash_components import Card
from dash import dcc
from database.sql_db.dao import dao_user
from i18n import t__person, t__default, t__access


# 二级菜单的标题、图标和显示顺序
title = '公告管理'
icon = None
logger = Log.get_logger(__name__)
order = 1
access_metas = ('公告管理-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    ...