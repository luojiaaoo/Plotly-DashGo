from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash import html

# 二级菜单的标题、图标和显示顺序
title = '个人设置'
icon = None
logger = Log.get_logger(__name__)
order = 2

def render_content(menu_access: MenuAccess, **kwargs):
    access_metas: List[str] = menu_access.get_access_metas(__name__)
    if 'show' not in access_metas:
        return '您没有权限显示该页面'
    return html.Iframe(
        style={
            'width': '100%',
            'height': '100%',
            'borderStyle': 'none',
        },
        src='https://fac.feffery.tech/',
    )
