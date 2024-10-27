import feffery_antd_components as fac
from dash_view.framework.aside import render_aside_content
from dash.dependencies import Input, Output, State
from dash_view.framework.head import render_head_content
from dash_view.framework.func import render_func_content
from server import app
from common.utilities.util_menu_access import MenuAccess
from dash import Patch, dcc
import importlib
import feffery_utils_components as fuc
import dash
from typing import Dict, List
from dash.exceptions import PreventUpdate
from dash import set_props
from flask import request
from yarl import URL

# 折叠侧边栏按钮回调
app.clientside_callback(
    """(nClicks, collapsed) => {
        if (collapsed){
            return [!collapsed, 'antd-menu-fold',{'display':'block'}];
        }else{
            return [!collapsed, 'antd-menu-unfold',{'display':'None'}];
        }
    }""",
    [
        Output('menu-collapse-sider', 'collapsed'),
        Output('btn-menu-collapse-sider-menu-icon', 'icon'),
        Output('logo-text', 'style'),
    ],
    Input('btn-menu-collapse-sider-menu', 'nClicks'),
    State('menu-collapse-sider', 'collapsed'),
    prevent_initial_call=True,
)


def render_content(menu_access: MenuAccess):
    # 初始化访问页面
    module_page = importlib.import_module('dash_view.application.dashboard.workbench')
    init_items = [
        {
            'label': module_page.title,
            'key': 'dashboard.workbench',
            'children': module_page.render_content(menu_access),
            'closable': False,
            'contextMenu': [
                {
                    'key': '关闭其他',
                    'label': '关闭其他',
                    'icon': 'antd-close-circle',
                },
            ],
        }
    ]
    return fac.AntdRow(
        [
            # 功能组件注入
            *render_func_content(),
            # 菜单列
            fac.AntdCol(
                fac.AntdSider(
                    render_aside_content(menu_access),
                    collapsible=False,
                    collapsedWidth=60,
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
                        render_head_content(),
                        align='middle',
                        className={
                            'height': '50px',
                            'box-shadow': '0 1px 4px rgba(0,21,41,.08)',
                            'flex': 'None',
                        },
                    ),
                    # tabs块
                    fac.AntdRow(
                        fuc.FefferyDiv(
                            fac.AntdTabs(
                                id='tabs-container',
                                # 初始页面为工作台
                                items=init_items,
                                type='editable-card',
                                className={
                                    'width': '100%',
                                    'height': '100%',
                                    'paddingLeft': '8px',
                                    'paddingRight': '8px',
                                },
                            ),
                            className={
                                'width': '100%',
                                'height': '100%',
                                '& .ant-tabs-content-holder > .ant-tabs-content': {
                                    'height': 'calc(100% - 10px)',  # 不知道为什么溢出了一部分，减去10像素
                                },
                                '& .ant-tabs-content-holder > .ant-tabs-content > .ant-tabs-tabpane': {
                                    'height': '100%',
                                },
                                '& .ant-tabs-nav': {
                                    'margin': '8px 0 8px 0',
                                },
                                '& .ant-tabs-nav-list .ant-tabs-tab': {
                                    'margin': '0 0px',
                                    'border-style': 'solid',
                                    'padding': '0 5px',
                                    'font-size': '14px',
                                    'border-radius': '2px',
                                },
                            },
                        ),
                        className={'flex': '1'},
                    ),
                ],
                flex='auto',
                className={'display': 'flex', 'flex-direction': 'column'},
            ),
        ],
        className={'width': '100vw', 'height': '100vh'},
        id='global-full-screen-container',
    )


# 主路由函数+Tab管理
@app.callback(
    Output('tabs-container', 'items', allow_duplicate=True),
    Input('global-url-location', 'href'),
    State('tabs-container', 'itemKeys'),
    prevent_initial_call=True,
)
def main_router(href, has_open_tab_keys: List):
    # 过滤无效回调
    if href is None:
        raise PreventUpdate
    # 初始回调，无论tab是否有标签，都是空，所以这里预置一个工作台的key
    if has_open_tab_keys is None:
        has_open_tab_keys = ['dashboard.workbench']

    url = URL(href)
    try:
        url_module_path = '.'.join(url.parts[1:])  # 访问路径，第一个为/，去除
        # 导入对应的页面模块
        module_page = importlib.import_module(f'dash_view.application.{url_module_path}')
        url_query: Dict = url.query  # 查询参数
        url_fragment: str = url.fragment  # 获取锚链接
        param = {
            **url_query,
            **({'url_fragment': url_fragment} if url_fragment else {}),
        }  # 合并查询和锚连接，组成综合参数
    except Exception:
        # 没有该页面对应的模块，返回404
        from dash_view.pages.page_404 import render

        set_props('global-full-screen-container', {'children': render()})
        return dash.no_update

    from common.utilities.util_menu_access import get_menu_access

    # 获取用户权限
    menu_access = get_menu_access()
    # 没有权限，返回401
    if url_module_path not in menu_access.menu_item:
        from dash_view.pages.page_401 import render

        set_props('global-full-screen-container', {'children': render()})
        return dash.no_update
    p = Patch()
    if url_module_path in has_open_tab_keys:
        # 如已经打开，直接切换页面即可
        set_props('tabs-container', {'activeKey': url_module_path})
        return dash.no_update
    else:
        # 未打开，通过Patch组件，将新的tab添加到tabs组件中
        p.append(
            {
                'label': module_page.title,
                'key': url_module_path,
                'closable': True,
                'children': module_page.render_content(menu_access, **param),
                'contextMenu': [
                    {
                        'key': '关闭其他',
                        'label': '关闭其他',
                        'icon': 'antd-close-circle',
                    },
                ],
            }
        )
        set_props('tabs-container', {'activeKey': url_module_path})
        return p


# Tab关闭
@app.callback(
    Output('tabs-container', 'items', allow_duplicate=True),
    Input('tabs-container', 'tabCloseCounts'),
    [
        State('tabs-container', 'latestDeletePane'),
        State('tabs-container', 'itemKeys'),
        State('tabs-container', 'activeKey'),
    ],
    prevent_initial_call=True,
)
def close_tab(tabCloseCounts, latestDeletePane_key, has_open_tab_keys: List, activeKey):
    idx_close = has_open_tab_keys.index(latestDeletePane_key)
    p = Patch()
    del p[idx_close]
    has_open_tab_keys.pop(idx_close)
    if activeKey == latestDeletePane_key:
        set_props('tabs-container', {'activeKey': has_open_tab_keys[-1]})
    return p
