import feffery_utils_components as fuc


class NiceDiv(fuc.FefferyDiv):
    def __init__(self, *args, **kwargs):
        kwargs['style'] = {
            'boxSizing': 'border-box',
            'boxShadow': '0px 0px 5px rgba(0,0,0,.12)',
            'padding': '12px',
            'borderRadius': '10px',
        }
        super().__init__(*args, **kwargs)
