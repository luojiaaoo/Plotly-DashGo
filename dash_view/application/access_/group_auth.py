from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash_components import Card, Table
from dash import html
from dash import dcc
from database.sql_db.dao import dao_user
from typing import Dict
from dash_callback.application.access_ import group_auth_c  # noqa
from functools import partial
from i18n import translator

_ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('团队授权')


icon = None
order = 4
access_metas = ('团队授权-页面',)
logger = Log.get_logger(__name__)


def render_content(menu_access: MenuAccess, **kwargs):
    return Card(
        Table(
            id='group-auth-table',
            columns=[
                {'title': _('团队名称'), 'dataIndex': 'group_name', 'width': '10%'},
                {'title': _('团队描述'), 'dataIndex': 'group_remark', 'width': '15%'},
                {'title': _('用户名'), 'dataIndex': 'user_name', 'width': '10%'},
                {'title': _('全名'), 'dataIndex': 'user_full_name', 'width': '10%'},
                {'title': _('角色'), 'dataIndex': 'user_roles', 'renderOptions': {'renderType': 'select'}, 'width': '55%'},
            ],
            data=[
                {
                    'key': f"{i['group_name']}:::{i['user_name']}",
                    'group_name': i['group_name'],
                    'group_remark': i['group_remark'],
                    'user_name': i['user_name'],
                    'user_full_name': i['user_full_name'],
                    'user_roles': {
                        'options': [{'label': group_role, 'value': group_role} for group_role in dao_user.filter_roles_enabled(i['group_roles'])],
                        'mode': 'multiple',
                        'value': i['user_roles'],
                    },
                }
                for i in dao_user.get_dict_group_name_users_roles(menu_access.user_name, exclude_disabled=True)
            ],
            pageSize=10,
        ),
        style={'width': '100%'},
    )
