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
import dash_callback.application.person_.personal_info_c  # noqa
from functools import partial
from i18n import translator

_ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('角色管理')


icon = None
logger = Log.get_logger(__name__)
order = 1

access_metas = ('角色管理-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    dict_access_meta2menu_item: Dict = menu_access.dict_access_meta2menu_item
    logger.debug(f'用户：{menu_access.user_name}，访问：{__name__}，参数列表：{kwargs}，权限元：{access_metas}')
    return fac.AntdFlex(
        [
            Card(
                Table(
                    columns=[
                        {'title': _('角色名称'), 'dataIndex': 'role_name'},
                        {'title': _('角色状态'), 'dataIndex': 'role_status'},
                        {'title': _('角色描述'), 'dataIndex': 'role_remark'},
                        {'title': _('更新时间'), 'dataIndex': 'update_datetime'},
                        {'title': _('更新人'), 'dataIndex': 'update_by'},
                        {'title': _('创建时间'), 'dataIndex': 'create_datetime'},
                        {'title': _('创建人'), 'dataIndex': 'create_by'},
                        {'title': _('修改'), 'dataIndex': 'change', 'renderOptions': {'renderType': 'button'}},
                        {
                            'title': _('删除'),
                            'dataIndex': 'delete',
                            'renderOptions': {
                                'renderType': 'button',
                                'renderButtonPopConfirmProps': {
                                    'title': '确认删除？',
                                    'okText': '确认',
                                    'cancelText': '取消',
                                },
                            },
                        },
                    ],
                    data=[
                        {
                            **i.__dict__,
                            'change': {
                                'content': '修改',
                                'type': 'primary',
                                'custom': 'balabalabalabala',
                            },
                            'delete': {
                                'content': '删除',
                                'type': 'primary',
                                'custom': 'balabalabalabala',
                            },
                        }
                        for i in dao_user.get_role_info()
                    ],
                    pageSize=10,
                ),
                title=_('应用权限列表'),
                className={'flex': 'auto'},
            ),
        ],
        gap='small',
        wrap='wrap',
    )
