import feffery_antd_components as fac
from dash import html


def render():
    return html.Div(
        [
            html.Div(
                [
                    fac.AntdResult(
                        status='401',
                        title='您没有权限访问该页面',
                        subTitle='如续访问，请联系系统管理员',
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
            'width': '100vh',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
        },
    )
