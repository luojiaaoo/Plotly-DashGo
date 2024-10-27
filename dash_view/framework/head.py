import feffery_antd_components as fac
from dash import html


def render_head_content():
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
                items=[{'title': '首页', 'icon': 'antd-dashboard', 'href': '/#'}],
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
                    fac.AntdPopover(
                        fac.AntdBadge(
                            fac.AntdAvatar(
                                id='avatar-info',
                                mode='image',
                                src='',
                                size=36,
                            ),
                            count=6,
                            size='small',
                        ),
                        content=fac.AntdTabs(
                            items=[
                                {
                                    'key': '未读消息',
                                    'label': '未读消息',
                                    'children': [
                                        fac.AntdSpace(
                                            [
                                                html.Div(
                                                    fac.AntdText(f'消息示例{i}'),
                                                    style={
                                                        'padding': '5px 10px',
                                                        'height': 40,
                                                        'width': 300,
                                                        'borderBottom': '1px solid #f1f3f5',
                                                    },
                                                )
                                                for i in range(1, 8)
                                            ],
                                            direction='vertical',
                                            style={
                                                'height': 280,
                                                'overflowY': 'auto',
                                            },
                                        )
                                    ],
                                },
                                {
                                    'key': '已读消息',
                                    'label': '已读消息',
                                    'children': [
                                        fac.AntdSpace(
                                            [
                                                html.Div(
                                                    fac.AntdText(f'消息示例{i}'),
                                                    style={
                                                        'padding': '5px 10px',
                                                        'height': 40,
                                                        'width': 300,
                                                        'borderBottom': '1px solid #f1f3f5',
                                                    },
                                                )
                                                for i in range(8, 15)
                                            ],
                                            direction='vertical',
                                            style={
                                                'height': 280,
                                                'overflowY': 'auto',
                                            },
                                        )
                                    ],
                                },
                            ],
                            centered=True,
                        ),
                        placement='bottomRight',
                    ),
                    fac.AntdDropdown(
                        id='index-header-dropdown',
                        title='Luoja',
                        arrow=True,
                        menuItems=[
                            {
                                'title': '个人资料',
                                'key': '个人资料',
                                'icon': 'antd-idcard',
                            },
                            {
                                'title': '布局设置',
                                'key': '布局设置',
                                'icon': 'antd-layout',
                            },
                            {'isDivider': True},
                            {
                                'title': '退出登录',
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
    ]
