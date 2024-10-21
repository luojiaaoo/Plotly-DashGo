import feffery_antd_components as fac
from dash_view.framework.aside import render_aside_content


def render_content():
    return fac.AntdRow(
        [
            fac.AntdCol(
                render_aside_content(),
                flex='None',
            ),
            fac.AntdCol(flex=1),
        ],
        className={'width': '100vw', 'height': '100vh'},
    )
