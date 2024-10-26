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
from typing import Dict
from dash.exceptions import PreventUpdate
from dash import set_props

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
                        className={'height': '50px', 'box-shadow': '0 1px 4px rgba(0,21,41,.08)'},
                    ),
                    # tabs块
                    fac.AntdRow(
                        fuc.FefferyDiv(
                            fac.AntdTabs(
                                id='tabs-container',
                                # fix bug: 必须有一个先置的tab，否则无法正常显示
                                items=[
                                    {
                                        'label': 'init',
                                        'key': 'init',
                                    }
                                ],
                                type='editable-card',
                                className={
                                    'width': '100%',
                                    'paddingLeft': '15px',
                                    'paddingRight': '15px',
                                },
                            ),
                            className={
                                'width': '100%',
                                'height': '100%',
                                '& .ant-tabs-nav-list .ant-tabs-tab': {
                                    'margin': '0 0px',
                                    'border-style': 'solid',
                                    'padding': '0 5px',
                                    'font-size': '14px',
                                    'border-radius': '2px',
                                },
                            },
                        )
                    ),
                ],
                flex='auto',
            ),
        ],
        className={'width': '100vw', 'height': '100vh'},
        id='global-full-screen-container',
    )


@app.callback(
    Output('tabs-container', 'items'),
    Input('global-url-location', 'href'),
    State('global-tabs-del-init', 'data'),  # fix bug: 存储是否删除tabs组件占位的内容
    prevent_initial_call=True,
)
def callback_func(href, has_del_init_tab):
    # 过滤无效回调
    if href is None:
        raise PreventUpdate
    from yarl import URL

    url = URL(href)
    try:
        # 访问路径，第一个为/，去除
        url_module_path = '.'.join(url.parts[1:])
        module_page = importlib.import_module(f'dash_view.application.{url_module_path}')
        # 查询参数
        url_query: Dict = url.query
        # 获取锚链接
        url_fragment: str = url.fragment
        # 合并查询和锚连接，组成综合参数
        param = {
            **url_query,
            **({'url_fragment': url_fragment} if url_fragment else {}),
        }
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
    # fix bug: 先删除tabs组件占位的内容，再加上新的tab
    if not has_del_init_tab:
        p.clear()
        set_props('global-tabs-del-init', {'data': 1})
    p.append(
        {
            'label': module_page.title,
            'key': url_module_path,
            'closable': True,
            'children': module_page.render_content(menu_access, **param),
            'contextMenu': [
                {
                    'key': '刷新页面',
                    'label': '刷新页面',
                    'icon': 'antd-reload',
                },
                {
                    'key': '关闭其他',
                    'label': '关闭其他',
                    'icon': 'antd-close-circle',
                },
                {
                    'key': '全部关闭',
                    'label': '全部关闭',
                    'icon': 'antd-close-circle',
                },
            ],
        }
    )
    return p
