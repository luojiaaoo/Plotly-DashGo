from server import app
from dash.dependencies import Input, Output, State
import dash
from database.sql_db.dao import dao_user
from dash_components import MessageManager
from typing import List
from functools import partial
from i18n import translator

_ = partial(translator.t)


@app.callback(
    [
        # 删除用户弹窗
        Output('user-mgmt-delete-affirm-modal', 'visible'),
        Output('user-mgmt-delete-user-name', 'children'),
        # 更新用户弹窗
        Output('user-mgmt-update-modal', 'visible'),
        Output('user-mgmt-update-user-name', 'children'),
        Output('user-mgmt-update-user-full-name', 'value'),
        Output('user-mgmt-update-user-email', 'value'),
        Output('user-mgmt-update-phone-number', 'value'),
        Output('user-mgmt-update-user-status', 'checked'),
        Output('user-mgmt-update-user-sex', 'value'),
        Output('user-mgmt-update-password', 'value'),
        Output('user-mgmt-update-user-remark', 'value'),
        Output('user-mgmt-update-roles', 'value'),
        Output('user-mgmt-update-roles', 'options'),
        Output('user-mgmt-update-groups', 'value'),
        Output('user-mgmt-update-groups', 'options'),
        Output('user-mgmt-update-admin-groups', 'value'),
        Output('user-mgmt-update-admin-groups', 'options'),
    ],
    Input('user-mgmt-table', 'nClicksButton'),
    State('user-mgmt-table', 'clickedCustom'),
    prevent_initial_call=True,
)
def update_delete_role(nClicksButton, clickedCustom: str):
    user_name = clickedCustom.split(':')[1]
    if clickedCustom.startswith('delete:'):
        return [
            True,
            user_name,
        ] + [dash.no_update] * 15
    elif clickedCustom.startswith('update:'):
        user_info = dao_user.get_user_info(user_name)[0]
        return [dash.no_update] * 2 + [
            True,
            user_info.user_name,
            user_info.user_full_name,
            user_info.user_email,
            user_info.phone_number,
            user_info.user_status,
            user_info.user_sex,
            '',
            user_info.user_remark,
            user_info.user_roles,
            [i.role_name for i in dao_user.get_role_info()],
            user_info.user_groups,
            [],
            user_info.user_admin_groups,
            [],
        ]


################### 更新用户
@app.callback(
    Output('user-mgmt-table', 'data', allow_duplicate=True),
    Input('user-mgmt-update-modal', 'okCounts'),
    [
        State('user-mgmt-update-user-name', 'children'),
        State('user-mgmt-update-user-full-name', 'value'),
        State('user-mgmt-update-user-email', 'value'),
        State('user-mgmt-update-phone-number', 'value'),
        State('user-mgmt-update-user-status', 'checked'),
        State('user-mgmt-update-user-sex', 'value'),
        State('user-mgmt-update-password', 'value'),
        State('user-mgmt-update-user-remark', 'value'),
        State('user-mgmt-update-roles', 'value'),
        State('user-mgmt-update-groups', 'value'),
        State('user-mgmt-update-admin-groups', 'value'),
    ],
    prevent_initial_call=True,
)
def update_user(okCounts, user_name, user_full_name, user_email, phone_number, user_status, user_sex, password, user_remark, user_roles, user_groups, user_admin_groups):
    if not user_name or not user_full_name:
        MessageManager.warning(content=_('用户名/全名不能为空'))
        return dash.no_update
    rt = dao_user.update_user(user_name, user_full_name, password, user_status, user_sex, user_roles, user_groups, user_admin_groups, user_email, phone_number, user_remark)
    if rt:
        MessageManager.success(content=_('用户更新成功'))
        return [
            {
                'key': i.user_name,
                **i.__dict__,
                'user_status': {'tag': dao_user.get_status_str(i.user_status), 'color': 'cyan' if i.user_status else 'volcano'},
                'operation': [
                    {
                        'content': _('编辑'),
                        'type': 'primary',
                        'custom': 'update:' + i.user_name,
                    },
                    {
                        'content': _('删除'),
                        'type': 'primary',
                        'custom': 'delete:' + i.user_name,
                        'danger': True,
                    },
                ],
            }
            for i in dao_user.get_user_info()
        ]
    else:
        MessageManager.warning(content=_('用户更新失败'))
        return dash.no_update


################### 新建用户
@app.callback(
    [
        Output('user-mgmt-add-user-name-form', 'validateStatus', allow_duplicate=True),
        Output('user-mgmt-add-user-name-form', 'help', allow_duplicate=True),
    ],
    Input('user-mgmt-add-user-name', 'debounceValue'),
    prevent_initial_call=True,
)
def check_user_name(user_name):
    """校验新建用户名的有效性"""
    if not user_name:
        return 'error', _('请填写名用户名')
    if not dao_user.exists_user_name(user_name):
        return 'success', _('该用户名名可用')
    else:
        return 'error', _('该用户名已存在')


