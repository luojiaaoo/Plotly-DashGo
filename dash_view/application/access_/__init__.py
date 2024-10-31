import pkgutil
from flask_babel import gettext as _  # noqa

__all__ = []
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    __all__.append(module_name)
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module

# 一级菜单的标题、图标和显示顺序
def get_title():
    return _('权限管理')


icon = 'antd-audit'
order = 9998
