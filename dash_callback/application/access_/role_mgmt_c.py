from server import app
from dash.dependencies import Input, Output, State
import dash
from database.sql_db.dao import dao_user
from dash_components import MessageManager
from typing import List
from i18n import t__access_mgmt, t__default


@app.callback(
    [
        # 删除角色弹窗
        Output('role-mgmt-delete-affirm-modal', 'visible'),
        Output('role-mgmt-delete-role-name', 'children'),
        # 更新角色弹窗
        Output('role-mgmt-update-modal', 'visible'),
        Output('role-mgmt-update-role-name', 'children'),
        Output('role-mgmt-update-role-status', 'checked'),
        Output('role-mgmt-update-role-status', 'readOnly'),
        Output('role-mgmt-update-role-remark', 'value'),
        Output('role-menu-access-tree-select-update', 'checkedKeys'),
    ],
    Input('role-mgmt-table', 'nClicksButton'),
    State('role-mgmt-table', 'clickedCustom'),
    prevent_initial_call=True,
)
def update_delete_role(nClicksButton, clickedCustom: str):
    """触发更新和删除角色弹窗显示"""
    role_name = clickedCustom.split(':')[1]
    if clickedCustom.startswith('delete:'):
        return [
            True,
            role_name,
        ] + [
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        ]
    elif clickedCustom.startswith('update:'):
        role_info = dao_user.get_role_info([role_name], exclude_disabled=False)[0]
        return [
            dash.no_update,
            dash.no_update,
        ] + [
            True,
            role_info.role_name,
            bool(role_info.role_status),
            False if role_name != 'admin' else True,
            role_info.role_remark,
            role_info.access_metas,
        ]


################### 更新角色
@app.callback(
    Output('role-mgmt-table', 'data', allow_duplicate=True),
    Input('role-mgmt-update-modal', 'okCounts'),
    [
        State('role-mgmt-update-role-name', 'children'),
        State('role-mgmt-update-role-status', 'checked'),
        State('role-mgmt-update-role-remark', 'value'),
        State('role-menu-access-tree-select-update', 'checkedKeys'),
    ],
    prevent_initial_call=True,
)
def callback_func(okCounts, role_name: str, role_status: bool, role_remark: str, access_metas: List[str]):
    access_metas = [i for i in access_metas if not i.startswith('ignore:')]
    rt = dao_user.update_role(role_name, role_status, role_remark, access_metas)
    if rt:
        MessageManager.success(content=t__access_mgmt('角色更新成功'))
        return [
            {
                'key': i.role_name,
                **i.__dict__,
                'role_status': {'tag': '启用' if i.role_status else '停用', 'color': 'cyan' if i.role_status else 'volcano'},
                'operation': [
                    {
                        'content': t__default('编辑'),
                        'type': 'primary',
                        'custom': 'update:' + i.role_name,
                    },
                    *(
                        [
                            {
                                'content': t__default('删除'),
                                'type': 'primary',
                                'custom': 'delete:' + i.role_name,
                                'danger': True,
                            }
                        ]
                        if i.role_name != 'admin'
                        else []
                    ),
                ],
            }
            for i in dao_user.get_role_info(exclude_disabled=False)
        ]
    else:
        MessageManager.warning(content=t__access_mgmt('角色更新失败'))
        return dash.no_update


################### 删除角色
@app.callback(
    Output('role-mgmt-table', 'data', allow_duplicate=True),
    Input('role-mgmt-delete-affirm-modal', 'okCounts'),
    State('role-mgmt-delete-role-name', 'children'),
    prevent_initial_call=True,
)
def delete_role_modal(okCounts, role_name):
    """删除角色"""
    rt = dao_user.delete_role(role_name)
    if rt:
        MessageManager.success(content=t__access_mgmt('角色删除成功'))
        return [
            {
                'key': i.role_name,
                **i.__dict__,
                'role_status': {'tag': '启用' if i.role_status else '停用', 'color': 'cyan' if i.role_status else 'volcano'},
                'operation': [
                    {
                        'content': t__default('编辑'),
                        'type': 'primary',
                        'custom': 'update:' + i.role_name,
                    },
                    *(
                        [
                            {
                                'content': t__default('删除'),
                                'type': 'primary',
                                'custom': 'delete:' + i.role_name,
                                'danger': True,
                            }
                        ]
                        if i.role_name != 'admin'
                        else []
                    ),
                ],
            }
            for i in dao_user.get_role_info(exclude_disabled=False)
        ]
    else:
        MessageManager.warning(content=t__access_mgmt('角色删除失败'))
        return dash.no_update


################### 新建角色
@app.callback(
    [
        Output('role-mgmt-add-role-name-form', 'validateStatus', allow_duplicate=True),
        Output('role-mgmt-add-role-name-form', 'help', allow_duplicate=True),
    ],
    Input('role-mgmt-add-role-name', 'debounceValue'),
    prevent_initial_call=True,
)
def check_role_name(role_name):
    """校验新建角色名的有效性"""
    if not role_name:
        return 'error', t__access_mgmt('请填写角色名')
    if not dao_user.exists_role_name(role_name):
        return 'success', t__access_mgmt('该角色名可用')
    else:
        return 'error', t__access_mgmt('该角色名已存在')


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
    """显示新建角色的弹窗"""
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
    """新建角色"""
    if not name:
        MessageManager.warning(content=t__access_mgmt('角色名不能为空'))
        return dash.no_update
    access_metas = [i for i in access_metas if not i.startswith('ignore:')]
    rt = dao_user.create_role(name, role_status, role_remark, access_metas)
    if rt:
        MessageManager.success(content=t__access_mgmt('角色添加成功'))
        return [
            {
                'key': i.role_name,
                **i.__dict__,
                'role_status': {'tag': '启用' if i.role_status else '停用', 'color': 'cyan' if i.role_status else 'volcano'},
                'operation': [
                    {
                        'content': t__default('编辑'),
                        'type': 'primary',
                        'custom': 'update:' + i.role_name,
                    },
                    *(
                        [
                            {
                                'content': t__default('删除'),
                                'type': 'primary',
                                'custom': 'delete:' + i.role_name,
                                'danger': True,
                            }
                        ]
                        if i.role_name != 'admin'
                        else []
                    ),
                ],
            }
            for i in dao_user.get_role_info(exclude_disabled=False)
        ]
    else:
        MessageManager.warning(content=t__access_mgmt('角色添加失败'))
        return dash.no_update
