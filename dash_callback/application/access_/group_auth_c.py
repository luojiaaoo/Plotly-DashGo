from server import app
from dash.dependencies import Input, Output
import dash
from common.utilities.util_menu_access import get_menu_access
from database.sql_db.dao import dao_user
from dash_components import MessageManager
from functools import partial
from i18n import translator

_ = partial(translator.t)


@app.callback(
    Output('group-auth-table', 'data'),
    [
        Input('group-auth-table', 'recentlySelectRow'),
        Input('group-auth-table', 'recentlySelectDataIndex'),
        Input('group-auth-table', 'recentlySelectValue'),
    ],
)
def change_role(recentlySelectRow, recentlySelectDataIndex, recentlySelectValue):
    group_name, user_name = recentlySelectRow['key'].split(':::')
    if recentlySelectDataIndex != 'user_roles':
        return dash.no_update
    rt = dao_user.update_user_roles_from_group(user_name, group_name, recentlySelectValue)
    if rt:
        MessageManager.success(content=_('权限更新成功'))
        return [
            {
                'key': f"{i['group_name']}:::{i['user_name']}",
                'group_name': i['group_name'],
                'group_remark': i['group_remark'],
                'user_name': i['user_name'],
                'user_status': i['user_status'],
                'user_full_name': i['user_full_name'],
                'user_roles': {
                    'options': [{'label': group_role, 'value': group_role} for group_role in i['group_roles']],
                    'mode': 'multiple',
                    'value': i['user_roles'],
                },
            }
            for i in dao_user.get_dict_group_name_users_roles(get_menu_access().user_name)
        ]
    else:
        MessageManager.warning(content=_('权限更新失败'))
        return dash.no_update
