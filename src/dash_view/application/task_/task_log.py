from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html
from dash_components import Card
from i18n import translator
from i18n import t__task
import dash_callback.application.task_.task_log_c  # noqa: F401
from common.utilities.util_apscheduler import get_apscheduler_all_jobs


# 二级菜单的标题、图标和显示顺序
title = '任务日志'
icon = None
logger = Log.get_logger(__name__)
order = 2
access_metas = ('任务日志-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return fuc.FefferyInViewport(
        Card(
            fac.AntdSpace(
                [
                    fac.AntdSpace(
                        [
                            fac.AntdSelect(
                                id='task-log-job-id-select',
                                options=sorted([{'label': job.job_id, 'value': job.job_id} for job in get_apscheduler_all_jobs()], key=lambda job: job['label'], reverse=True),
                                style={'width': 800},
                                listHeight=200,
                                autoClearSearchValue=True,
                                prefix=fac.AntdIcon(icon='bi-table'),
                            ),
                            fac.AntdButton(t__task('查询执行记录'), id='task-log-get-start-datetime-btn'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdSelect(
                                id='task-log-start-datetime-select',
                                prefix=fac.AntdIcon(icon='md-query-builder'),
                                listHeight=500,
                                autoClearSearchValue=True,
                                style={'width': 800},
                            ),
                            fac.AntdButton(t__task('查询执行日志'), id='task-log-get-log-btn'),
                            fac.AntdSwitch(
                                checked=True,
                                id='task-log-scroll-log',
                                checkedChildren=t__task('自动滚动'),
                                unCheckedChildren=t__task('关闭滚动'),
                            ),
                        ]
                    ),
                    fac.Fragment(id='task-log-sse-container'),
                    fuc.FefferyScroll(
                        id='task-log-scroll-bottom',
                        scrollMode='to-bottom',
                        containerId='task-log-command-output-records',
                    ),
                    html.Div(
                        '---',
                        id='task-log-command-output-records',
                        style={
                            'width': '95%',
                            'background': 'black',
                            'color': 'white',
                            'padding': '6px 8px',
                            'whiteSpace': 'pre',
                            'height': '95%',
                            'overflow': 'auto',
                        },
                    ),
                ],
                size='middle',
                style={'width': '100%', 'height': '85%'},
                className={'& :nth-child(5)': {'height': '100%'}},
                direction='vertical',
            ),
            style={'width': '100%', 'height': '100%'},
            className={'& .ant-card-body': {'height': '100%'}},
        ),
        id='task-log-viewport',
    )
