from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html
from dash_components import Table
from dash import dcc
from database.sql_db.dao import dao_user
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
    access_metas: List[str] = menu_access.all_access_metas
    logger.debug(
        f'用户：{menu_access.user_name}，访问：{__name__}，参数列表：{kwargs}，权限元：{access_metas}'
    )
    return html.Div(
        [
            Table(
                columns=[{'title': f'字段{i}', 'dataIndex': f'字段{i}'} for i in range(1, 6)],
                data=[{f'字段{i}': '示例内容' for i in range(1, 6)}] * 3,
            ),
        ],
        style={'display': 'flex'},
    )
