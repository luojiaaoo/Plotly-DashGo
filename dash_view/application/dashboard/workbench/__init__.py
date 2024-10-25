from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac

# 二级菜单的标题和图标
title = '工作台'
icon = None


def render_content(menu_access: MenuAccess, **kwargs):
    print(kwargs)
    # 获取权限元，根据权限元，用户自定义渲染UI
    access_metas: List[str] = menu_access.get_access_metas(__name__)
    return str(kwargs)
