from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html
from dash_components import Card
import dash_callback.application.message_.announcement_c  # noqa: F401
from i18n import t__notification, translator


# 二级菜单的标题、图标和显示顺序
title = '公告管理'
icon = None
logger = Log.get_logger(__name__)
order = 1
access_metas = ('公告管理-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return [
        fac.Fragment(
            [
                fuc.FefferyTimeout(id='announcement-init-timeout', delay=1),
            ]
        ),
        fac.AntdSpace(
            [
                fac.AntdSpace(
                    [
                        fac.AntdButton(
                            id='announcement-button-add',
                            children=t__notification('新增公告'),
                            type='primary',
                            icon=fac.AntdIcon(icon='antd-plus'),
                        ),
                        fac.AntdPopconfirm(
                            fac.AntdButton(
                                t__notification('删除选中'),
                                type='primary',
                                danger=True,
                                icon=fac.AntdIcon(icon='antd-close'),
                            ),
                            id='announcement-button-delete',
                            title=t__notification('确认删除选中行吗？'),
                            locale=translator.get_current_locale(),
                        ),
                    ]
                ),
                Card(
                    html.Div(
                        id='announcement-table-container',
                        style={'width': '100%'},
                    ),
                    style={'width': '100%'},
                ),
            ],
            direction='vertical',
            style={
                'marginBottom': '10px',
                'width': '100%',
            },
        ),
    ]
