from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash_components import Card
from dash_callback.application.setting_ import notify_api_c  # noqa
from i18n import t__setting
from feffery_dash_utils.style_utils import style


# 二级菜单的标题、图标和显示顺序
title = '通知接口'
icon = None
logger = Log.get_logger(__name__)
order = 1
access_metas = ('通知接口-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return fac.AntdSpace(
        [
            fac.AntdButton(
                '💕' + t__setting('一天1毛钱的极简微信等消息接口，点击此处购买Server酱消息推送') + '💕',
                variant='dashed',
                color='primary',
                href='https://sct.ftqq.com/r/16293',
                target='_blank',
            ),
            fac.AntdSpace(
                [
                    fac.AntdInput(size='small', placeholder=t__setting('输入通知渠道名'), id='notify-api-add-name'),
                    fac.AntdButton(t__setting('添加Server酱'), type='primary', size='small', id='notify-api-add-serverchan'),
                    fac.AntdButton(t__setting('添加企业微信群机器人'), type='primary', size='small', id='notify-api-add-wecom-group-robot'),
                    fac.AntdButton(t__setting('添加邮件SMTP协议'), type='primary', size='small', id='notify-api-add-email-smtp'),
                ],
                style=style(width=800),
            ),
            Card(
                fac.AntdCheckboxGroup(
                    options=(api_activate := notify_api_c.get_notify_api())[0],
                    value=api_activate[1],
                    id='notify-api-activate',
                ),
                title=t__setting('激活通道'),
            ),
            Card(
                fac.AntdTabs(
                    items=notify_api_c.get_tabs_items(),
                    id='notify-api-edit-tabs',
                    tabPosition='left',
                    tabBarGutter=0,
                    size='small',
                    placeholder=fac.AntdEmpty(description='There are no available notify api at present'),
                    style=style(width='100%'),
                ),
                title=t__setting('通道配置'),
            ),
        ],
        direction='vertical',
    )
