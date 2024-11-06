from functools import partial
from i18n import translator

_ = partial(translator.t)


# 一级菜单的标题、图标和显示顺序
def get_title():
    return _('应用案例')


icon = 'antd-alipay'
order = 1
