from dash.dependencies import Input, Output, State
from uuid import uuid4
from server import app
from dash import Patch
import importlib
import dash
from typing import Dict, List
from dash.exceptions import PreventUpdate
from dash import set_props
from yarl import URL
from common.utilities.util_menu_access import get_menu_access
from dash_view.pages import page_404, page_401
from i18n import t__access

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
        Output('menu-collapse-sider', 'collapsed', allow_duplicate=True),
        Output('btn-menu-collapse-sider-menu-icon', 'icon'),
        Output('logo-text', 'style'),
    ],
    Input('btn-menu-collapse-sider-menu', 'nClicks'),
    State('menu-collapse-sider', 'collapsed'),
    prevent_initial_call=True,
)

# 宽度小于700px时，侧边栏自动折叠
app.clientside_callback(
    """(_width,nClicks,collapsed) => {
        _width = _width || 999;
        nClicks = nClicks || 0;
        if (_width < 700 && !collapsed){
            return nClicks+1;
        }
        return window.dash_clientside.no_update;
    }""",
    Output('btn-menu-collapse-sider-menu', 'nClicks'),
    Input('global-window-size', '_width'),
    [
        State('btn-menu-collapse-sider-menu', 'nClicks'),
        State('menu-collapse-sider', 'collapsed'),
    ],
    prevent_initial_call=True,
)

# 地址栏-》更新地址URL中继store 或者 直接切换页面不进行路由回调
app.clientside_callback(
    """
        (href,activeKey_tab,has_open_tab_keys,opened_tab_pathname_infos,collapsed) => {
            if (has_open_tab_keys === undefined){
                has_open_tab_keys = [];
            }
            const urlObj = new URL(href);
            pathname = urlObj.pathname;
            if (has_open_tab_keys.includes(pathname)){
                if (collapsed){
                    return [window.dash_clientside.no_update, window.dash_clientside.no_update, opened_tab_pathname_infos[pathname][1], opened_tab_pathname_infos[pathname][2],pathname];
                }else{
                    return [window.dash_clientside.no_update, [opened_tab_pathname_infos[pathname][0]], opened_tab_pathname_infos[pathname][1], opened_tab_pathname_infos[pathname][2],pathname];
                }
            }else{
                return [href, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
            }
        }
    """,
    [
        Output('global-url-relay', 'data', allow_duplicate=True),
        Output('global-menu', 'openKeys', allow_duplicate=True),
        Output('global-menu', 'currentKey', allow_duplicate=True),
        Output('header-breadcrumb', 'items', allow_duplicate=True),
        Output('tabs-container', 'activeKey', allow_duplicate=True),
    ],
    Input('global-url-location', 'href'),
    [
        State('tabs-container', 'activeKey'),
        State('tabs-container', 'itemKeys'),
        State('global-opened-tab-pathname-infos', 'data'),
        State('menu-collapse-sider', 'collapsed'),
    ],
    prevent_initial_call=True,
)


