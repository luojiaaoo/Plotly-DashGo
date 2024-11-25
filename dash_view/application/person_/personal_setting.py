from common.utilities.util_menu_access import MenuAccess
from typing import List
from common.utilities.util_logger import Log
from dash import html
from functools import partial
from i18n import translator

__ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
title = '个人设置'
icon = None
logger = Log.get_logger(__name__)
order = 2

access_metas = ('个人设置-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return 'TODO: 快捷导航，用户动态'
