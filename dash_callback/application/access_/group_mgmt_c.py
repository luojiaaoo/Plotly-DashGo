from server import app
from dash.dependencies import Input, Output, State
import dash
from database.sql_db.dao import dao_user
from dash_components import MessageManager
from typing import List
from functools import partial
from i18n import translator

_ = partial(translator.t)


########################################## 新增团队
@app.callback(
    [
        Output('group-mgmt-add-group-name-form', 'validateStatus', allow_duplicate=True),
        Output('group-mgmt-add-group-name-form', 'help', allow_duplicate=True),
    ],
    Input('group-mgmt-add-group-name', 'debounceValue'),
    prevent_initial_call=True,
)
def check_role_name(group_name):
    """校验新建团队名的有效性"""
    if not group_name:
        return 'error', _('请填写团队名')
    if not dao_user.exists_group_name(group_name):
        return 'success', _('该团队名可用')
    else:
        return 'error', _('该团队名已存在')


@app.callback(
    [
        Output('group-mgmt-add-modal', 'visible'),
        Output('group-mgmt-add-group-name', 'value'),
        Output('group-mgmt-add-group-status', 'checked'),
        Output('group-mgmt-add-group-remark', 'value'),
        Output('group-mgmt-add-group-roles', 'options'),
        Output('group-mgmt-add-group-roles', 'value'),
        Output('group-mgmt-add-group-admin-users', 'options'),
        Output('group-mgmt-add-group-admin-users', 'value'),
        Output('group-mgmt-add-group-users', 'options'),
        Output('group-mgmt-add-group-users', 'value'),
    ],
    Input('group-mgmt-button-add', 'nClicks'),
    prevent_initial_call=True,
)
def show_add_group_modal(nClicks):
    user_names = [i.user_name for i in dao_user.get_user_info(exclude_role_admin=True)]
    return (
        True,
        '',
        True,
        '',
        [i.role_name for i in dao_user.get_role_info(exclude_role_admin=True)],
        [],
        user_names,
        [],
        user_names,
        [],
    )


@app.callback(
    Output('role-mgmt-table', 'data'),
    Input('group-mgmt-add-modal', 'okCounts'),
    [
        State('group-mgmt-add-group-name', 'value'),
        State('group-mgmt-add-group-status', 'checked'),
        State('group-mgmt-add-group-remark', 'value'),
        State('group-mgmt-add-group-roles', 'value'),
        State('group-mgmt-add-group-admin-users', 'value'),
        State('group-mgmt-add-group-users', 'value'),
    ],
)
def add_group(okCounts, group_name, group_status, group_remark, group_roles, group_admin_users, group_users):
    """新建团队"""
    if not group_name:
        MessageManager.warning(content=_('角色名不能为空'))
        return dash.no_update
    rt = dao_user.add_group(group_name, group_status, group_remark, group_roles, group_admin_users, group_users)
    if rt:
        MessageManager.success(content=_('团队添加成功'))
        return [
            {
                'key': i.group_name,
                **i.__dict__,
                'group_status': {'tag': dao_user.get_status_str(i.group_status), 'color': 'cyan' if i.group_status else 'volcano'},
                'operation': [
                    {
                        'content': _('编辑'),
                        'type': 'primary',
                        'custom': 'update:' + i.group_name,
                    },
                    {
                        'content': _('删除'),
                        'type': 'primary',
                        'custom': 'delete:' + i.group_name,
                        'danger': True,
                    },
                ],
            }
            for i in dao_user.get_group_info()
        ]
    else:
        MessageManager.warning(content=_('团队添加失败'))
        return dash.no_update
