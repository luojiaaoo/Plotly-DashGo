# 本应用的权限工厂
from dash_view.application.access_ import access_meta, group_auth, role_auth, user_auth
from dash_view.application.dashboard_ import workbench, monitor
from dash_view.application.person_ import personal_info, personal_setting


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
    dict_access_meta2module_path = {
        access_meta: view.__name__ for view in views for access_meta in view.access_metas
    }

    # 基础默认权限，主页和个人中心
    default_access_meta = (
        '个人信息-页面',
        '个人设置-页面',
        '工作台-页面',
    )
    # 团队管理员的默认权限，权限列表和用户权限
    group_admin_access_meta = (
        '权限列表-页面',
        '用户权限-页面',
    )
    # 超级管理员拥有所有权限
    super_admin_access_meta = dict_access_meta2module_path.keys()

    # 检查数据库和应用权限
    @classmethod
    def check_access_meta(cls) -> None:
        from common.utilities.util_logger import Log

        logger = Log.get_logger(__name__)

        # 角色类型附加权限检查
        outliers = set(
            [*cls.default_access_meta, *cls.group_admin_access_meta, *cls.super_admin_access_meta]
        ) - set(cls.dict_access_meta2module_path.keys())
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
        from database.sql_db.dao.dao_user import get_all_access_meta_for_setup_check

        outliers = get_all_access_meta_for_setup_check() - set(cls.dict_access_meta2module_path.keys())
        if outliers:
            logger.error(f'数据库中存在未定义的权限：{outliers}')
            raise ValueError(f'数据库中存在未定义的权限：{outliers}')
