import feffery_utils_components as fuc


class NiceDiv(fuc.FefferyDiv):
    def __init__(self, *args, **kwargs):
        kwargs['style'] = {
            'boxSizing': 'border-box',
            'boxShadow': 'rgba(0, 0, 0, 0.1) 0px 4px 12px',
            'padding': '12px',
            'margin-bottom': '24px',
        }
        super().__init__(*args, **kwargs)
