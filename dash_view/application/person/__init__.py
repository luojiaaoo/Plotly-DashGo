import pkgutil

__all__ = []
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    __all__.append(module_name)
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module

# 一级菜单的标题、图标和显示顺序

title = '个人页'
icon = 'antd-user'
order = 9999
