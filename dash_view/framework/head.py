import feffery_antd_components as fac
from dash import html
from dash_view.framework.lang import render_lang_content
from common.utilities.util_menu_access import MenuAccess
from common.utilities.util_path import get_avatar_url
from flask_babel import gettext as _  # noqa
from server import app
from dash.dependencies import Input, Output, State
import dash
from dash.exceptions import PreventUpdate


def render_head_content(menu_access: MenuAccess):
    return [
        # 页首左侧折叠按钮区域
        fac.AntdCol(
            fac.AntdButton(
                fac.AntdIcon(id='btn-menu-collapse-sider-menu-icon', icon='antd-menu-fold'),
                id='btn-menu-collapse-sider-menu',
                type='text',
                shape='circle',
                size='large',
                style={
                    'marginLeft': '5px',
                    'marginRight': '15px',
                    'background': 'rgba(0,0,0,0)',
                },
            ),
            style={
                'height': '100%',
                'display': 'flex',
                'alignItems': 'center',
            },
            flex='None',
        ),
        # 页首面包屑区域
        fac.AntdCol(
            fac.AntdBreadcrumb(
                items=[{'title': _('首页'), 'href': '/dashboard/workbench'}],
                id='header-breadcrumb',
                style={
                    'height': '100%',
                    'display': 'flex',
                    'alignItems': 'center',
                },
            ),
            id='header-breadcrumb-col',
            flex='1',
        ),
        # 页首右侧用户信息区域
        fac.AntdCol(
            fac.AntdSpace(
                [
                    fac.AntdBadge(
                        fac.AntdAvatar(
                            id='global-head-avatar',
                            mode='image',
                            src=get_avatar_url(menu_access.user_name),
                            alt=menu_access.user_info.user_full_name,
                            size=36,
                        ),
                        # count=6, # todo: 消息通知
                        size='small',
                    ),
                    fac.AntdDropdown(
                        id='global-head-user-name-dropdown',
                        title=menu_access.user_name,
                        arrow=True,
                        menuItems=[
                            {
                                'title': _('个人信息'),
                                'key': '个人信息',
                                'icon': 'antd-idcard',
                            },
                            {'isDivider': True},
                            {
                                'title': _('退出登录'),
                                'key': '退出登录',
                                'icon': 'antd-logout',
                            },
                        ],
                        placement='bottomRight',
                    ),
                ],
                style={
                    'height': '100%',
                    'float': 'right',
                    'display': 'flex',
                    'alignItems': 'center',
                    'paddingRight': '20px',
                },
            ),
            flex='None',
        ),
        render_lang_content(),
    ]


# 个人信息，退出登录
@app.callback(
    [
        Output('global-dcc-url', 'pathname', allow_duplicate=True),
        Output('global-reload', 'reload', allow_duplicate=True),
    ],
    Input('global-head-user-name-dropdown', 'nClicks'),
    State('global-head-user-name-dropdown', 'clickedKey'),
    prevent_initial_call=True,
)
def callback_func(nClicks, clickedKey):
    if clickedKey == '退出登录':
        from common.utilities.util_jwt import clear_access_token_from_session

        clear_access_token_from_session()
        return dash.no_update, True
    elif clickedKey == '个人信息':
        return '/person/personal_info', dash.no_update
    return PreventUpdate
