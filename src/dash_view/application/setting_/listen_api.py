from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash_components import Card
from dash_callback.application.setting_ import listen_api_c  # noqa
from i18n import t__setting
from feffery_dash_utils.style_utils import style


# 二级菜单的标题、图标和显示顺序
title = '监听接口'
icon = None
logger = Log.get_logger(__name__)
order = 2
access_metas = ('监听接口-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return fac.AntdSpace(
        [
            fac.AntdSpace(
                [
                    fac.AntdInput(size='small', placeholder=t__setting('输入通知渠道名'), id='listen-api-add-name'),
                    fac.AntdTooltip(
                        fac.AntdButton(t__setting('添加邮件IMAP协议'), type='primary', size='small', id='listen-api-add-email-imap'),
                        title=t__setting('按2分钟的周期轮询邮箱，获取最新的邮件'),
                    ),
                ],
                style=style(width=800),
            ),
            Card(
                fac.AntdCheckboxGroup(
                    options=(api_activate := listen_api_c.get_listen_api())[0],
                    value=api_activate[1],
                    id='listen-api-activate',
                ),
                title=t__setting('激活通道'),
            ),
            Card(
                fac.AntdTabs(
                    items=listen_api_c.get_tabs_items(),
                    id='listen-api-edit-tabs',
                    tabPosition='left',
                    tabBarGutter=0,
                    size='small',
                    placeholder=fac.AntdEmpty(description='There are no available listen api at present'),
                    style=style(width='100%'),
                ),
                title=t__setting('通道配置'),
            ),
        ],
        direction='vertical',
    )
