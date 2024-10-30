import feffery_antd_components as fac
import feffery_utils_components as fuc
from dash import dcc, html
from server import app
from dash.dependencies import Input, Output
from common.utilities.util_menu_access import MenuAccess

app.clientside_callback(
    """
    (okCounts) => {
        if (okCounts>0) {
            return true;
        }
    }
    """,
    Output('global-reload', 'reload'),
    Input('global-token-err-modal', 'okCounts'),
)


def render_func_content():
    return [
        # 全局强制网页刷新组件
        fuc.FefferyReload(id='global-reload'),
        # 全局url监听组件
        fuc.FefferyLocation(id='global-url-location'),
        # 用于回调更新pathname信息
        dcc.Location(id='global-dcc-url', refresh=False),
        # 全局重定向组件容器
        fac.Fragment(id='global-redirect-container'),
        # 退出登录提示弹窗
        fac.AntdModal(
            html.Div(
                [
                    fac.AntdIcon(icon='fc-high-priority', style={'fontSize': '28px'}),
                    fac.AntdText(
                        '登录状态已过期/无效，请重新登录',
                        style={'marginLeft': '5px'},
                    ),
                ]
            ),
            id='global-token-err-modal',
            visible=False,
            maskClosable=False,
            closable=False,
            title='系统提示',
            okText='重新登录',
            renderFooter=True,
            centered=True,
            cancelButtonProps={'style': {'display': 'none'}},
        ),
        # 当标签页重载时，如访问页面不是首页，保存访问地址
        dcc.Store(id='global-url-last-when-load'),
        # 触发进入目标页面上面Store保存的访问地址的超时组件
        fuc.FefferyTimeout(id='global-url-timeout-last-when-load'),
        # 监听窗口大小
        fuc.FefferyWindowSize(id='global-window-size'),
    ]
