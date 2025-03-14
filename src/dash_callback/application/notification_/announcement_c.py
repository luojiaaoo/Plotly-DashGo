from server import app
from dash.dependencies import Input, Output, State
import feffery_antd_components as fac
from dash_components import Card, Table
from uuid import uuid4
from dash_components import MessageManager


@app.callback(
    [
        Output('announcement-table-container', 'children'),
        Output('announcement-flush-table-trigger-store', 'data'),
    ],
    Input('announcement-init-timeout', 'timeoutCount'),
    prevent_initial_call=True,
)
def init_table(_):
    """页面加载时初始化渲染表格"""
    return Table(
        id='announcement-table',
        columns=[
            {'title': '创建人', 'dataIndex': 'create_by', 'width': 'calc(100% / 5)'},
            {'title': '内容', 'dataIndex': 'content', 'width': 'calc(100% * 2 / 5)'},
            {'title': '发布时间', 'dataIndex': 'create_datetime', 'width': 'calc(100% / 5)'},
            {'title': '启用', 'dataIndex': 'enable', 'renderOptions': {'renderType': 'switch'}, 'width': 'calc(100% / 5)'},
        ],
        rowSelectionType='checkbox',
        data=[],
        pageSize=10,
    ), uuid4().hex


@app.callback(
    Output('announcement-table', 'data'),
    Input('announcement-flush-table-trigger-store', 'data'),
    prevent_initial_call=True,
)
def flush_table_data(_):
    from database.sql_db.dao import dao_announcement

    return [
        {
            'content': announcement.announcement,
            'create_datetime': announcement.datetime,
            'create_by': announcement.name,
            'enable': {
                'checked': announcement.status,
                'checkedChildren': '开',
                'unCheckedChildren': '关',
                'custom': f'enable: {announcement.datetime}',
            },
        }
        for announcement in dao_announcement.get_all_announcements()
    ]


@app.callback(
    Output('announcement-flush-table-trigger-store', 'data', allow_duplicate=True),
    Input('announcement-button-delete', 'confirmCounts'),
    State('announcement-table', 'selectedRows'),
    prevent_initial_call=True,
)
def handle_delete(confirmCounts, selectedRows):
    """处理表格数据行删除逻辑"""

    # 若当前无已选中行
    if not selectedRows:
        MessageManager.warning(content='请先选择要删除的行')

    # 删除选中行
    from database.sql_db.dao import dao_announcement

    dao_announcement.delete_announcement([row['content'] for row in selectedRows])
    MessageManager.success(content='选中行删除成功')

    # 重置选中行
    return uuid4().hex
