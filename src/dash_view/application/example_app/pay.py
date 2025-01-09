from common.utilities.util_menu_access import MenuAccess
import feffery_utils_components as fuc
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash_components import Card


# 二级菜单的标题、图标和显示顺序
title = '支付页'
icon = None
order = 2
logger = Log.get_logger(__name__)

access_metas = (
    '支付页-页面',
    '支付页-今年支付额',
    '支付页-可用余额',
)


def render_content(menu_access: MenuAccess, **kwargs):
    return fac.AntdFlex(
        [
            *(
                [
                    Card(
                        fac.AntdStatistic(
                            title='您的余额',
                            value=fuc.FefferyCountUp(end=112893, duration=3),
                        ),
                        title='您的余额',
                    )
                ]
                if menu_access.has_access('支付页-可用余额')
                else []
            ),
            *(
                [
                    Card(
                        fac.AntdStatistic(
                            title='您今年支付额',
                            value=fuc.FefferyCountUp(end=2873, duration=3),
                        ),
                    )
                ]
                if menu_access.has_access('支付页-今年支付额')
                else []
            ),
        ],
        wrap='wrap',
    )
