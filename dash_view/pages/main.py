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
                                # fix bug: 占位
                                items=[
                                    {
                                        'label': '',
                                        'key': 'init',
                                        'children': 'init',
                                    }
                                ],
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


# 主路由函数：地址栏 -》 Tab新增+Tab切换+菜单展开+菜单选中+面包屑
@app.callback(
    [
        Output('tabs-container', 'items', allow_duplicate=True),
        Output('tabs-container', 'activeKey'),
        Output('global-menu', 'openKeys'),
        Output('global-menu', 'currentKey'),
        Output('header-breadcrumb', 'items'),
    ],
    Input('global-url-location', 'href'),
    [
        State('tabs-container', 'itemKeys'),
        State('menu-collapse-sider', 'collapsed'),
        State('global-url-location', 'trigger'),
        State('global-url-last-when-load', 'data'),
    ],
    prevent_initial_call=True,
)
def main_router(href, has_open_tab_keys: List, is_collapsed_menu: bool, trigger, url_last_when_load):
    # 过滤无效回调
    if href is None:
        raise PreventUpdate
    has_open_tab_keys = has_open_tab_keys or []

    url = URL(href)
    url_module_path = '.'.join(url.parts[1:])  # 访问路径，第一个为/，去除
    url_query: Dict = url.query  # 查询参数
    url_fragment: str = url.fragment  # 获取锚链接
    param = {
        **url_query,
        **({'url_fragment': url_fragment} if url_fragment else {}),
    }  # 合并查询和锚连接，组成综合参数

    # 当重载页面时，如果访问的不是首页，则先访问首页，再自动访问目标页
    relocation = False
    last_herf = ''
    if trigger == 'load' and url_module_path != 'dashboard.workbench':
        relocation = True
        url_module_path = 'dashboard.workbench'
        param = {}
        # 保存目标页的url
        from uuid import uuid4

        last_herf = str(
            URL()
            .with_path(url.path)
            .with_query(
                {**url_query, 'flush': str(uuid4())[:8]}
            )  # 添加随机码，强制刷新'global-url-location', 'href'，触发目标页面打开
            .with_fragment(url_fragment)
        )
    try:
        # 导入对应的页面模块
        module_page = importlib.import_module(f'dash_view.application.{url_module_path}')
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

    breadcrumb_items = [{'title': '首页', 'href': '/dashboard/workbench'}]
    _modules: List = url_module_path.split('.')
    for i in range(len(_modules)):
        breadcrumb_items = breadcrumb_items + [{'title': get_title('.'.join(_modules[: i + 1]))}]

    # 如已经打开，并且不带强制刷新参数,直接切换页面即可
    if key_url_path in has_open_tab_keys and param.get('flush', None) is None:
        return [
            dash.no_update,  # tab标签页
            key_url_path,  # tab选中key
            dash.no_update if is_collapsed_menu else [key_url_path_parent],  # 菜单展开
            key_url_path,  # 菜单选中
            breadcrumb_items,  # 面包屑
        ]

    # 获取用户权限
    menu_access = get_menu_access()
    # 没有权限，返回401
    if url_module_path not in menu_access.menu_item:
        set_props('global-full-screen-container', {'children': page_401.render()})
        return dash.no_update

    ################# 返回页面 #################
    p = Patch()
    if trigger == 'load':
        p.clear()
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
        return [
            p,  # tab标签页
            key_url_path,  # tab选中key
            dash.no_update if is_collapsed_menu else [key_url_path_parent],  # 菜单展开
            key_url_path,  # 菜单选中
            breadcrumb_items,  # 面包屑
        ]
    else:
        # 未打开，通过Patch组件，将新的tab添加到tabs组件中
        p.append(
            {
                'label': module_page.title,
                'key': key_url_path,
                # 工作台不能关闭
                'closable': False if key_url_path == '/dashboard/workbench' else True,
                'children': module_page.render_content(menu_access, **param),
            }
        )
        if relocation:
            # 激活超时组件，马上动态更新到目标页
            set_props('global-url-last-when-load', {'data': last_herf})
            set_props('global-url-timeout-last-when-load', {'delay': 0})
        return [
            p,  # tab标签页
            dash.no_update if relocation else key_url_path,  # tab选中key
            dash.no_update if is_collapsed_menu or relocation else [key_url_path_parent],  # 菜单展开
            dash.no_update if relocation else key_url_path,  # 菜单选中
            dash.no_update if relocation else breadcrumb_items,  # 面包屑
        ]


app.clientside_callback(
    """
        (timeoutCount,data) => {
            return data;
        }
    """,
    Output('global-dcc-url', 'href'),
    Input('global-url-timeout-last-when-load', 'timeoutCount'),
    State('global-url-last-when-load', 'data'),
)

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
