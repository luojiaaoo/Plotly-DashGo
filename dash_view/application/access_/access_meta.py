from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash_components import Card
from dash import html
from dash import dcc
from database.sql_db.dao import dao_user
from typing import Dict
import dash_callback.application.person_.personal_info_c  # noqa
from flask_babel import gettext as _  # noqa


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('权限列表')


icon = None
logger = Log.get_logger(__name__)
order = 1

access_metas = ('权限列表-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    dict_access_meta2menu_item: Dict = menu_access.dict_access_meta2menu_item
    logger.debug(f'用户：{menu_access.user_name}，访问：{__name__}，参数列表：{kwargs}，权限元：{access_metas}')
    return fac.AntdFlex(
        [
            Card(
                fac.AntdTable(
                    columns=[
                        {'title': _('一级菜单'), 'dataIndex': 'level1'},
                        {'title': _('二级菜单'), 'dataIndex': 'level2'},
                        {'title': _('权限元'), 'dataIndex': 'access_meta'},
                    ],
                    data=[
                        {
                            'level1': MenuAccess.get_title(menu_item.split('.')[0]),
                            'level2': MenuAccess.get_title(menu_item),
                            'access_meta': access_meta,
                        }
                        for access_meta, menu_item in dict_access_meta2menu_item.items()
                    ],
                    bordered=True,
                    filterOptions={
                        'level1': {'filterSearch': True},
                        'level2': {'filterSearch': True},
                        'access_meta': {'filterSearch': True},
                    },
                ),
                title=_('应用权限列表'),
            ),
        ],
        gap='small',
        wrap='wrap',
    )
