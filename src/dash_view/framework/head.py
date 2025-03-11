import feffery_antd_components as fac
from dash_view.framework.lang import render_lang_content
from common.utilities.util_menu_access import MenuAccess
from dash import html
from server import app
from dash.dependencies import Input, Output, State
import dash
from dash.exceptions import PreventUpdate
from database.sql_db.dao import dao_announcement
from i18n import t__access, t__other, t__default


def render_head_content(menu_access: MenuAccess):
    return [
        # 页首左侧折叠按钮区域
        fac.AntdCol(
            fac.AntdButton(
                fac.AntdIcon(id='btn-menu-collapse-sider-menu-icon', icon='antd-menu-unfold'),
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
            fac.AntdSpace(
                [
                    fac.AntdBreadcrumb(
                        items=[{'title': t__access('首页'), 'href': '/dashboard_/workbench'}],
                        id='header-breadcrumb',
                        style={
                            'height': '100%',
                            'display': 'flex',
                            'alignItems': 'center',
                        },
                    ),
                    *(
                        [
                            fac.AntdAlert(
                                message=dao_announcement.get_announcement(),
                                type='info',
                                banner=True,
                                showIcon=True,
                                icon='📢',
                                messageRenderMode='loop-text',
                                className={
                                    'backgroundColor': 'rgba(0,0,0,0)',
                                    'maxWidth': '20em',
                                    'marginLeft': '50px',
                                    'border': '1px',
                                },
                            )
                        ]
                        if dao_announcement.get_announcement()
                        else []
                    ),
                ],
                style={
                    'height': '100%',
                    'alignItems': 'center',
                },
                wrap=False,
            ),
            id='header-breadcrumb-col',
            flex='1',
        ),
        # 页首右侧用户信息区域
        fac.AntdCol(
            fac.AntdSpace(
                [
                    html.A(
                        html.Img(src='https://img.shields.io/github/stars/luojiaaoo/DashGo.svg?style=social&label=Stars'),
                        href='https://github.com/luojiaaoo/DashGo',
                        target='_blank',
                        style={
                            'height': '100%',
                            'alignItems': 'center',
                        },
                    ),
                    html.A(
                        html.Img(src='https://gitee.com/luojiaaoo/DashGo/badge/star.svg?theme=dark'),
                        href='https://gitee.com/luojiaaoo/DashGo',
                        target='_blank',
                        style={
                            'height': '100%',
                            'alignItems': 'center',
                            'marginRight': '40px',
                        },
                    ),
                    fac.AntdBadge(
                        fac.AntdAvatar(
                            id='global-head-avatar',
                            mode='image',
                            src=f'/avatar/{menu_access.user_info.user_name}',
                            alt=menu_access.user_info.user_full_name,
                            size=36,
                        ),
                        # count=6, # TODO: 消息通知
                        size='small',
                    ),
                    fac.AntdDropdown(
                        id='global-head-user-name-dropdown',
                        title=menu_access.user_name,
                        arrow=True,
                        trigger='click',
                        menuItems=[
                            {
                                'title': t__access('个人信息'),
                                'key': '个人信息',
                                'icon': 'antd-idcard',
                            },
                            {'isDivider': True},
                            {
                                'title': t__other('退出登录'),
                                'key': '退出登录',
                                'icon': 'antd-logout',
                            },
                        ],
                        placement='bottomRight',
                    ),
                    fac.AntdTooltip(
                        fac.AntdIcon(
                            id='global-full-screen',
                            icon='antd-full-screen',
                            debounceWait=300,
                            style={'cursor': 'pointer', 'marginLeft': '12px', 'fontSize': '1.2em'},
                        ),
                        title=t__default('全屏'),
                        placement='left',
                    ),
                    render_lang_content(),
                ],
                style={
                    'height': '100%',
                    'display': 'flex',
                    'alignItems': 'center',
                    'paddingRight': '10px',
                },
                wrap=False,
            ),
            flex='None',
        ),
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
        return '/person_/personal_info', dash.no_update
    return PreventUpdate


# 全屏
app.clientside_callback(
    """
    (nClicks) => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            if (document.exitFullscreen) {
            document.exitFullscreen();
            }
        }
    }
    """,
    Input('global-full-screen', 'nClicks'),
    prevent_initial_call=True,
)
