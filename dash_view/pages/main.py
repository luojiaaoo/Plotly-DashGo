import feffery_antd_components as fac
from dash_view.framework.aside import render_aside_content
from dash.dependencies import Input, Output, State
from dash_view.framework.head import render_head_content
from dash_view.framework.func import render_func_content
from server import app
from common.utilities.util_menu_access import MenuAccess
from dash import html
import importlib
import feffery_utils_components as fuc
from config.dash_melon_conf import LoginConf

module_first_page = importlib.import_module(f'dash_view.application.{LoginConf.FIRST_SHOW_PAGE}')

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
            *render_func_content(),
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
            fac.AntdCol(
                [
                    fac.AntdRow(
                        render_head_content(),
                        align='middle',
                        className={'height': '50px', 'box-shadow': '0 1px 4px rgba(0,21,41,.08)'},
                    ),
                    fac.AntdRow(
                        fuc.FefferyDiv(
                            fac.AntdTabs(
                                items=[
                                    {
                                        'label': '工作台',
                                        'key': LoginConf.FIRST_SHOW_PAGE,
                                        'closable': True,
                                        'children': module_first_page.render_content(menu_access),
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
                                ],
                                id='tabs-container',
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
                                    'border-radius':'2px'
                                },
                            },
                        )
                    ),
                ],
                flex='auto',
            ),
        ],
        className={'width': '100vw', 'height': '100vh'},
    )
