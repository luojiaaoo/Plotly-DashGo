import feffery_antd_components as fac
import feffery_utils_components as fuc
from dash import get_asset_url
from config.dash_melon_conf import ShowConf
from common.utilities.util_menu_access import MenuAccess


def render_aside_content(menu_access: MenuAccess):
    return fuc.FefferyDiv(
        [
            # logo 和 app名
            fac.AntdRow(
                fac.AntdSpace(
                    [
                        fac.AntdImage(
                            width=40,
                            height=40,
                            src=get_asset_url('imgs/logo.png'),
                            preview=False,
                        ),
                        fac.AntdText(
                            ShowConf.APP_NAME,
                            id='logo-text',
                            ellipsis=True,
                            className={
                                'fontSize': '20px',
                                'fontWeight': 'bold',
                                'color': 'rgb(245,245,245)',
                            },
                            style={'display': 'None'},
                        ),
                    ]
                ),
                className={
                    'height': '60px',
                    'background': 'rgb( 43, 47, 58)',
                    'position': 'sticky',
                    'top': 0,
                    'zIndex': 999,
                    'paddingTop': '12px',
                    'paddingLeft': '12px',
                    'paddingRight': '20px',
                    'paddingBottom': '12px',
                },
            ),
            # 目录
            fac.AntdRow(
                fac.AntdMenu(
                    id='global-menu',
                    menuItems=menu_access.menu,
                    mode='inline',
                    theme='dark',
                    onlyExpandCurrentSubMenu=True,
                    expandIcon={
                        'expand': fac.AntdIcon(icon='antd-right'),
                        'collapse': fac.AntdIcon(icon='antd-caret-down'),
                    },
                )
            ),
        ],
        # 修改目录的样式
        className={
            '.ant-menu-submenu-title, .ant-menu': {'backgroundColor': 'rgb( 43, 47, 58)', 'overflow': 'hidden'},
            '.ant-menu-submenu-title:hover': {'color': '#fff'},
            '.ant-menu-item-selected': {
                'backgroundColor': 'rgba(0,0,0,0)',
                'borderRight': '2px solid rgb(64,143,201)',
                'borderRadius': '0.8em',
                'color': 'rgb(64,143,201)',
            },
        },
    )
