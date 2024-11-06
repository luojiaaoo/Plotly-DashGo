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
        kwargs['size'] = 'small'
        kwargs['pagination'] = {
            'pageSize': 10 if kwargs.get('pageSize', None) is None else kwargs['pageSize'],
            'showSizeChanger': True,
            'pageSizeOptions': [10, 20, 30, 40, 50, 100],
            'showQuickJumper': True,
            'position': 'bottomLeft',
        }
        if kwargs.get('pageSize', None) is not None:
            kwargs.pop('pageSize') 
        super().__init__(*args, **kwargs)
