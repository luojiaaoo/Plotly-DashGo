from server import app
from dash.dependencies import Input, Output, State
import feffery_antd_components as fac
from dash_components import Table
import dash
from dash import set_props
from dash_components import MessageManager
import time
from database.sql_db.dao import dao_apscheduler
from common.utilities.util_apscheduler import add_local_interval_job, get_apscheduler_all_jobs, start_stop_job
from feffery_dash_utils.style_utils import style
from uuid import uuid4


def get_table_data():
    return [
        {
            'job_id': job.job_id,
            'type': job.type,
            'extract_names': '-' if job.extract_names is None else str(job.extract_names),
            'trigger': job.trigger,
            'plan': f'{job.plan}',
            'job_next_run_time': job.job_next_run_time,
            'enable': {
                'checked': job.status,
                'checkedChildren': 'open',
                'unCheckedChildren': 'close',
                'custom': job.job_id,
            },
            'view_log': {
                'content': 'View Log',
                'type': 'primary',
                'custom': f'view_log:{job.job_id}',
            },
        }
        for job in get_apscheduler_all_jobs()
    ]


@app.callback(
    Output('task-mgmt-table-container', 'children'),
    Input('task-mgmt-init-timeout', 'timeoutCount'),
    prevent_initial_call=True,
)
def init_table(timeoutCount):
    """页面加载时初始化渲染表格"""
    return [
        fac.AntdModal(
            id='task-mgmt-table-add-modal-interval',
            title='新增周期任务',
            renderFooter=True,
            okClickClose=False,
        ),
        fac.AntdModal(
            id='task-mgmt-table-add-modal-cron',
            title='新增定时任务',
            renderFooter=True,
            okClickClose=False,
        ),
        Table(
            id='task-mgmt-table',
            columns=[
                {'title': '任务名', 'dataIndex': 'job_id', 'width': 'calc(100% / 8)'},
                {'title': '类型', 'dataIndex': 'type', 'width': 'calc(100% / 8)'},
                {'title': '数据采集', 'dataIndex': 'extract_names', 'width': 'calc(100% / 8)'},
                {'title': '触发器', 'dataIndex': 'trigger', 'width': 'calc(100% / 8)'},
                {'title': '执行计划', 'dataIndex': 'plan', 'width': 'calc(100% / 8)'},
                {'title': '下一次执行时间', 'dataIndex': 'job_next_run_time', 'width': 'calc(100% / 8)'},
                {'title': '启用', 'dataIndex': 'enable', 'renderOptions': {'renderType': 'switch'}, 'width': 'calc(100% / 8)'},
                {'title': '执行记录', 'dataIndex': 'view_log', 'renderOptions': {'renderType': 'button'}, 'width': 'calc(100% / 8)'},
            ],
            rowSelectionType='radio',
            data=get_table_data(),
            pageSize=10,
        ),
    ]


@app.callback(
    Output('task-mgmt-table', 'data', allow_duplicate=True),
    [
        Input('task-mgmt-table', 'recentlySwitchDataIndex'),
        Input('task-mgmt-table', 'recentlySwitchStatus'),
        Input('task-mgmt-table', 'recentlySwitchRow'),
    ],
    prevent_initial_call=True,
)
def handle_enable_eow(recentlySwitchDataIndex, recentlySwitchStatus, recentlySwitchRow):
    """处理启用、关闭逻辑"""
    status = recentlySwitchRow['enable']['checked']
    job_id = recentlySwitchRow['enable']['custom']
    start_stop_job(job_id=job_id, is_start=status)
    if status:
        MessageManager.success(content=f'{job_id}任务启用成功')
    else:
        MessageManager.success(content=f'{job_id}任务停用成功')
    return get_table_data()


@app.callback(
    Output('task-mgmt-table-add-modal-interval', 'visible'),
    Input('task-mgmt-button-add-interval', 'nClicks'),
    prevent_initial_call=True,
)
def open_add_modal(nClicks):
    """显示新增数据模态框"""
    return True


@app.callback(
    Output('task-mgmt-table-add-modal-interval', 'children'),
    Input('task-mgmt-table-add-modal-interval', 'visible'),
    running=[Output('task-mgmt-table-add-modal-interval', 'loading'), True, False],
    prevent_initial_call=True,
)
def refresh_add_modal(visible):
    """刷新新增数据模态框内容"""

    if visible:
        time.sleep(0.5)

        return fac.AntdForm(
            [
                fac.AntdFormItem(
                    fac.AntdSegmented(
                        key=uuid4().hex,
                        id='task-mgmt-table-add-modal-interval-type-select',
                        options=[{'label': '本地脚本', 'value': 'local', 'icon': 'md-home'}, {'label': 'ssh远程执行', 'value': 'ssh', 'icon': 'antd-cloud'}],
                        defaultValue='local',
                        block=True,
                    ),
                    label='类型',
                ),
                fac.AntdSpace(
                    [
                        fac.AntdFormItem(
                            fac.AntdInput(
                                id='task-mgmt-table-add-modal-interval-ssh-username',
                            ),
                            label='ssh用户名',
                        ),
                        fac.AntdFormItem(
                            fac.AntdInput(
                                mode='password',
                                id='task-mgmt-table-add-modal-interval-ssh-password',
                            ),
                            label='ssh密码',
                        ),
                    ],
                    id='task-mgmt-table-add-modal-interval-ssh-container',
                    style=style(display='none'),
                ),
                fac.AntdFormItem(
                    fac.AntdInput(id='task-mgmt-table-add-modal-interval-script-text', mode='text-area', showCount=True),
                    label='脚本',
                ),
            ],
            labelCol={'span': 5},
            wrapperCol={'span': 20},
            style={'width': 400},
        )
    return dash.no_update


app.clientside_callback(
    """(value) => {
        if(value=='ssh'){
            return {'display':'block'}
        }else{
            return {'display':'None'}
        }
    }""",
    Output('task-mgmt-table-add-modal-interval-ssh-container', 'style'),
    Input('task-mgmt-table-add-modal-interval-type-select', 'value'),
)
