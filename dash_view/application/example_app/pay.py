from common.utilities.util_menu_access import MenuAccess
import feffery_utils_components as fuc
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash import html, dcc
from dash_components import Card
import dash_callback.application.dashboard_.monitor_c  # noqa
from functools import partial
from i18n import translator

_ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('支付页')


icon = None
order = 2
logger = Log.get_logger(__name__)

access_metas = (
    '支付页-页面',
    '支付页-今年支付额',
    '支付页-可用余额',
)


def render_content(menu_access: MenuAccess, **kwargs):
    all_access_metas = menu_access.all_access_metas
    return fac.AntdFlex(
        [
            *(
                [
                    Card(
                        fac.AntdStatistic(
                            title=_('您的余额'),
                            value=fuc.FefferyCountUp(end=112893, duration=3),
                        ),
                        title='您的余额',
                    )
                ]
                if '支付页-可用余额' in all_access_metas
                else []
            ),
            *(
                [
                    Card(
                        fac.AntdStatistic(
                            title=_('您今年支付额'),
                            value=fuc.FefferyCountUp(end=2873, duration=3),
                        ),
                    )
                ]
                if '支付页-今年支付额' in all_access_metas
                else []
            ),
        ],
        wrap='wrap',
    )
