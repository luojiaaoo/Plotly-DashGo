# 本应用的权限工厂，此处手动导入应用模块 - 内置应用，请勿修改
from dash_view.application.access_ import role_mgmt, user_mgmt, group_auth, group_mgmt
from dash_view.application.dashboard_ import workbench, monitor
from dash_view.application.person_ import personal_info, personal_setting

################## 【开始】此处导入您的应用 ###################
from dash_view.application.example_app import subapp1, subapp2

apps = [subapp2, subapp1]

################## 【结束】此处导入您的应用 ###################


def trim_module_path2menu_item(module_path):
    # 传进来的是__name__包路径，去掉前缀才是菜单项
    menu_item_name = module_path.replace('dash_view.application.', '')
    return menu_item_name


class AccessFactory:
    from common.utilities.util_menu_access import MenuAccess

    views = [role_mgmt, user_mgmt, group_auth, group_mgmt, workbench, monitor, personal_info, personal_setting, *apps]

    # 读取每个VIEW中配置的所有权限
    dict_access_meta2module_path = {access_meta: view.__name__ for view in views for access_meta in view.access_metas}
    dict_access_meta2menu_item = {access_meta: trim_module_path2menu_item(module_path) for access_meta, module_path in dict_access_meta2module_path.items()}

    # 基础默认权限，主页和个人中心，每人都有，无需分配
    default_access_meta = (
        '个人信息-页面',
        '个人设置-页面',
        '工作台-页面',
        '监控页-页面',
    )

    # 团队管理员默认权限
    group_access_meta = ('团队授权-页面',)

    # 系统管理员默认权限
    admin_access_meta = ('用户管理-页面', '角色管理-页面', '团队管理-页面')

    # 检查数据库和应用权限
    @classmethod
    def check_access_meta(cls) -> None:
        from common.utilities.util_logger import Log

        logger = Log.get_logger(__name__)

        # 角色类型附加权限检查
        outliers = set(cls.default_access_meta) - set(cls.dict_access_meta2module_path.keys())
        if outliers:
            logger.error(f'角色类型附加权限中存在未定义的权限：{outliers}')
            raise ValueError(f'角色类型附加权限中存在未定义的权限：{outliers}')

        # 每个VIEW的权限唯一性检查
        from collections import Counter

        all_access_metas = []
        for view in cls.views:
            all_access_metas.append(view.access_metas)
        dict_va_cou = Counter(all_access_metas)
        for va, cou in dict_va_cou.items():
            if cou > 1:
                logger.error(f'以下权限多次定义：{va}')
                raise ValueError(f'以下权限多次定义：{va}')

        # 数据库检查
        from database.sql_db.dao import dao_user

        outliers = set(dao_user.get_all_access_meta_for_setup_check()) - set(cls.dict_access_meta2module_path.keys())
        if outliers:
            logger.error(f'数据库中存在未定义的权限：{outliers}')
            raise ValueError(f'数据库中存在未定义的权限：{outliers}')
