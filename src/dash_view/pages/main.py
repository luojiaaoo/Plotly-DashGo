import feffery_antd_components as fac
from dash_view.framework.aside import render_aside_content
from dash_view.framework.head import render_head_content
from common.utilities.util_browser import get_browser_info
from common.utilities.util_menu_access import MenuAccess
import feffery_utils_components as fuc
from i18n import t__default
from dash_view.framework import func_main
from dash_callback.pages.main_c import parse_url, is_independent
from dash_view.pages import page_403, page_404
import importlib
import dash_callback.pages.main_c  # noqa


def render_content(menu_access: MenuAccess, href: str):
    _, url_menu_item, url_query, _, param = parse_url(href=href)
    # 检查是否有这个页面，返回404
    try:
        module_page = importlib.import_module(f'dash_view.application.{url_menu_item}')
    except Exception:
        return page_404.render()
    # 检查权限，没有权限，返回403
    if url_menu_item not in menu_access.menu_items:
        return page_403.render()
    # 是否为独立页面，直接返回独立页面，无需渲染框架
    if is_independent(url_query):
        return module_page.render_content(menu_access, **param)
    return fac.AntdRow(
        [
            # 功能组件注入
            fac.Fragment(func_main.render()),
            # 菜单列
            fac.AntdCol(
                fac.AntdSider(
                    render_aside_content(menu_access),
                    collapsed=False,
                    collapsible=True,
                    collapsedWidth=60,
                    width=225,
                    trigger=None,
                    id='menu-collapse-sider',
                ),
                flex='None',
                className={
                    'background': 'rgb( 43, 47, 58)',
                },
            ),
            # 内容列
            fac.AntdCol(
                [
                    # head块，包括菜单折叠、面包屑导航、用户信息、全局功能按钮
                    fac.AntdRow(
                        render_head_content(menu_access),
                        align='middle',
                        className={
                            'marginRight': '8px',
                            'height': '50px',
                            'boxShadow': '0 1px 4px rgba(0,21,41,.08)',
                        },
                    ),
                    # tabs块
                    fac.AntdRow(
                        fuc.FefferyDiv(
                            fac.AntdTabs(
                                id='tabs-container',
                                tabPaneAnimated=False,
                                tabBarRightExtraContent=fac.AntdSpace(
                                    [
                                        fac.AntdTooltip(
                                            fac.AntdIcon(
                                                id='tabs-open-independent',
                                                icon='antd-export',
                                                debounceWait=300,
                                                style={'cursor': 'pointer', 'marginRight': '10px', 'fontSize': '1.2em'},
                                            ),
                                            title=t__default('新页面打开'),
                                            placement='left',
                                        ),
                                        fac.AntdTooltip(
                                            fac.AntdIcon(
                                                id='tabs-refresh',
                                                icon='fc-synchronize',
                                                debounceWait=300,
                                                style={'cursor': 'pointer', 'marginRight': '10px', 'fontSize': '1.2em'},
                                            ),
                                            title=t__default('刷新'),
                                            placement='left',
                                        ),
                                    ]
                                ),
                                size='small',
                                items=[],
                                type='editable-card',
                                className={
                                    'width': '100%',
                                    'height': 'calc(100vh - 50px)',
                                    'paddingLeft': '8px',
                                    'paddingRight': '8px',
                                },
                            ),
                            className={
                                'width': '100%',
                                'height': 'calc(100vh - 50px)',
                                ### 美化滚动条
                                '& .ant-tabs-content-holder': {
                                    'height': '100%',
                                    'overflow': 'auto',
                                    'scrollbar-width': 'thin',
                                    'scrollbar-color': 'rgba(144,147,153,.2) #fff',
                                },
                                **(
                                    {
                                        '& .ant-tabs-content-holder::-webkit-scrollbar': {'width': '8px'},
                                        '& .ant-tabs-content-holder::-webkit-scrollbar-track': {'background': '#fff', 'border-radius': '10px'},
                                        '& .ant-tabs-content-holder::-webkit-scrollbar-thumb': {'background': 'rgba(144,147,153,.2)', 'border-radius': '10px'},
                                        '& .ant-tabs-content-holder::-webkit-scrollbar-thumb:hover': {'background': 'rgba(144,147,153,.4)'},
                                    }
                                    if get_browser_info().type != 'firefox'
                                    else {}
                                ),  ## 火狐浏览器不支持通过伪类自定义滚动条样式
                                '& .ant-tabs-content-holder > .ant-tabs-content': {'height': '100%'},
                                '& .ant-tabs-content-holder > .ant-tabs-content > .ant-tabs-tabpane': {'height': '100%', 'paddingBottom': '8px'},
                                '& .ant-tabs-nav': {'margin': '8px 0 8px 0'},
                            },
                        ),
                        className={'height': 'calc(100vh - 50px)'},
                        gutter=0,
                    ),
                ],
                flex='auto',
            ),
        ],
        className={'width': '100vw', 'height': '100vh'},
        wrap=False,
    )
