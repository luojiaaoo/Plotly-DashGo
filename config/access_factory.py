# 本应用的权限工厂
from dash_view.application.access_ import access_meta, group_auth, role_auth, user_auth
from dash_view.application.dashboard_ import workbench, monitor
from dash_view.application.person_ import personal_info, personal_setting
from common.utilities.util_menu_access import trim_module_path2menu_item


class AccessFactory:
    views = [
        access_meta,
        group_auth,
        role_auth,
        user_auth,
        workbench,
        monitor,
        personal_info,
        personal_setting,
    ]
    # 读取每个VIEW中配置的所有权限

    dict_label2menu_item_access_meta = {
        label: f'{trim_module_path2menu_item(view.__name__)}:{access_meta_name}'
        for view in views
        for label, access_meta_name in view.access_metas.items()
    }

    # 基础默认权限，主页和个人中心
    default_menu_item_and_access_meta = (
        dict_label2menu_item_access_meta['个人信息-页面'],
        dict_label2menu_item_access_meta['个人设置-页面'],
        dict_label2menu_item_access_meta['工作台-页面'],
    )
    # 团队管理员的默认权限，权限列表和用户权限
    group_admin_menu_item_and_access_meta = (
        dict_label2menu_item_access_meta['权限列表-页面'],
        dict_label2menu_item_access_meta['用户权限-页面'],
    )
    # 超级管理员拥有所有权限
    super_admin_menu_item_and_access_meta = dict_label2menu_item_access_meta.values()

    # 检查数据库和应用权限
