from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash import html
from dash_components import NiceDiv

# 二级菜单的标题、图标和显示顺序
title = '个人信息'
icon = None
logger = Log.get_logger(__name__)
order = 1


def render_content(menu_access: MenuAccess, **kwargs):
    access_metas: List[str] = menu_access.get_access_metas(__name__)
    return NiceDiv(
        className={
            'width': '100%',
            'height': '100%',
            'backgroundColor': '#000'
        },
    )