# 主路由函数：地址URL中继store -》 Tab新增+Tab切换+菜单展开+菜单选中+面包屑
@app.callback(
    [
        Output('tabs-container', 'items', allow_duplicate=True),
        Output('tabs-container', 'activeKey', allow_duplicate=True),
        Output('global-menu', 'openKeys', allow_duplicate=True),
        Output('global-menu', 'currentKey', allow_duplicate=True),
        Output('header-breadcrumb', 'items', allow_duplicate=True),
        Output('global-opened-tab-pathname-infos', 'data'),
    ],
    Input('global-url-relay', 'data'),
    [
        State('tabs-container', 'itemKeys'),
        State('menu-collapse-sider', 'collapsed'),
        State('global-url-location', 'trigger'),
    ],
    prevent_initial_call=True,
)
def main_router(href, has_open_tab_keys: List, is_collapsed_menu: bool, trigger):
    # 过滤无效回调
    if href is None:
        raise PreventUpdate
    has_open_tab_keys = has_open_tab_keys or []
    url = URL(href)
    url_menu_item = '.'.join(url.parts[1:])  # 访问路径，第一个为/，去除
    url_query: Dict = url.query  # 查询参数
    url_fragment: str = url.fragment  # 获取锚链接
    param = {
        **url_query,
        **({'url_fragment': url_fragment} if url_fragment else {}),
    }  # 合并查询和锚连接，组成综合参数

    # 当重载页面时，如果访问的不是首页，则先访问首页，再自动访问目标页
    relocation = False
    last_herf = ''
    if trigger == 'load' and url_menu_item != 'dashboard_.workbench':
        relocation = True
        # 强制访问首页
        url_menu_item = 'dashboard_.workbench'
        param = {}
        # 保存目标页的url
        last_herf = str(
            URL()
            .with_path(url.path)
            .with_query({**url_query, 'flush': str(uuid4())[:8]})  # 添加随机码，强制刷新'global-url-location', 'href'，触发目标页面打开
            .with_fragment(url_fragment)
        )
    try:
        # 导入对应的页面模块
        module_page = importlib.import_module(f'dash_view.application.{url_menu_item}')
    except Exception:
        # 没有该页面对应的模块，返回404
        set_props('global-full-screen-container', {'children': page_404.render()})
        return dash.no_update

    def menu_item2url_path(menu_item: str, parent_count=0) -> str:
        if parent_count > 0:
            return '/' + '/'.join(menu_item.split('.')[:-parent_count])
        else:
            return '/' + '/'.join(menu_item.split('.'))

    # 构建key的字符串格式
    key_url_path = menu_item2url_path(url_menu_item)
    key_url_path_parent = menu_item2url_path(url_menu_item, 1)

    # 构建面包屑格式
    from common.utilities.util_menu_access import MenuAccess

    breadcrumb_items = [{'title': t__access('首页'), 'href': '/dashboard_/workbench'}]
    _modules: List = url_menu_item.split('.')
    for i in range(len(_modules)):
        breadcrumb_items = breadcrumb_items + [{'title': t__access(MenuAccess.get_title('.'.join(_modules[: i + 1])))}]

    # 情况1（实际上已经不存在这个情况，上一个回调已经拦截了这种情况，为了鲁棒性，还是保留）： 如已经打开，并且不带强制刷新参数,直接切换页面即可
    if key_url_path in has_open_tab_keys:
        return [
            dash.no_update,  # tab标签页
            key_url_path,  # tab选中key
            dash.no_update if is_collapsed_menu else [key_url_path_parent],  # 菜单展开
            key_url_path,  # 菜单选中
            breadcrumb_items,  # 面包屑
            dash.no_update,
        ]

    # 获取用户权限
    menu_access: MenuAccess = get_menu_access()
    # 没有权限，返回401
    if url_menu_item not in menu_access.menu_items:
        set_props('global-full-screen-container', {'children': page_401.render()})
        return dash.no_update

    ################# 返回页面 #################
    p_items = Patch()
    p_opened_tab_pathname_infos = Patch()
    p_opened_tab_pathname_infos[key_url_path] = [key_url_path_parent, key_url_path, breadcrumb_items]
    # 情况2： 未打开，通过Patch组件，将新的tab添加到tabs组件中
    p_items.append(
        {
            'label': t__access(module_page.title),
            'key': key_url_path,
            'closable': False,
            'children': module_page.render_content(menu_access, **param),
        }
    )
    if relocation:
        # 激活超时组件，马上动态更新到目标页
        set_props('global-url-last-when-load', {'data': last_herf})
        set_props('global-url-timeout-last-when-load', {'delay': 100})
    return [
        p_items,  # tab标签页
        dash.no_update if relocation else key_url_path,  # tab选中key
        dash.no_update if is_collapsed_menu or relocation else [key_url_path_parent],  # 菜单展开
        dash.no_update if relocation else key_url_path,  # 菜单选中
        dash.no_update if relocation else breadcrumb_items,  # 面包屑
        p_opened_tab_pathname_infos,  # 保存目标标题对应的展开key、选中key、面包屑
    ]


# 只显示选中的那个Tab的关闭按钮
app.clientside_callback(
    """
        (activeKey,items) => {
            for (let i = 0; i < items.length; i++) {
                if (items[i].key === '/dashboard_/workbench'){ //除了主页以外
                    items[i].closable = false;
                } else {
                    items[i].closable = items[i].key === activeKey;
                }                
            }
            return items;
        }
    """,
    Output('tabs-container', 'items', allow_duplicate=True),
    Input('tabs-container', 'activeKey'),
    State('tabs-container', 'items'),
    prevent_initial_call=True,
)

# 在初始化非主页时，在访问主页后，自动通过超时组件切换值目标页
app.clientside_callback(
    """
        (timeoutCount,data) => {
            return data;
        }
    """,
    Output('global-dcc-url', 'href'),
    Input('global-url-timeout-last-when-load', 'timeoutCount'),
    State('global-url-last-when-load', 'data'),
    prevent_initial_call=True,
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
app.clientside_callback(
    """
    (tabCloseCounts, items, latestDeletePane, itemKeys,activeKey) => {
        let del_index = itemKeys.findIndex(item => item === latestDeletePane);
        items.splice(del_index, 1);
        itemKeys.splice(del_index, 1);
        if (activeKey==latestDeletePane) {
             if (itemKeys[del_index] !== undefined){
                 return [items, itemKeys[del_index]];
            }else{
                return [items, itemKeys[del_index-1]];
            }
        }else{
            return [items, activeKey];
        }
    }
    """,
    [
        Output('tabs-container', 'items', allow_duplicate=True),
        Output('tabs-container', 'activeKey', allow_duplicate=True),
    ],
    Input('tabs-container', 'tabCloseCounts'),
    [
        State('tabs-container', 'items'),
        State('tabs-container', 'latestDeletePane'),
        State('tabs-container', 'itemKeys'),
        State('tabs-container', 'activeKey'),
    ],
    prevent_initial_call=True,
)

# 页面刷新
app.clientside_callback(
    """
    (nClicks) => {
        return true;
    }
    """,
    Output('global-reload', 'reload', allow_duplicate=True),
    Input('tabs-refresh', 'nClicks'),
    prevent_initial_call=True,
)
