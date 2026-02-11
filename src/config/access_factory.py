# 本应用的权限工厂，此处手动导入应用模块 - 内置应用，请勿修改
from dash_view.application.sys_access import role_mgmt, user_mgmt
from dash_view.application.sys_dashboard import workbench
from dash_view.application.sys_person import personal_info
from dash_view.application.sys_message import announcement

################## 【开始】此处导入您的应用 ###################
from dash_view.application.example_app import subapp1, subapp2

apps = [subapp2, subapp1]

################## 【结束】此处导入您的应用 ###################


class AccessFactory:
    from common.utilities.util_menu_access import MenuAccess
    from cacheout import Cache

    cache_dict_access_meta2menu_item = Cache()

    views = [
        role_mgmt,
        user_mgmt,
        workbench,
        personal_info,
        announcement,
        *apps,
    ]

    # 读取每个VIEW中配置的所有权限，生成权限与模块路径的映射，缓存10秒
    @classmethod
    @cache_dict_access_meta2menu_item.memoize(ttl=10, typed=True)
    def get_dict_access_meta2menu_item(cls):
        dict_access_meta2module_path = {
            access_meta: view.__name__
            for view in cls.views
            for access_meta in (
                view.access_metas()
                if callable(view.access_metas)
                else view.access_metas
            )
        }
        return {
            access_meta: module_path.replace("dash_view.application.", "")
            for access_meta, module_path in dict_access_meta2module_path.items()
        }

    # 基础默认权限，主页和个人中心，每人都有，无需分配
    default_access_meta = [
        "个人信息-页面",
        "工作台-页面",
    ]

    # 团队管理员默认权限
    group_access_meta = ["团队授权-页面",]

    # 系统管理员默认权限
    admin_access_meta = [
        "用户管理-页面",
        "角色管理-页面",
        "公告管理-页面",
    ]

    # 内置可以分配的权限
    assignable_access_meta = []
