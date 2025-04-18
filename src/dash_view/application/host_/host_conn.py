from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from feffery_dash_utils.style_utils import style
from dash_components import Card
import dash_callback.application.host_.host_conn_c  # noqa: F401
from dash import html


# 二级菜单的标题、图标和显示顺序
title = '主机连接'
icon = None
order = 2
logger = Log.get_logger(__name__)


access_metas = ('主机连接-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return [
        fuc.FefferyStyle(
            rawStyle="""
        .terminal {
            border: #000 solid 5px;
            font-family: cursive;
            font-size: 15px;
            background: #000;
            box-shadow: rgba(0, 0, 0, 0.8) 2px 2px 20px;
            height: 100%;
            width: 100%;
        }
        .reverse-video {
            color: #000;
            background: #f0f0f0;
        }
"""
        ),
        fac.AntdRow(
            [
                fac.AntdCol(
                    [
                        html.Div(id='host-node-xterm-mount-target'),
                        fuc.FefferyTimeout(id='host-node-init-timeout', delay=1),
                    ],
                    style=style(width='100%'),
                ),
            ],
            wrap=False,
        ),
    ]
