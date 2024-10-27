from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash import html

# 二级菜单的标题和图标
title = '监控页'
icon = None
logger = Log.get_logger(__name__)


def render_content(menu_access: MenuAccess, **kwargs):
    return html.Iframe(
        style={
            'width': '100%',
            'height': '100%',
            'borderStyle': 'none',
        },
        src='https://gushitong.baidu.com/',
    )
