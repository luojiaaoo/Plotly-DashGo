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
        # 删除角色弹窗
        Output('role-mgmt-delete-affirm-modal', 'visible'),
        Output('role-mgmt-delete-role-name', 'children'),
        Output('role-mgmt-update-role-name', 'children'),
        Output('role-mgmt-update-role-status', 'checked'),
        Output('role-menu-access-tree-select-update', 'checkedKeys'),
    ],
    Input('role-mgmt-table', 'nClicksButton'),
    State('role-mgmt-table', 'clickedCustom'),
    prevent_initial_call=True,
)
def update_delete_role(nClicksButton, clickedCustom: str):
    if clickedCustom.startswith('delete'):
        role_name = clickedCustom.split(':')[1]
        return True, role_name, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output('role-mgmt-table', 'data', allow_duplicate=True),
    Input('role-mgmt-delete-affirm-modal', 'okCounts'),
    State('role-mgmt-delete-role-name', 'children'),
    prevent_initial_call=True,
)
def delete_role_modal(okCounts, role_name):
    rt = dao_user.delete_role(role_name)
    if rt:
        MessageManager.success(content=_('用户删除成功'))
        return [
            {
                **i.__dict__,
                'operation': [
                    {
                        'content': _('编辑'),
                        'type': 'primary',
                        'custom': 'update:' + i.role_name,
                    },
                    {
                        'content': _('删除'),
                        'type': 'primary',
                        'custom': 'delete:' + i.role_name,
                        'danger': True,
                    },
                ],
            }
            for i in dao_user.get_role_info()
        ]
    else:
        MessageManager.warning(content=_('用户删除失败'))
        return dash.no_update


@app.callback(
    [
        Output('role-mgmt-add-role-name-form', 'validateStatus', allow_duplicate=True),
        Output('role-mgmt-add-role-name-form', 'help', allow_duplicate=True),
    ],
    Input('role-mgmt-add-role-name', 'debounceValue'),
    prevent_initial_call=True,
)
def check_role_name(role_name):
    if not role_name:
        return 'error', _('请填写角色名')
    if not dao_user.exists_role_name(role_name):
        return 'success', _('该角色名名可用')
    else:
        return 'error', _('该角色名已存在')


@app.callback(
    [
        Output('role-mgmt-add-modal', 'visible'),
        Output('role-mgmt-add-role-name', 'value'),
        Output('role-mgmt-add-role-status', 'checked'),
        Output('role-mgmt-add-role-remark', 'value'),
        Output('role-menu-access-tree-select-add', 'checkedKeys'),
        Output('role-mgmt-add-role-name-form', 'validateStatus', allow_duplicate=True),
        Output('role-mgmt-add-role-name-form', 'help', allow_duplicate=True),
    ],
    Input('role-mgmt-button-add', 'nClicks'),
    prevent_initial_call=True,
)
def open_add_role_modal(nClicks):
    return True, '', True, '', [], None, None


@app.callback(
    Output('role-mgmt-table', 'data', allow_duplicate=True),
    Input('role-mgmt-add-modal', 'okCounts'),
    [
        State('role-mgmt-add-role-name', 'debounceValue'),
        State('role-mgmt-add-role-status', 'checked'),
        State('role-mgmt-add-role-remark', 'value'),
        State('role-menu-access-tree-select-add', 'checkedKeys'),
    ],
    prevent_initial_call=True,
)
def add_role_c(okCounts, name, role_status, role_remark, access_metas: List[str]):
    access_metas = [i for i in access_metas if not i.startswith('ignore:')]
    rt = dao_user.add_role(name, role_status, role_remark, access_metas)
    if rt:
        MessageManager.success(content=_('用户添加成功'))
        return [
            {
                **i.__dict__,
                'operation': [
                    {
                        'content': _('编辑'),
                        'type': 'primary',
                        'custom': 'update:' + i.role_name,
                    },
                    {
                        'content': _('删除'),
                        'type': 'primary',
                        'custom': 'delete:' + i.role_name,
                        'danger': True,
                    },
                ],
            }
            for i in dao_user.get_role_info()
        ]
    else:
        MessageManager.warning(content=_('用户添加失败'))
        return dash.no_update
