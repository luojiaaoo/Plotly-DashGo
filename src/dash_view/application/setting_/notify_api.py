from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash_components import Card
from dash_callback.application.setting_ import notify_api_c  # noqa
from i18n import t__setting


# 二级菜单的标题、图标和显示顺序
title = '通知接口'
icon = None
logger = Log.get_logger(__name__)
order = 1
access_metas = ('通知接口-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return fac.AntdSpace(
        [
            Card(
                fac.AntdCheckboxGroup(
                    options=(api_activate := notify_api_c.get_notify_api_activate())[0],
                    value=api_activate[1],
                    id='notify-api-activate',
                ),
                title=t__setting('激活通道'),
            ),
            Card(
                fac.AntdSpace(
                    [
                        fac.AntdTabs(
                            items=notify_api_c.get_tabs_items(),
                            id='notify-api-edit-tabs',
                            tabPosition='left',
                            defaultActiveKey='Server酱',
                        ),
                    ],
                    direction='vertical',
                ),
                title=t__setting('通道配置'),
            ),
        ],
        direction='vertical',
    )
