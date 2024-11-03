from server import app
from dash.dependencies import Input, Output, State
import dash
from database.sql_db.dao import dao_user
from dash_components import MessageManager
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
        Output('role-menu-access-tree-select', 'checkedKeys'),
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
    Output('role-mgmt-table', 'data'),
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
