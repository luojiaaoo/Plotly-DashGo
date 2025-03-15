from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html
from dash_components import Card
from dash import dcc
from database.sql_db.dao import dao_user
import dash_callback.application.notification_.announcement_c  # noqa: F401
from i18n import t__person, t__default, t__access


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
                dcc.Store(id='announcement-flush-table-trigger-store'),
                fuc.FefferyTimeout(id='announcement-init-timeout', delay=1),
            ]
        ),
        fac.AntdSpace(
            [
                fac.AntdSpace(
                    [
                        fac.AntdButton(
                            id='announcement-button-add',
                            children='新增公告',
                            type='primary',
                            icon=fac.AntdIcon(icon='antd-plus'),
                        ),
                        fac.AntdPopconfirm(
                            fac.AntdButton(
                                '删除选中',
                                type='primary',
                                danger=True,
                                icon=fac.AntdIcon(icon='antd-close'),
                            ),
                            id='announcement-button-delete',
                            title='确认删除选中行吗？',
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
