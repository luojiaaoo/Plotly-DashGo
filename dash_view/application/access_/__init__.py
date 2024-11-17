from functools import partial
from i18n import translator

_ = partial(translator.t)

# 一级菜单的标题、图标和显示顺序
title = '权限管理'
icon = 'antd-audit'
order = 9998
