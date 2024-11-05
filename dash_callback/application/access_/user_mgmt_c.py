from server import app
from dash.dependencies import Input, Output, State
import dash
from database.sql_db.dao import dao_user
from dash_components import MessageManager
from typing import List
from functools import partial
from i18n import translator

_ = partial(translator.t)


# ################### 新建角色
# @app.callback(
#     [
#         Output('role-mgmt-add-role-name-form', 'validateStatus', allow_duplicate=True),
#         Output('role-mgmt-add-role-name-form', 'help', allow_duplicate=True),
#     ],
#     Input('role-mgmt-add-role-name', 'debounceValue'),
#     prevent_initial_call=True,
# )
# def check_role_name(role_name):
#     """校验新建角色名的有效性"""
#     if not role_name:
#         return 'error', _('请填写角色名')
#     if not dao_user.exists_role_name(role_name):
#         return 'success', _('该角色名名可用')
#     else:
#         return 'error', _('该角色名已存在')


@app.callback(
    [
        Output('user-mgmt-add-modal', 'visible'),
        Output('user-mgmt-add-user-name', 'value'),
        Output('user-mgmt-add-user-full-name', 'value'),
        Output('user-mgmt-add-user-status', 'checked'),
        Output('user-mgmt-add-user-remark', 'value'),
        Output('user-mgmt-add-roles', 'value'),
        Output('user-mgmt-add-groups', 'value'),
        Output('user-mgmt-add-admin-groups', 'value'),
        Output('user-mgmt-add-user-email', 'value'),
        Output('user-mgmt-add-phone-number', 'value'),
        Output('user-mgmt-add-user-name-form', 'validateStatus', allow_duplicate=True),
        Output('user-mgmt-add-user-name-form', 'help', allow_duplicate=True),
    ],
    Input('user-mgmt-button-add', 'nClicks'),
    prevent_initial_call=True,
)
def open_add_role_modal(nClicks):
    """显示新建用户的弹窗"""
    return True, '', '', True, '', [], [], [], '', '', None, None