@app.callback(
    [
        Output('user-mgmt-add-modal', 'visible'),
        Output('user-mgmt-add-user-name', 'value'),
        Output('user-mgmt-add-user-full-name', 'value'),
        Output('user-mgmt-add-user-status', 'checked'),
        Output('user-mgmt-add-user-remark', 'value'),
        Output('user-mgmt-add-roles', 'options'),
        Output('user-mgmt-add-roles', 'value'),
        Output('user-mgmt-add-groups', 'options'),
        Output('user-mgmt-add-groups', 'value'),
        Output('user-mgmt-add-admin-groups', 'options'),
        Output('user-mgmt-add-admin-groups', 'value'),
        Output('user-mgmt-add-user-email', 'value'),
        Output('user-mgmt-add-phone-number', 'value'),
        Output('user-mgmt-add-password', 'value'),
        Output('user-mgmt-add-user-name-form', 'validateStatus', allow_duplicate=True),
        Output('user-mgmt-add-user-name-form', 'help', allow_duplicate=True),
    ],
    Input('user-mgmt-button-add', 'nClicks'),
    prevent_initial_call=True,
)
def open_add_role_modal(nClicks):
    """显示新建用户的弹窗"""
    from uuid import uuid4

    return True, '', '', True, '', [i.role_name for i in dao_user.get_role_info()], [], [], [], [], [], '', '', str(uuid4())[:12].replace('-', ''), None, None


@app.callback(
    Output('user-mgmt-table', 'data', allow_duplicate=True),
    Input('user-mgmt-add-modal', 'okCounts'),
    [
        State('user-mgmt-add-user-name', 'debounceValue'),
        State('user-mgmt-add-user-full-name', 'value'),
        State('user-mgmt-add-user-email', 'value'),
        State('user-mgmt-add-phone-number', 'value'),
        State('user-mgmt-add-user-status', 'checked'),
        State('user-mgmt-add-user-sex', 'value'),
        State('user-mgmt-add-password', 'value'),
        State('user-mgmt-add-user-remark', 'value'),
        State('user-mgmt-add-roles', 'value'),
        State('user-mgmt-add-groups', 'value'),
        State('user-mgmt-add-admin-groups', 'value'),
    ],
    prevent_initial_call=True,
)
def add_user(okCounts, user_name, user_full_name, user_email, phone_number, user_status: bool, user_sex, password, user_remark, user_roles, user_groups, user_admin_groups):
    """新建用户"""
    if not user_name or not user_full_name:
        MessageManager.warning(content=_('用户名/全名不能为空'))
        return dash.no_update
    rt = dao_user.add_user(user_name, user_full_name, password, user_status, user_sex, user_roles, user_groups, user_admin_groups, user_email, phone_number, user_remark)
    if rt:
        MessageManager.success(content=_('用户添加成功'))
        return [
            {
                'key': i.user_name,
                **i.__dict__,
                'user_status': {'tag': dao_user.get_status_str(i.user_status), 'color': 'cyan' if i.user_status else 'volcano'},
                'operation': [
                    {
                        'content': _('编辑'),
                        'type': 'primary',
                        'custom': 'update:' + i.user_name,
                    },
                    {
                        'content': _('删除'),
                        'type': 'primary',
                        'custom': 'delete:' + i.user_name,
                        'danger': True,
                    },
                ],
            }
            for i in dao_user.get_user_info()
        ]
    else:
        MessageManager.warning(content=_('用户添加失败'))
        return dash.no_update


################### 删除用户
@app.callback(
    Output('user-mgmt-table', 'data', allow_duplicate=True),
    Input('user-mgmt-delete-affirm-modal', 'okCounts'),
    State('user-mgmt-delete-user-name', 'children'),
    prevent_initial_call=True,
)
def delete_role_modal(okCounts, user_name):
    """删除角色"""
    rt = dao_user.delete_user(user_name)
    if rt:
        MessageManager.success(content=_('用户删除成功'))
        return [
            {
                'key': i.user_name,
                **i.__dict__,
                'user_status': {'tag': dao_user.get_status_str(i.user_status), 'color': 'cyan' if i.user_status else 'volcano'},
                'operation': [
                    {
                        'content': _('编辑'),
                        'type': 'primary',
                        'custom': 'update:' + i.user_name,
                    },
                    {
                        'content': _('删除'),
                        'type': 'primary',
                        'custom': 'delete:' + i.user_name,
                        'danger': True,
                    },
                ],
            }
            for i in dao_user.get_user_info()
        ]
    else:
        MessageManager.warning(content=_('用户删除失败'))
        return dash.no_update