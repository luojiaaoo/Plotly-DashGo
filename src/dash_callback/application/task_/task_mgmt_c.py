from server import app
from dash.dependencies import Input, Output, State
import feffery_antd_components as fac
from dash_components import Table
import dash
from dash import set_props
from dash_components import MessageManager
import time
from database.sql_db.dao import dao_apscheduler
from common.utilities.util_apscheduler import add_local_interval_job, get_apscheduler_all_job
from feffery_dash_utils.style_utils import style


def get_table_data():
    return get_apscheduler_all_job()
    # from database.sql_db.dao import dao_apscheduler

    # return [
    #     {
    #         'content': announcement.announcement,
    #         'create_datetime': announcement.datetime,
    #         'create_by': announcement.name,
    #         'enable': {
    #             'checked': announcement.status,
    #             'checkedChildren': 'open',
    #             'unCheckedChildren': 'close',
    #             'custom': announcement.announcement,
    #         },
    #     }
    #     for announcement in dao_announcement.get_all_announcements()
    # ]


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
                {'title': '任务名', 'dataIndex': 'create_by', 'width': 'calc(100% / 8)'},
                {'title': '任务类型', 'dataIndex': 'content', 'width': 'calc(100% / 8)'},
                {'title': '脚本', 'dataIndex': 'content', 'width': 'calc(100% / 8)'},
                {'title': '数据采集', 'dataIndex': 'content', 'width': 'calc(100% / 8)'},
                {'title': '执行计划', 'dataIndex': 'create_datetime', 'width': 'calc(100% / 8)'},
                {'title': '下一次执行时间', 'dataIndex': 'create_datetime', 'width': 'calc(100% / 8)'},
                {'title': '启用', 'dataIndex': 'enable', 'renderOptions': {'renderType': 'switch'}, 'width': 'calc(100% / 8)'},
                {'title': '执行记录', 'dataIndex': 'enable', 'renderOptions': {'renderType': 'button'}, 'width': 'calc(100% / 8)'},
            ],
            rowSelectionType='checkbox',
            # data=get_table_data(),
            pageSize=10,
        ),
    ]

