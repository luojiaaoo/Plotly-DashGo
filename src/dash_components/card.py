import feffery_antd_components as fac
from dash import html


class Card(fac.AntdCard):
    def __init__(self, *args, **kwargs):
        kwargs['style'] = {
            **(kwargs['style'] if kwargs.get('style', None) is not None else {}),
            **{
                'boxShadow': 'rgba(99, 99, 99, 0.2) 0px 2px 8px 0px',
                'boxSizing': 'border-box',
            },
        }
        kwargs['size'] = 'small'
        if kwargs.get('title', None) is not None:
            kwargs['title'] = html.Div(
                [
                    *([fac.AntdIcon(icon=kwargs['icon'])] if kwargs.get('icon', None) is not None else []),
                    fac.AntdText(kwargs['title'], style={'marginLeft': '10px'}),
                ]
            )
        else:
            kwargs['headStyle'] = {
                **(kwargs['headStyle'] if kwargs.get('headStyle', None) is not None else {}),
                **{'display': 'none'},
            }
        super().__init__(*args, **kwargs)
