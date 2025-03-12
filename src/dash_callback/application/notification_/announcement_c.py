from server import app
from dash.dependencies import Input, Output
import feffery_antd_components as fac
from dash_components import Card, Table


@app.callback(
    Output('announcement-table-container', 'children'),
    Input('announcement-table-container', 'id'),
    # Input('announcement-button-add', 'id'),
)
def init_table(_):
    """页面加载时初始化渲染表格"""
    print(111111111111111)
    return Card(
        Table(
            id='announcement-table',
            columns=[
                {'title': '内容', 'dataIndex': 'content'},
                {'title': '状态', 'dataIndex': 'announcement_status', 'renderOptions': {'renderType': 'tags'}},
                {'title': '发布时间', 'dataIndex': 'create_datetime'},
                {'title': '创建人', 'dataIndex': 'create_by'},
            ],
            data=[],
            pageSize=10,
        ),
        style={'width': '100%'},
    )


# @app.callback(
#     Output('announcement-table', 'data'),
#     Input('announcement-flush-table-data', 'data'),
# )
# def flush_table_data(_):
#     return [
#         {
#             'content': '公告',
#             'announcement_status': '启用',
#             'create_datetime': '2023-07-01 12:00:00',
#             'create_by': 'admin',
#         }
#     ]
