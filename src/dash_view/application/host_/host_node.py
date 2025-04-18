from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from feffery_dash_utils.style_utils import style
from dash_components import Card
import dash_callback.application.host_.host_node_c
from dash import html


# 二级菜单的标题、图标和显示顺序
title = '主机节点'
icon = None
order = 1
logger = Log.get_logger(__name__)


access_metas = ('主机节点-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return ''