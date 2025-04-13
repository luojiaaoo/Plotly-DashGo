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
    Input('main-window-size', '_width'),
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
                    return [window.dash_clientside.no_update, window.dash_clientside.no_update, opened_tab_pathname_infos[pathname][1], opened_tab_pathname_infos[pathname][2],pathname,opened_tab_pathname_infos[pathname][3]];
                }else{
                    return [window.dash_clientside.no_update, [opened_tab_pathname_infos[pathname][0]], opened_tab_pathname_infos[pathname][1], opened_tab_pathname_infos[pathname][2],pathname,opened_tab_pathname_infos[pathname][3]];
                }
            }else{
                return [href, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
            }
        }
    """,
    [
        Output('main-url-relay', 'data', allow_duplicate=True),
        Output('main-menu', 'openKeys', allow_duplicate=True),
        Output('main-menu', 'currentKey', allow_duplicate=True),
        Output('main-header-breadcrumb', 'items', allow_duplicate=True),
        Output('tabs-container', 'activeKey', allow_duplicate=True),
        Output('main-dcc-url', 'search', allow_duplicate=True),
    ],
    Input('main-url-location', 'href'),
    [
        State('tabs-container', 'activeKey'),
        State('tabs-container', 'itemKeys'),
        State('main-opened-tab-pathname-infos', 'data'),
        State('menu-collapse-sider', 'collapsed'),
    ],
    prevent_initial_call=True,
)


# 主路由函数：地址URL中继store -》 Tab新增+Tab切换+菜单展开+菜单选中+面包屑
@app.callback(
    [
        Output('tabs-container', 'items', allow_duplicate=True),
        Output('tabs-container', 'activeKey', allow_duplicate=True),
        Output('main-menu', 'openKeys', allow_duplicate=True),
        Output('main-menu', 'currentKey', allow_duplicate=True),
        Output('main-header-breadcrumb', 'items', allow_duplicate=True),
        Output('main-opened-tab-pathname-infos', 'data'),
    ],
    Input('main-url-relay', 'data'),
    [
        State('tabs-container', 'itemKeys'),
        State('menu-collapse-sider', 'collapsed'),
        State('main-url-location', 'trigger'),
    ],
    prevent_initial_call=True,
)
def main_router(href, has_open_tab_keys: List, is_collapsed_menu: bool, trigger):
    # 过滤无效回调
    if href is None:
        raise PreventUpdate
    has_open_tab_keys = has_open_tab_keys or []
    url = URL(href)
    url_pathname = url.path
    url_menu_item = '.'.join(url.parts[1:])  # 访问路径，第一个为/，去除
    url_query: Dict = dict(url.query)  # 查询参数
    url_fragment: str = url.fragment  # 获取锚链接
    if 'flash' in url_query:  # 排除强制刷新flash参数
        url_query.pop('flash')
    param = {
        **url_query,
        **({'url_fragment': url_fragment} if url_fragment else {}),
    }  # 合并查询和锚连接，组成综合参数

    # 当重载页面时，如果访问的不是首页，则先访问首页，再自动访问目标页
    relocation = False
    _last_pathname = ''
    _last_search = {}
    _last_hash = ''
    if trigger == 'load' and url_menu_item != 'dashboard_.workbench':
        relocation = True
        # 保存目标页的url
        _last_pathname = url_pathname
        _last_search = url_query
        _last_hash = url_fragment
        # 强制访问首页，不带参数
        url_menu_item = 'dashboard_.workbench'
        url_pathname = '/dashboard_/workbench'
        url_query = {}
        url_fragment = ''
        param = {}
    try:
        # 导入对应的页面模块
        module_page = importlib.import_module(f'dash_view.application.{url_menu_item}')
    except Exception:
        # 没有该页面对应的模块，返回404
        set_props('root-container', {'children': page_404.render()})
        return dash.no_update

    def menu_item2url_path(menu_item: str, parent_count=0) -> str:
        if parent_count > 0:
            return '/' + '/'.join(menu_item.split('.')[:-parent_count])
        else:
            return '/' + '/'.join(menu_item.split('.'))

    # 构建key的字符串格式
    key_url_path = menu_item2url_path(url_menu_item)  # 其实应该和url_pathname的值相同
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
        set_props('root-container', {'children': page_401.render()})
        return dash.no_update

    ################# 返回页面 #################
    p_items = Patch()
    p_opened_tab_pathname_infos = Patch()
    p_opened_tab_pathname_infos[key_url_path] = [key_url_path_parent, key_url_path, breadcrumb_items, URL.build(query=url_query).__str__()]
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
        set_props('main-url-pathname-last-when-load', {'data': _last_pathname})
        set_props('main-url-search-last-when-load', {'data': _last_search})
        set_props('main-url-hash-last-when-load', {'data': _last_hash})
        set_props('main-url-timeout-last-when-load', {'delay': 100})
    return [
        p_items,  # tab标签页
        dash.no_update if relocation else key_url_path,  # tab选中key
        dash.no_update if is_collapsed_menu or relocation else [key_url_path_parent],  # 菜单展开
        dash.no_update if relocation else key_url_path,  # 菜单选中
        dash.no_update if relocation else breadcrumb_items,  # 面包屑
        p_opened_tab_pathname_infos,  # 保存目标标题对应的展开key、选中key、面包屑、get参数
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
@app.callback(
    [
        Output('main-dcc-url', 'pathname', allow_duplicate=True),
        Output('main-dcc-url', 'search', allow_duplicate=True),
        Output('main-dcc-url', 'hash', allow_duplicate=True),
    ],
    Input('main-url-timeout-last-when-load', 'timeoutCount'),
    [
        State('main-url-pathname-last-when-load', 'data'),
        State('main-url-search-last-when-load', 'data'),
        State('main-url-hash-last-when-load', 'data'),
    ],
    prevent_initial_call=True,
)
def jump_to_init_page(timeoutCount, pathname, search, hash):
    from yarl import URL

    url = URL(pathname).with_query({**search, **{'flash': uuid4().hex[:8]}}).with_fragment(hash)
    return url.path, URL.build(query=url.query).__str__(), URL.build(fragment=url.fragment).__str__()


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
    Output('main-dcc-url', 'pathname'),
    Input('tabs-container', 'activeKey'),
    prevent_initial_call=True,
)

# Tab关闭
app.clientside_callback(
    """
    (tabCloseCounts, items, latestDeletePane, itemKeys,activeKey,pathname_info) => {
        //const { latestDeletePane, ...new_pathname_info } = pathname_info;
        //Reflect.deleteProperty(pathname_info, latestDeletePane);
        delete pathname_info[latestDeletePane];
        let del_index = itemKeys.findIndex(item => item === latestDeletePane);
        items.splice(del_index, 1);
        itemKeys.splice(del_index, 1);
        if (activeKey==latestDeletePane) {
             if (itemKeys[del_index] !== undefined){
                 return [items, itemKeys[del_index], pathname_info];
            }else{
                return [items, itemKeys[del_index-1], pathname_info];
            }
        }else{
            return [items, activeKey, pathname_info];
        }
    }
    """,
    [
        Output('tabs-container', 'items', allow_duplicate=True),
        Output('tabs-container', 'activeKey', allow_duplicate=True),
        Output('main-opened-tab-pathname-infos', 'data', allow_duplicate=True),
    ],
    Input('tabs-container', 'tabCloseCounts'),
    [
        State('tabs-container', 'items'),
        State('tabs-container', 'latestDeletePane'),
        State('tabs-container', 'itemKeys'),
        State('tabs-container', 'activeKey'),
        State('main-opened-tab-pathname-infos', 'data'),
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
    Output('main-reload', 'reload', allow_duplicate=True),
    Input('tabs-refresh', 'nClicks'),
    prevent_initial_call=True,
)
