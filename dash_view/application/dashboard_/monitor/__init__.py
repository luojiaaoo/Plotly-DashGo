from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash import html
from common.utilities.util_menu_access import enter_access_check
from flask_babel import gettext as _  # noqa


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('监控页')


icon = None
order = 2
logger = Log.get_logger(__name__)

@enter_access_check(__name__)
def render_content(menu_access: MenuAccess, **kwargs):
    menu_access.get_access_meta_from_label(__name__, '监控页面')
    return html.Iframe(
        style={
            'width': '100%',
            'height': '100%',
            'borderStyle': 'none',
        },
        src='https://fac.feffery.tech/',
    )
