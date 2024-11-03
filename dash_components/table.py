import feffery_antd_components as fac
from i18n import translator


class Table(fac.AntdTable):
    def __init__(self, *args, **kwargs):
        kwargs['bordered'] = True
        kwargs['locale'] = translator.get_current_locale()
        if kwargs.get('style', None) is not None:
            kwargs['style'] = {**kwargs['style'], 'width': '100%'}
        else:
            kwargs['style'] = {'width': '100%'}
        kwargs['pagination'] = {
            'pageSize': 5,
            'showSizeChanger': True,
            'pageSizeOptions': [5, 10, 20],
            'showQuickJumper': True,
        }
        super().__init__(*args, **kwargs)
