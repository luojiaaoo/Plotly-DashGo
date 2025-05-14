import feffery_antd_components as fac
from dash import html
from common.constant import HttpStatusConstant


def render_content():
    return html.Div(
        [
            html.Div(
                [
                    fac.AntdResult(
                        status=str(HttpStatusConstant.FORBIDDEN),
                        title='您没有权限访问该页面',
                        subTitle='如需访问，请联系系统管理员',
                        style={'paddingBottom': 0, 'paddingTop': 0},
                    ),
                    fac.AntdButton(
                        '回到首页', type='link', href='/', target='_self'
                    ),
                ],
                style={'textAlign': 'center'},
            )
        ],
        style={
            'height': '100vh',
            'width': '100vw',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
        },
    )
