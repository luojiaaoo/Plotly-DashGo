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
from dash_callback.application.access_ import role_mgmt_c  # noqa
from functools import partial
from i18n import translator

_ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('团队管理')


icon = None
order = 4
access_metas = ('团队管理-页面',)
logger = Log.get_logger(__name__)


def render_content(menu_access: MenuAccess, **kwargs):
    from config.access_factory import AccessFactory

    logger.debug(f'用户：{menu_access.user_name}，访问：{__name__}，参数列表：{kwargs}，权限元：{menu_access.all_access_metas}')
    return fac.AntdCol(
        [
            fac.AntdRow(
                fac.AntdButton(
                    id='role-mgmt-button-add',
                    children=_('添加团队'),
                    type='primary',
                    icon=fac.AntdIcon(icon='antd-plus'),
                    style={'marginBottom': '10px'},
                )
            ),
            fac.AntdRow(
                [
                    Card(
                        Table(
                            id='role-mgmt-table',
                            columns=[
                                {'title': _('团队名称'), 'dataIndex': 'group_name'},
                                {'title': _('团队状态'), 'dataIndex': 'group_status', 'renderOptions': {'renderType': 'tags'}},
                                {'title': _('团队描述'), 'dataIndex': 'group_remark'},
                                {'title': _('更新时间'), 'dataIndex': 'update_datetime'},
                                {'title': _('更新人'), 'dataIndex': 'update_by'},
                                {'title': _('创建时间'), 'dataIndex': 'create_datetime'},
                                {'title': _('创建人'), 'dataIndex': 'create_by'},
                                {'title': _('操作'), 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}},
                            ],
                            data=[
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
                            ],
                            pageSize=10,
                        ),
                        style={'width': '100%'},
                    ),
                ],
            ),
        ],
    )
