from common.utilities.util_menu_access import MenuAccess
import feffery_utils_components as fuc
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash import html, dcc
from dash_components import Card, Table
import dash_callback.application.dashboard_.monitor_c  # noqa
from functools import partial
from i18n import translator

_ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('购买页')


icon = None
order = 2
logger = Log.get_logger(__name__)

access_metas = (
    '购买页-页面',
    '购买页-已买商品',
    '购买页-购物车',
)


def render_content(menu_access: MenuAccess, **kwargs):
    all_access_metas = menu_access.all_access_metas
    fac.AntdFlex(
        [
            *(
                [
                    Card(
                        Table(
                            columns=[
                                {'title': '商品名', 'dataIndex': '商品名'},
                                {'title': '支付额', 'dataIndex': '支付额'},
                            ],
                            data=[
                                {
                                    '商品名': '鞋子',
                                    '支付额': '￥86.3',
                                }
                            ]
                            * 3,
                        )
                    )
                ]
                if '购买页-已买商品' in all_access_metas
                else []
            ),
            *(
                [
                    Card(
                        Table(
                            columns=[
                                {'title': '商品名', 'dataIndex': '商品名'},
                                {'title': '价格', 'dataIndex': '价格'},
                            ],
                            data=[
                                {
                                    '商品名': '衬衫',
                                    '价格': '￥22.1',
                                }
                            ]
                            * 3,
                        )
                    )
                ]
                if '购买页-购物车' in all_access_metas
                else []
            ),
        ],
        wrap='wrap',
    )
