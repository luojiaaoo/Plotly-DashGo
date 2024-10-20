import feffery_antd_components as fac
from dash_view.framework.aside import render_aside_content


def render_content():
    return (
        fac.AntdCol(
            [
                fac.AntdRow(
                    style={
                        'height': '50px',
                        'boxShadow': 'rgb(240 241 242) 0px 2px 14px',
                        'background': 'white',
                        'marginBottom': '10px',
                        'position': 'sticky',
                        'top': 0,
                        'zIndex': 999,
                    },
                ),
                fac.AntdRow(render_aside_content(), wrap=False),
            ],
            flex='auto',
            style={'width': 0},
        ),
    )
