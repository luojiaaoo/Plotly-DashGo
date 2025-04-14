from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html,dcc
from dash_components import Card
from i18n import translator
import dash_callback.application.task_.task_mgmt_c  # noqa


# 二级菜单的标题、图标和显示顺序
title = '任务管理'
icon = None
logger = Log.get_logger(__name__)
order = 1
access_metas = ('任务管理-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return [
        fac.Fragment(
            [
                fuc.FefferyTimeout(id='task-mgmt-init-timeout', delay=100),
            ]
        ),
        fac.AntdSpace(
            [
                fac.AntdSpace(
                    [
                        fac.AntdButton(
                            id='task-mgmt-button-add-interval',
                            children='新增周期任务',
                            type='primary',
                            icon=fac.AntdIcon(icon='md-update'),
                        ),
                        fac.AntdButton(
                            id='task-mgmt-button-add-cron',
                            children='新增定时任务',
                            type='primary',
                            icon=fac.AntdIcon(icon='md-schedule'),
                        ),
                        fac.AntdPopconfirm(
                            fac.AntdButton(
                                '删除选中',
                                type='primary',
                                danger=True,
                                icon=fac.AntdIcon(icon='antd-close'),
                            ),
                            id='task-mgmt-button-delete',
                            title='确认删除选中行吗？',
                            locale=translator.get_current_locale(),
                        ),
                        fac.AntdButton(
                            '刷新',
                            id='task-mgmt-button-flash',
                            color='primary',
                            variant='link',
                            icon=fac.AntdIcon(icon='antd-reload'),
                        ),
                        fuc.FefferyTimeout(id='task-mgmt-view-jump-timeout'),
                    ]
                ),
                Card(
                    html.Div(
                        id='task-mgmt-table-container',
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
