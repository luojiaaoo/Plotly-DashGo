# 本应用的权限工厂，此处手动导入应用模块
from dash_view.application.access_ import group_mgmt, role_mgmt, user_auth, group_auth
from dash_view.application.dashboard_ import workbench, monitor
from dash_view.application.person_ import personal_info, personal_setting


def trim_module_path2menu_item(module_path):
    # 传进来的是__name__包路径，去掉前缀才是菜单项
    menu_item_name = module_path.replace('dash_view.application.', '')
    return menu_item_name


class AccessFactory:
    views = [
        group_mgmt,
        role_mgmt,
        user_auth,
        group_auth,
        workbench,
        monitor,
        personal_info,
        personal_setting,
    ]

    @classmethod
    def gen_antd_tree_data_menu_item_access_meta(cls, dict_access_meta2menu_item):
        from i18n import translator
        from functools import partial

        _ = partial(translator.t)
        from common.utilities.util_menu_access import MenuAccess

        json_menu_item_access_meta = {}
        for access_meta, menu_item in dict_access_meta2menu_item.items():
            # 此权限无需分配
            if access_meta in (cls.default_access_meta) or access_meta in (cls.group_admin_access_meta):
                continue
            level1_name, level2_name = menu_item.split('.')
            if json_menu_item_access_meta.get(level1_name, None) is None:
                json_menu_item_access_meta[level1_name] = {level2_name: [access_meta]}
            else:
                if json_menu_item_access_meta[level1_name].get(level2_name, None) is None:
                    json_menu_item_access_meta[level1_name][level2_name] = [access_meta]
                else:
                    json_menu_item_access_meta[level1_name][level2_name].append(access_meta)

        # 根据order属性排序目录
        json_menu_item_access_meta = dict(sorted(json_menu_item_access_meta.items(), key=lambda x: MenuAccess.get_order(f'{x[0]}')))
        for level1_name, dict_level2_access_metas in json_menu_item_access_meta.items():
            json_menu_item_access_meta[level1_name] = dict(
                sorted(dict_level2_access_metas.items(), key=lambda x: MenuAccess.get_order(f'{level1_name}.{x[0]}'))
            )

        # 生成antd_tree的格式
        antd_tree_data = []
        for level1_name, dict_level2_access_metas in json_menu_item_access_meta.items():
            format_level2 = []
            for level2_name, access_metas in dict_level2_access_metas.items():
                format_level2.append(
                    {
                        'title': MenuAccess.get_title(f'{level1_name}.{level2_name}'),
                        'key': 'ignore:' + MenuAccess.get_title(f'{level1_name}.{level2_name}'),
                        'children': [{'title': _(access_meta), 'key': access_meta} for access_meta in access_metas],
                    },
                )
            antd_tree_data.append(
                {
                    'title': MenuAccess.get_title(f'{level1_name}'),
                    'key': 'ignore:' + MenuAccess.get_title(f'{level1_name}'),
                    'children': format_level2,
                }
            )
        return antd_tree_data

    # 读取每个VIEW中配置的所有权限
    dict_access_meta2module_path = {access_meta: view.__name__ for view in views for access_meta in view.access_metas}
    dict_access_meta2menu_item = {
        access_meta: trim_module_path2menu_item(module_path) for access_meta, module_path in dict_access_meta2module_path.items()
    }

    @classmethod
    def get_antd_tree_data_menu_item_access_meta(cls):
        return cls.gen_antd_tree_data_menu_item_access_meta(cls.dict_access_meta2menu_item)

    # 基础默认权限，主页和个人中心，每人都有，无需分配
    default_access_meta = (
        '个人信息-页面',
        '个人设置-页面',
        '工作台-页面',
        '监控页-页面',
    )
    # 团队管理员的默认权限，无需分配
    group_admin_access_meta = ('团队权限-页面',)

    # 检查数据库和应用权限
    @classmethod
    def check_access_meta(cls) -> None:
        from common.utilities.util_logger import Log

        logger = Log.get_logger(__name__)

        # 角色类型附加权限检查
        outliers = set([*cls.default_access_meta, *cls.group_admin_access_meta]) - set(cls.dict_access_meta2module_path.keys())
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
