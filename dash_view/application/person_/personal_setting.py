from common.utilities.util_menu_access import MenuAccess
from typing import List
from common.utilities.util_logger import Log
from dash import html
from functools import partial
from i18n import translator

_ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
title = '个人设置'
icon = None
logger = Log.get_logger(__name__)
order = 2

access_metas = ('个人设置-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    access_metas: List[str] = menu_access.all_access_metas
    return html.Iframe(
        style={
            'width': '100%',
            'height': '100%',
            'borderStyle': 'none',
        },
        src='https://fac.feffery.tech/',
    )
