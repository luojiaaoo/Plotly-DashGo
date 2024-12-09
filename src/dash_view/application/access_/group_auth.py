from common.utilities.util_menu_access import MenuAccess
from common.utilities.util_logger import Log
from dash_components import Card, Table
from database.sql_db.dao import dao_user
from dash_callback.application.access_ import group_auth_c  # noqa
from i18n import t__access, t__default


# 二级菜单的标题、图标和显示顺序
title = '团队授权'
icon = None
order = 4
access_metas = ('团队授权-页面',)
logger = Log.get_logger(__name__)


def render_content(menu_access: MenuAccess, **kwargs):
    return Card(
        Table(
            id='group-auth-table',
            columns=[
                {'title': t__access('团队名称'), 'dataIndex': 'group_name', 'width': '10%'},
                {'title': t__access('团队描述'), 'dataIndex': 'group_remark', 'width': '10%'},
                {'title': t__access('用户名'), 'dataIndex': 'user_name', 'width': '10%'},
                {'title': t__access('用户全名'), 'dataIndex': 'user_full_name', 'width': '10%'},
                {'title': t__access('用户状态'), 'dataIndex': 'user_status', 'renderOptions': {'renderType': 'tags'}, 'width': '10%'},
                {'title': t__access('用户角色'), 'dataIndex': 'user_roles', 'renderOptions': {'renderType': 'select'}, 'width': '50%'},
            ],
            data=[
                {
                    'key': f"{i['group_name']}:::{i['user_name']}",
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
                for i in dao_user.get_dict_group_name_users_roles(menu_access.user_name)
            ],
            pageSize=10,
        ),
        style={'width': '100%'},
    )
