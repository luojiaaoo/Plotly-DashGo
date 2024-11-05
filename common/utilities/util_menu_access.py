from database.sql_db.dao.dao_user import get_user_access_meta_plus_role, get_user_info, UserInfo
from typing import Dict, List, Set
from common.exception import NotFoundUsername
from common.utilities.util_logger import Log
import re

logger = Log.get_logger(__name__)


class MenuAccess:
    def get_user_all_access_metas(cls, user_info: UserInfo) -> Set[str]:
        from config.access_factory import AccessFactory

        user_name = user_info.user_name
        user_admin_groups: Dict = user_info.user_admin_groups
        all_access_metas: Set[str] = get_user_access_meta_plus_role(user_name=user_name)
        all_access_metas.update(AccessFactory.default_access_meta)
        if len(user_admin_groups) > 0:
            all_access_metas.update(AccessFactory.group_admin_access_meta)
        return all_access_metas

    @classmethod
    def get_user_menu_items(cls, all_access_meta: Set[str]):
        from config.access_factory import AccessFactory

        # 获取所有菜单项
        menu_items = set()
        for access_meta in all_access_meta:
            menu_item = AccessFactory.dict_access_meta2menu_item.get(access_meta)
            menu_items.add(menu_item)
        return menu_items

    @staticmethod
    def get_title(module_path):
        from dash_view import application  # noqa

        return eval(f'application.{module_path}.get_title()')

    @staticmethod
    def get_order(module_path):
        from dash_view import application  # noqa

        try:
            return eval(f'application.{module_path}.order')
        except Exception:
            logger.warning(f'{module_path}没有定义order属性')
            return 999

    @staticmethod
    def get_icon(module_path):
        from dash_view import application  # noqa

        try:
            return eval(f'application.{module_path}.icon')
        except Exception:
            return None

    @classmethod
    def gen_menu(cls, menu_items: Set[str]):
        # 根据菜单项构建菜单层级
        dict_level1_level2 = dict()
        for per_menu_item in menu_items:
            level1_name, level2_name = per_menu_item.split('.')
            if dict_level1_level2.get(level1_name) is None:
                dict_level1_level2[level1_name] = [level2_name]
            else:
                dict_level1_level2[level1_name].append(level2_name)

        # 根据order属性排序
        dict_level1_level2 = dict(sorted(dict_level1_level2.items(), key=lambda x: cls.get_order(f'{x[0]}')))
        for level1, level2 in dict_level1_level2.items():
            level2.sort(key=lambda x: cls.get_order(f'{level1}.{x}'))

        menu = [
            {
                'component': 'SubMenu',
                'props': {
                    'key': f'/{level1_name}',
                    'title': cls.get_title(f'{level1_name}'),
                    'icon': cls.get_icon(f'{level1_name}'),
                },
                'children': [
                    {
                        'component': 'Item',
                        'props': {
                            'key': f'/{level1_name}/{level2_name}',
                            'title': cls.get_title(f'{level1_name}.{level2_name}'),
                            'icon': cls.get_icon(f'{level1_name}.{level2_name}'),
                            'href': f'/{level1_name}/{level2_name}',
                        },
                    }
                    for level2_name in level2_name_list
                ],
            }
            for level1_name, level2_name_list in dict_level1_level2.items()
        ]
        return menu

    def __init__(self, user_name) -> None:
        from config.access_factory import AccessFactory

        # 获取应用全部的权限元和菜单的对应关系
        self.dict_access_meta2menu_item = AccessFactory.dict_access_meta2menu_item
        self.user_name = user_name
        try:
            self.user_info: UserInfo = get_user_info(user_name)[0]
        except IndexError:
            raise NotFoundUsername(f'用户名不存在: {user_name}')
        # 用户所有的权限元
        self.all_access_metas: Set[str] = self.get_user_all_access_metas(user_info=self.user_info)
        # 生成用户的目录路径
        self.menu_items = self.get_user_menu_items(self.all_access_metas)
        # 生成AntdMenu的菜单格式
        self.menu = self.gen_menu(self.menu_items)


def get_menu_access() -> MenuAccess:
    """
    在已登录状态下，获取菜单访问权限。

    本函数通过JWT（JSON Web Token）解码来获取当前用户的访问权限信息，并返回一个包含用户名的MenuAccess对象。
    如果解码无效，强制退出登录；如果过期则可选择性退出登录或者不管。

    参数:
    无

    返回:
    MenuAccess: 包含用户访问权限信息的MenuAccess对象。
    """
    from common.utilities import util_jwt
    from config.dash_melon_conf import LoginConf

    rt_access = util_jwt.jwt_decode_from_session(
        verify_exp=True,
        force_logout_if_exp=LoginConf.JWT_EXPIRED_FORCE_LOGOUT,
        ignore_exp=not LoginConf.JWT_EXPIRED_FORCE_LOGOUT,
        force_logout_if_invalid=True,
    )
    return MenuAccess(user_name=rt_access['user_name'])
