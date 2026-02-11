from common.utilities.util_menu_access import MenuAccess
import random
import feffery_antd_charts as fact
import feffery_antd_components as fac
import feffery_utils_components as fuc
from feffery_dash_utils.style_utils import style
from dash_components import Card
import feffery_antd_components as fac
from loguru import logger
from i18n import t__dashboard


# 二级菜单的标题、图标和显示顺序
title = '工作台'
icon = None
order = 1

access_metas = ('工作台-页面',)


def chart_block(title, chart):
    """示例自定义组件，返回仪表盘区块"""

    return fac.AntdFlex(
        [
            fac.AntdText(
                title,
                style=style(borderLeft='3px solid #1890ff', paddingLeft=8, fontSize=15),
            ),
            chart,
        ],
        vertical=True,
        gap=8,
        style=style(height='calc(100% - 20px)'),
    )


def render_content(menu_access: MenuAccess, **kwargs):
    return fac.AntdSpace(
        [
            Card(
                fac.AntdSpace(
                    [
                        fac.AntdAvatar(
                            id='workbench-avatar',
                            mode='image',
                            src=f'/avatar/{menu_access.user_info.user_name}',
                            alt=menu_access.user_info.user_full_name,
                            size=70,
                            style={'marginRight': '20px'},
                        ),
                        fac.AntdText(t__dashboard('你好，')),
                        fac.AntdText(menu_access.user_info.user_full_name, id='workbench-user-full-name'),
                    ]
                )
            ),
        ],
        direction='vertical',
        style={'width': '100%'},
    )
