from flask_babel import gettext as _  # noqa


# 一级菜单的标题、图标和显示顺序
def get_title():
    return _('权限管理')


icon = 'antd-audit'
order = 9998
