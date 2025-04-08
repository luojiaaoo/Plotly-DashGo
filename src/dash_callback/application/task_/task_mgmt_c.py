from server import app
from dash.dependencies import Input, Output, State
import feffery_antd_components as fac
from dash_components import Table
import dash
from dash import set_props
from dash_components import MessageManager
import time
from database.sql_db.dao import dao_apscheduler
from common.utilities.util_apscheduler import add_local_interval_job, get_apscheduler_all_jobs
from feffery_dash_utils.style_utils import style


def get_table_data():
    return [
        {
            'job_id': job.job_id,
            'type': job.type,
            'script_text': job.script_text,
            'extract_names': job.extract_names,
            'plan': job.plan,
            'job_next_run_time': job.job_next_run_time,
            'enable': {
                'checked': job.status,
                'checkedChildren': 'open',
                'unCheckedChildren': 'close',
                'custom': f'enable:{job.job_id}',
            },
            'view_history': {
                    'content': 'view History',
                    'type': 'primary',
                    'custom': f'view_history:{job.job_id}',
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
            id='task-mgmt-table-add-modal',
            title='新增任务',
            renderFooter=True,
            okClickClose=False,
        ),
        Table(
            id='task-mgmt-table',
            columns=[
                {'title': '任务名', 'dataIndex': 'job_id', 'width': 'calc(100% / 8)'},
                {'title': '类型', 'dataIndex': 'type', 'width': 'calc(100% / 8)'},
                {'title': '脚本', 'dataIndex': 'script_text', 'width': 'calc(100% / 8)'},
                {'title': '数据采集', 'dataIndex': 'extract_names', 'width': 'calc(100% / 8)'},
                {'title': '执行计划', 'dataIndex': 'plan', 'width': 'calc(100% / 8)'},
                {'title': '下一次执行时间', 'dataIndex': 'job_next_run_time', 'width': 'calc(100% / 8)'},
                {'title': '启用', 'dataIndex': 'enable', 'renderOptions': {'renderType': 'switch'}, 'width': 'calc(100% / 8)'},
                {'title': '执行记录', 'dataIndex': 'view_history', 'renderOptions': {'renderType': 'button'}, 'width': 'calc(100% / 8)'},
            ],
            rowSelectionType='checkbox',
            data=get_table_data(),
            pageSize=10,
        ),
    ]
