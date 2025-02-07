from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash_components import Card


# 二级菜单的标题、图标和显示顺序
title = '应用1'
icon = None
order = 2
logger = Log.get_logger(__name__)

access_metas = (
    '应用1-基础权限',
    '应用1-权限1',
    '应用1-权限2',
)


def render_content(menu_access: MenuAccess, **kwargs):
    return fac.AntdFlex(
        [
            *(
                [
                    Card(
                        fac.AntdStatistic(
                            title='展示',
                            value=fuc.FefferyCountUp(end=100, duration=3),
                        ),
                        title='应用1-权限1',
                    )
                ]
                if menu_access.has_access('应用1-权限1')
                else []
            ),
            *(
                [
                    Card(
                        fac.AntdStatistic(
                            title='展示',
                            value=fuc.FefferyCountUp(end=200, duration=3),
                        ),
                        title='应用1-权限2',
                    )
                ]
                if menu_access.has_access('应用1-权限2')
                else []
            ),
        ],
        wrap='wrap',
    )
