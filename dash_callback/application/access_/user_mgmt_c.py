from server import app
from dash.dependencies import Input, Output, State
import dash
from database.sql_db.dao import dao_user
from dash_components import MessageManager
from typing import List
from functools import partial
from i18n import translator

_ = partial(translator.t)


################### 新建角色
@app.callback(
    [
        Output('user-mgmt-add-user-name-form', 'validateStatus', allow_duplicate=True),
        Output('user-mgmt-add-user-name-form', 'help', allow_duplicate=True),
    ],
    Input('user-mgmt-add-user-name', 'debounceValue'),
    prevent_initial_call=True,
)
def check_role_name(user_name):
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
        Output('user-mgmt-add-user-name', 'visible'),
        Output('user-mgmt-add-user-full-name', 'value'),
        Output('user-mgmt-add-user-status', 'checked'),
        Output('user-mgmt-add-user-remark', 'value'),
        Output('user-mgmt-add-roles', 'options'),
        Output('user-mgmt-add-groups', 'options'),
        Output('user-mgmt-add-admin-groups', 'options'),
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
    return True, '', '', True, '', [i.role_name for i in dao_user.get_role_info()], [], [], '', '', None, None

