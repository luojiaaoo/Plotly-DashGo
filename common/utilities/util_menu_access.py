from typing import Set
from common.exception import NotFoundUserException, AuthException
from common.utilities.util_logger import Log
from i18n import translator
from functools import partial


__ = partial(translator.t)


logger = Log.get_logger(__name__)


class MenuAccess:
    def get_user_all_access_metas(cls, user_info) -> Set[str]:
        from database.sql_db.dao import dao_user
        from config.access_factory import AccessFactory

        user_info: dao_user.UserInfo = user_info
        user_name = user_info.user_name
        all_access_metas: Set[str] = dao_user.get_user_access_meta(user_name=user_name, exclude_disabled=True)
        # 所有用户添加默认权限
        all_access_metas.update(AccessFactory.default_access_meta)
        # admin角色添加默认权限
        if 'admin' in user_info.user_roles:
            all_access_metas.update(AccessFactory.admin_access_meta)
        # 团队管理员添加默认权限
        if dao_user.is_group_admin(user_name):
            all_access_metas.update(AccessFactory.group_access_meta)
        return all_access_metas

    @staticmethod
    def gen_antd_tree_data_menu_item_access_meta(dict_access_meta2menu_item):
        from common.utilities.util_menu_access import MenuAccess
        from config.access_factory import AccessFactory

        json_menu_item_access_meta = {}
        for access_meta, menu_item in dict_access_meta2menu_item.items():
            # 此权限无需分配
            if access_meta in (*AccessFactory.default_access_meta, *AccessFactory.admin_access_meta, *AccessFactory.group_access_meta):
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
            json_menu_item_access_meta[level1_name] = dict(sorted(dict_level2_access_metas.items(), key=lambda x: MenuAccess.get_order(f'{level1_name}.{x[0]}')))

        # 生成antd_tree的格式
        antd_tree_data = []
        for level1_name, dict_level2_access_metas in json_menu_item_access_meta.items():
            format_level2 = []
            for level2_name, access_metas in dict_level2_access_metas.items():
                format_level2.append(
                    {
                        'title': MenuAccess.get_title(f'{level1_name}.{level2_name}'),
                        'key': 'ignore:' + MenuAccess.get_title(f'{level1_name}.{level2_name}'),
                        'children': [{'title': __(access_meta), 'key': access_meta} for access_meta in access_metas],
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

        return eval(f'application.{module_path}.title')

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

    def has_access(self, access_meta) -> bool:
        return access_meta in self.all_access_metas

    def __init__(self, user_name) -> None:
        from config.access_factory import AccessFactory
        from database.sql_db.dao import dao_user

        # 获取应用全部的权限元和菜单的对应关系
        self.dict_access_meta2menu_item = AccessFactory.dict_access_meta2menu_item
        self.user_name = user_name
        try:
            self.user_info: dao_user.UserInfo = dao_user.get_user_info([user_name], exclude_disabled=True, exclude_role_admin=False)[0]
        except IndexError:
            raise NotFoundUserException(message=f'用户{user_name}尝试登录，但该用户不存在，可能已被删除')
        # 用户所有的权限元
        self.all_access_metas: Set[str] = self.get_user_all_access_metas(user_info=self.user_info)
        # 生成用户的目录路径
        self.menu_items = self.get_user_menu_items(self.all_access_metas)
        # 生成AntdMenu的菜单格式
        self.menu = self.gen_menu(self.menu_items)


def get_menu_access(only_get_user_name=False) -> MenuAccess:
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
        verify_exp=LoginConf.JWT_EXPIRED_FORCE_LOGOUT,
    )
    if rt_access == util_jwt.AccessFailType.NO_ACCESS:
        raise AuthException(message='没有找到您的授权令牌，请重新登录')
    elif rt_access == util_jwt.AccessFailType.EXPIRED:
        raise AuthException(message='您的授权令牌已过期，请重新登录')
    elif rt_access == util_jwt.AccessFailType.INVALID:
        raise AuthException(message='您的授权令牌无效，请重新登录')
    if only_get_user_name:
        return rt_access['user_name']
    else:
        return MenuAccess(user_name=rt_access['user_name'])
