from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_utils_components as fuc
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash import html
from server import app
from flask_babel import gettext as _  # noqa
import dash_callback.application.dashboard_.monitor_c


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('监控页')


icon = None
order = 2
logger = Log.get_logger(__name__)

access_metas = ('监控页-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return html.Div(
        [
            fac.AntdParagraph(
                id='monitor-sys-info',
                style={'whiteSpace': 'pre', 'fontSize': 15},
            ),
            fuc.FefferyEventSource(id='monitor-sys-info-sse', url='/stream-sys-monitor', immediate=True),
        ]
    )
