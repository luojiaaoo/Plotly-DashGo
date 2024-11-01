import feffery_antd_components as fac


class Table(fac.AntdTable):
    def __init__(self, *args, **kwargs):
        kwargs['style'] = {
            'width': '100%',
            'boxShadow': '0px 0px 5px rgba(0,0,0,.12)',
            'padding': '20px',
            'borderRadius': '10px',
        }
        super().__init__(*args, **kwargs)
