from flask_babel import gettext as _  # noqa


# 一级菜单的标题、图标和显示顺序
def get_title():
    return _('仪表盘')


icon = 'antd-dashboard'
order = 0
