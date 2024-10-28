import feffery_antd_components as fac
from dash_view.framework.aside import render_aside_content
from dash.dependencies import Input, Output, State
from dash_view.framework.head import render_head_content
from dash_view.framework.func import render_func_content
from server import app
from common.utilities.util_menu_access import MenuAccess
from dash import Patch
import importlib
import feffery_utils_components as fuc
import dash
from typing import Dict, List
from dash.exceptions import PreventUpdate
from dash import set_props
from yarl import URL
from common.utilities.util_menu_access import get_menu_access
from dash_view.pages import page_404, page_401

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
            'key': '/dashboard/workbench',
            'children': module_page.render_content(menu_access),
            'closable': False,
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
                            'boxShadow': '0 1px 4px rgba(0,21,41,.08)',
                            'flex': 'None',
                        },
                    ),
                    # tabs块
                    fac.AntdRow(
                        fuc.FefferyDiv(
                            fac.AntdTabs(
                                id='tabs-container',
                                tabPaneAnimated=True,
                                size='small',
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
                            },
                        ),
                        className={'flex': '1'},
                    ),
                ],
                flex='auto',
                className={'display': 'flex', 'flexDirection': 'column'},
            ),
        ],
        className={'width': '100vw', 'height': '100vh'},
        id='global-full-screen-container',
    )


init_breadcrumb_items = [{'title': '首页', 'href': '/dashboard/workbench'}]


# 主路由函数：地址栏 -》 Tab新增+Tab切换+菜单展开+菜单选中+面包屑
@app.callback(
    Output('tabs-container', 'items', allow_duplicate=True),
    Input('global-url-location', 'href'),
    [
        State('tabs-container', 'itemKeys'),
        State('menu-collapse-sider', 'collapsed'),
    ],
    prevent_initial_call=True,
)
def main_router(href, has_open_tab_keys: List, is_collapsed_menu: bool):
    # 过滤无效回调
    if href is None:
        raise PreventUpdate
    # 初始回调，无论tab是否有标签，都是空，所以这里预置一个工作台的key
    if has_open_tab_keys is None:
        has_open_tab_keys = ['/dashboard/workbench']

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
        set_props('global-full-screen-container', {'children': page_404.render()})
        return dash.no_update

    def module_path2url_path(module_path: str, parent_count=0) -> str:
        if parent_count > 0:
            return '/' + '/'.join(module_path.split('.')[:-parent_count])
        else:
            return '/' + '/'.join(module_path.split('.'))

    # 构建key的字符串格式
    key_url_path = module_path2url_path(url_module_path)
    key_url_path_parent = module_path2url_path(url_module_path, 1)

    # 构建面包屑格式
    def get_title(module_path):
        from dash_view import application  # noqa

        return eval(f'application.{module_path}.title')

    breadcrumb_items = init_breadcrumb_items
    _modules: List = url_module_path.split('.')
    for i in range(len(_modules)):
        breadcrumb_items = breadcrumb_items + [{'title': get_title('.'.join(_modules[: i + 1]))}]

    # 如已经打开，并且不带强制刷新参数,直接切换页面即可
    if key_url_path in has_open_tab_keys and param.get('flush', None) is None:
        set_props('header-breadcrumb', {'items': breadcrumb_items})
        set_props('tabs-container', {'activeKey': key_url_path})
        set_props('global-menu', {'currentKey': key_url_path})
        if not is_collapsed_menu:
            set_props('global-menu', {'openKeys': [key_url_path_parent]})
        return dash.no_update

    # 获取用户权限
    menu_access = get_menu_access()
    # 没有权限，返回401
    if url_module_path not in menu_access.menu_item:
        set_props('global-full-screen-container', {'children': page_401.render()})
        return dash.no_update

    ################# 返回页面 #################
    p = Patch()
    if key_url_path in has_open_tab_keys and param.get('flush', None) is not None:
        # 如果已经打开，但是带有flush的query，就重新打开，通过Patch组件，删除老的，将新的tab添加到tabs组件中
        old_idx = has_open_tab_keys.index(key_url_path)
        del p[old_idx]
        p.insert(
            old_idx,
            {
                'label': module_page.title,
                'key': key_url_path,
                'closable': True,
                'children': module_page.render_content(menu_access, **param),
            },
        )
        set_props('header-breadcrumb', {'items': breadcrumb_items})
        set_props('tabs-container', {'activeKey': key_url_path})
        set_props('global-menu', {'currentKey': key_url_path})
        if not is_collapsed_menu:
            set_props('global-menu', {'openKeys': [key_url_path_parent]})
        return dash.no_update
    else:
        # 未打开，通过Patch组件，将新的tab添加到tabs组件中
        p.append(
            {
                'label': module_page.title,
                'key': key_url_path,
                'closable': True,
                'children': module_page.render_content(menu_access, **param),
            }
        )
        set_props('header-breadcrumb', {'items': breadcrumb_items})
        set_props('tabs-container', {'activeKey': key_url_path})
        set_props('global-menu', {'currentKey': key_url_path})
        if not is_collapsed_menu:
            set_props('global-menu', {'openKeys': [key_url_path_parent]})
        return p


# 地址栏随tabs的activeKey变化
app.clientside_callback(
    """
    (activeKey) => {
        if (activeKey === undefined){
            return window.dash_clientside.no_update;
        }
        return activeKey;
    }
    """,
    Output('global-dcc-url', 'pathname'),
    Input('tabs-container', 'activeKey'),
    prevent_initial_call=True,
)


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
