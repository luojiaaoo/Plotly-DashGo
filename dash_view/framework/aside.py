import feffery_antd_components as fac
from dash import  get_asset_url
from config.dash_melon_conf import ShowConf

def render_aside_content(menu_info=None):
    menu_info = [
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
    ]
    return [
        fac.AntdSider(
            [
                fac.AntdRow(
                    [
                        fac.AntdCol(
                            fac.AntdImage(
                                width=32,
                                height=32,
                                src=get_asset_url('imgs/logo.png'),
                                preview=False,
                            ),
                            flex='1',
                            style={
                                'height': '100%',
                                'display': 'flex',
                                'alignItems': 'center',
                            },
                        ),
                        fac.AntdCol(
                            fac.AntdText(
                                ShowConf.APP_NAME,
                                id='logo-text',
                                style={
                                    'fontSize': '22px',
                                    'color': 'rgb(255, 255, 255)',
                                },
                            ),
                            flex='5',
                            style={
                                'height': '100%',
                                'display': 'flex',
                                'alignItems': 'center',
                                'marginLeft': '25px',
                            },
                        ),
                    ],
                    style={
                        'height': '50px',
                        'background': '#001529',
                        'position': 'sticky',
                        'top': 0,
                        'zIndex': 999,
                        'paddingLeft': '18px',
                    },
                ),
                fac.AntdMenu(
                    id='index-side-menu',
                    menuItems=menu_info,
                    mode='inline',
                    theme='dark',
                    defaultSelectedKey='首页',
                    style={'width': '100%', 'height': 'calc(100vh - 50px)'},
                ),
            ],
            id='menu-collapse-sider-custom',
            collapsible=True,
            collapsedWidth=64,
            trigger=None,
            width=256,
        ),
    ]
