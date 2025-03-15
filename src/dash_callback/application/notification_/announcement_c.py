from server import app
from dash.dependencies import Input, Output, State
import feffery_antd_components as fac
from dash_components import Table
from uuid import uuid4
import dash
from dash import set_props
from dash_components import MessageManager
import time
from feffery_dash_utils.style_utils import style


@app.callback(
    [
        Output('announcement-table-container', 'children'),
        Output('announcement-flush-table-trigger-store', 'data'),
    ],
    Input('announcement-init-timeout', 'timeoutCount'),
    prevent_initial_call=True,
)
def init_table(timeoutCount):
    """页面加载时初始化渲染表格"""
    return [
        fac.AntdModal(
            id='announcement-table-add-modal',
            title='新增公告',
            renderFooter=True,
            okClickClose=False,
        ),
        Table(
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
        ),
    ], uuid4().hex


@app.callback(
    Output('announcement-table', 'data'),
    Input('announcement-flush-table-trigger-store', 'data'),
    prevent_initial_call=True,
)
def flush_table_data(data):
    """触发数据更新，从数据库中获取所有公告数据到表中"""
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
        return dash.no_update

    # 删除选中行
    from database.sql_db.dao import dao_announcement

    dao_announcement.delete_announcement([row['content'] for row in selectedRows])
    MessageManager.success(content='选中行删除成功')

    # 重置选中行
    set_props('announcement-table', {'selectedRows': []})
    set_props('announcement-table', {'selectedRowKeys': []})

    return uuid4().hex


@app.callback(
    Output('announcement-table-add-modal', 'visible'),
    Input('announcement-button-add', 'nClicks'),
    prevent_initial_call=True,
)
def open_add_modal(nClicks):
    """显示新增数据模态框"""
    return True


@app.callback(
    Output('announcement-table-add-modal', 'children'),
    Input('announcement-table-add-modal', 'visible'),
    running=[Output('announcement-table-add-modal', 'loading'), True, False],
    prevent_initial_call=True,
)
def refresh_add_modal(visible):
    """刷新新增数据模态框内容"""

    if visible:
        time.sleep(0.5)

        return fac.AntdForm(
            [
                fac.AntdFormItem(
                    fac.AntdInput(id='announcement-content'),
                    label='发布内容',
                ),
            ],
        )
    return dash.no_update


@app.callback(
    Output('announcement-flush-table-trigger-store', 'data', allow_duplicate=True),
    Input('announcement-table-add-modal', 'okCounts'),
    State('announcement-content', 'value'),
    prevent_initial_call=True,
)
def handle_add_data(okCounts, value):
    """处理新增数据逻辑"""

    if value:
        from common.utilities.util_menu_access import get_menu_access

        op_user_name = get_menu_access(only_get_user_name=True)
        from database.sql_db.dao import dao_announcement

        MessageManager.success(content='数据新增成功')
        dao_announcement.add_announcement(user_name=op_user_name, announcement=value)
        return uuid4().hex

    MessageManager.success(content='数据填写不完整')
    return dash.no_update
