import feffery_antd_components as fac
from dash import get_asset_url
from config.dash_melon_conf import ShowConf
from server import app


def render_aside_content():
    return fac.AntdCol(
        [
            fac.AntdRow(
                [
                    fac.AntdCol(
                        fac.AntdImage(
                            width=40,
                            height=40,
                            src=get_asset_url('imgs/logo.png'),
                            preview=False,
                        ),
                        flex='1',
                        className={
                            'height': '100%',
                            'alignItems': 'center',
                        },
                    ),
                    fac.AntdCol(
                        fac.AntdText(
                            ShowConf.APP_NAME,
                            id='logo-text',
                            className={
                                'fontSize': '20px',
                                'font-weight': 'bold',
                                'color': 'rgb(245,245,245)',
                            },
                        ),
                        flex='5',
                        className={
                            'height': '100%',
                            'alignItems': 'center',
                            'marginLeft': '20px',
                        },
                    ),
                ],
                style={
                    'height': '60px',
                    'background': 'rgb( 43, 47, 58)',
                    'position': 'sticky',
                    'top': 0,
                    'zIndex': 999,
                    'padding-top': '12px',
                    'padding-left': '12px',
                    'padding-right': '20px',
                    'padding-bottom': '12px',
                },
            ),
            fac.AntdRow(
                fac.AntdMenu(
                    menuItems=[
                        {
                            'component': 'SubMenu',
                            'props': {
                                'key': f'{sub_menu}',
                                'title': f'子菜单{sub_menu}',
                            },
                            'children': [
                                {
                                    'component': 'ItemGroup',
                                    'props': {
                                        'key': f'{sub_menu}-{item_group}',
                                        'title': f'菜单项分组{sub_menu}-{item_group}',
                                    },
                                    'children': [
                                        {
                                            'component': 'Item',
                                            'props': {
                                                'key': f'{sub_menu}-{item_group}-{item}',
                                                'title': f'菜单项{sub_menu}-{item_group}-{item}',
                                            },
                                        }
                                        for item in range(1, 3)
                                    ],
                                }
                                for item_group in range(1, 3)
                            ],
                        }
                        for sub_menu in range(1, 5)
                    ],
                    mode='inline',
                    theme='dark',
                    className={'height': 'calc(100vh-60px)'},
                    onlyExpandCurrentSubMenu=True,
                    expandIcon={
                        'expand': fac.AntdIcon(icon='antd-right'),
                        'collapse': fac.AntdIcon(icon='antd-caret-down'),
                    },
                )
            ),
        ],
        className={
            'height': '100vh',
            'background': 'rgb( 43, 47, 58)',
            '.ant-menu-submenu-title, .ant-menu': {'background-color': 'rgb( 43, 47, 58)'},
            '.ant-menu-submenu-title:hover': {'color': '#fff'},
            '.ant-menu-item-selected': {
                'background-color': 'rgba(0,0,0,0)',
                'border-left': '2px solid rgb(64,143,201)',
                'border-radius': '0',
                'color': 'rgb(64,143,201)',
            },
        },
    )
