from server import app
from dash.dependencies import Input, Output
import dash
from common import get_menu_access
from database.sql_db.dao import dao_user
from dash_components import MessageManager
from i18n import t__access, t__default


@app.callback(
    Output('group-auth-table', 'data'),
    [
        Input('group-auth-table', 'recentlySelectRow'),
        Input('group-auth-table', 'recentlySelectDataIndex'),
        Input('group-auth-table', 'recentlySelectValue'),
    ],
)
def change_role(recentlySelectRow, recentlySelectDataIndex, recentlySelectValue):
    from uuid import uuid4

    group_name = recentlySelectRow['group_name']
    user_name = recentlySelectRow['user_name']
    if recentlySelectDataIndex != 'user_roles':
        return dash.no_update
    rt = dao_user.update_user_roles_from_group(user_name, group_name, recentlySelectValue)
    if rt:
        MessageManager.success(content=t__access('权限更新成功'))
        return [
            {
                'key': f"{i['group_name']}:::{i['user_name']}+{uuid4()}",  # 强制刷新多选数据
                'group_name': i['group_name'],
                'group_remark': i['group_remark'],
                'user_name': i['user_name'],
                'user_full_name': i['user_full_name'],
                'user_status': {'tag': t__default('启用' if i['user_status'] else '停用'), 'color': 'cyan' if i['user_status'] else 'volcano'},
                'user_roles': {
                    'options': [{'label': group_role, 'value': group_role} for group_role in i['group_roles']],
                    'mode': 'multiple',
                    'value': i['user_roles'],
                },
            }
            for i in dao_user.get_dict_group_name_users_roles(get_menu_access().user_name)
        ]
    else:
        MessageManager.warning(content=t__access('权限更新失败'))
        return dash.no_update
