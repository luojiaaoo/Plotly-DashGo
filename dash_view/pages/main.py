import feffery_antd_components as fac
from dash_view.framework.aside import render_aside_content
from dash_view.framework.head import render_head_content


def render_content():
    return fac.AntdRow(
        [
            fac.AntdCol(
                render_aside_content(),
                flex='None',
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
        ],
        className={'width': '100vw', 'height': '100vh'},
    )
