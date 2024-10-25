from common.utilities.util_menu_access import MenuAccess
from typing import List

# 一级菜单的标题
title = '工作台'


def render_content(menu_access: MenuAccess):
    # 获取权限元，根据权限元，用户自定义渲染UI
    access_metas: List[str] = menu_access.get_access_metas(__name__)
