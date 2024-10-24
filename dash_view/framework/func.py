import feffery_antd_components as fac
import feffery_utils_components as fuc
from dash import dcc,html


def render_func_content():
    return [
        # 全局强制网页刷新组件
        fuc.FefferyReload(id='global-reload'),
        # 全局url监听组件
        fuc.FefferyLocation(id='global-url-location'),
        fac.AntdModal(
            html.Div(
                [
                    fac.AntdIcon(
                        icon='fc-high-priority', style={'font-size': '28px'}
                    ),
                    fac.AntdText(
                        '登录状态已过期，您可以继续留在该页面，或者重新登录',
                        style={'margin-left': '5px'},
                    ),
                ]
            ),
            id='token-err-modal',
            visible=True,
            title='系统提示',
            okText='重新登录',
            renderFooter=True,
            centered=True,
        ),
    ]
