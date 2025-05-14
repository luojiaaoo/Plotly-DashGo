import feffery_antd_components as fac
from dash import html
from common.constant import HttpStatusConstant


def render_content():
    return html.Div(
        [
            html.Div(
                [
                    fac.AntdResult(
                        status=str(HttpStatusConstant.NOT_FOUND),
                        title='页面不存在',
                        subTitle='检查您的网址输入是否正确',
                        style={'paddingBottom': 0, 'paddingTop': 0},
                    ),
                    fac.AntdButton('回到首页', type='link', href='/', target='_self'),
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
