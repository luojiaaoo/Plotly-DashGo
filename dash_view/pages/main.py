import feffery_antd_components as fac
from dash_view.framework.aside import render_aside_content
from dash.dependencies import Input, Output, State
from dash_view.framework.head import render_head_content
from dash_view.framework.func import render_func_content
from server import app
from common.utilities.util_menu_access import MenuAccess

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
                        className={'height': '60px', 'box-shadow': '0 1px 4px rgba(0,21,41,.08)'},
                    ),
                    fac.AntdRow(),
                ],
                flex=1,
            ),
            *render_func_content(),
        ],
        className={'width': '100vw', 'height': '100vh'},
    )
