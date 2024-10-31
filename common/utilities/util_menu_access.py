from database.sql_db.dao.dao_user import get_user_menu_item_and_access_meta, get_user_info, UserInfo
from typing import Dict, List, Set
from common.utilities.util_logger import Log
from config.access_factory import AccessFactory
from common.exception import AccessException
import re
from flask_babel import gettext as _  # noqa

logger = Log.get_logger(__name__)


class MenuAccess:
    @classmethod
    def get_dict_menu_item_and_access_meta(cls, user_info: UserInfo) -> Dict[str, List[str]]:
        """获取用户可访问的菜单项权限字典

        根据用户名获取该用户可以访问的所有菜单项和应用权限，并将其整理为字典格式。
        这个方法主要用于权限控制，快速查找用户是否有特定菜单项的访问权限。

        参数:
        user_info (UserInfo): 用户信息，用于查询用户权限。

        返回:
        Dict[str, List[str]]: 一个字典，其中键是菜单项的模块路径，值是对应的权限列表。
        """
        # 比如 menu_item:  dashboard_.workbench:log_info,冒号前为视图的包路径，后面为权限列表
        user_name = user_info.user_name
        user_type = user_info.user_type
        all_menu_item_and_access_meta: Set[str] = get_user_menu_item_and_access_meta(user_name=user_name)
        all_menu_item_and_access_meta.update(AccessFactory.default_menu_item_and_access_meta)
        if user_type == '超级管理员':
            all_menu_item_and_access_meta.update(AccessFactory.super_admin_menu_item_and_access_meta)
        elif user_type == '团队管理员':
            all_menu_item_and_access_meta.update(AccessFactory.group_admin_menu_item_and_access_meta)
        dict_menu_item_and_access_meta = dict()
        for _menu_item_and_access_meta in all_menu_item_and_access_meta:
            module_path, access = _menu_item_and_access_meta.split(':')
            if dict_menu_item_and_access_meta.get(module_path) is None:
                dict_menu_item_and_access_meta[module_path] = [access]
            else:
                dict_menu_item_and_access_meta[module_path].append(access)
        return dict_menu_item_and_access_meta

    @classmethod
    def gen_menu(self, menu_item: Set[str]):
        dict_level1_level2 = dict()
        for per_menu_item in menu_item:
            level1_name, level2_name = per_menu_item.split('.')
            if dict_level1_level2.get(level1_name) is None:
                dict_level1_level2[level1_name] = [level2_name]
            else:
                dict_level1_level2[level1_name].append(level2_name)

        def get_title(module_path):
            from dash_view import application  # noqa

            return eval(f'application.{module_path}.get_title()')

        def get_order(module_path):
            from dash_view import application  # noqa

            try:
                return eval(f'application.{module_path}.order')
            except Exception:
                logger.warning(f'{module_path}没有定义order属性')
                return 999

        def get_icon(module_path):
            from dash_view import application  # noqa

            try:
                return eval(f'application.{module_path}.icon')
            except Exception:
                return None

        # 根据order属性排序
        dict_level1_level2 = dict(sorted(dict_level1_level2.items(), key=lambda x: get_order(f'{x[0]}')))
        for level1, level2 in dict_level1_level2.items():
            level2.sort(key=lambda x: get_order(f'{level1}.{x}'))

        menu = [
            {
                'component': 'SubMenu',
                'props': {
                    'key': f'/{level1_name}',
                    'title': get_title(f'{level1_name}'),
                    'icon': get_icon(f'{level1_name}'),
                },
                'children': [
                    {
                        'component': 'Item',
                        'props': {
                            'key': f'/{level1_name}/{level2_name}',
                            'title': get_title(f'{level1_name}.{level2_name}'),
                            'icon': get_icon(f'{level1_name}.{level2_name}'),
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
        self.user_name = user_name
        self.user_info: UserInfo = get_user_info(user_name)
        # 菜单项 -> 权限元的字典
        self.dict_menu_item_and_access_meta = self.get_dict_menu_item_and_access_meta(self.user_info)
        # 所有菜单项
        self.menu_item = set(list(self.dict_menu_item_and_access_meta.keys()))
        # 生成AntdMenu的菜单格式
        self.menu = self.gen_menu(self.menu_item)

    def get_access_metas(self, module_path: str) -> List[str]:
        """获取用户可访问的权限元"""
        # 传进来的是__name__包路径，去掉前缀才是菜单项
        menu_item_name = module_path.replace('dash_view.application.', '')
        # 回调的路径转换为view的路径
        menu_item_name = menu_item_name.replace('dash_callback.application.', '')
        menu_item_name = re.sub(r'_c$', '', menu_item_name)
        return self.dict_menu_item_and_access_meta.get(menu_item_name)

    @classmethod
    def get_access_meta_from_label(cls, module_path: str, label: str) -> str:
        """获取根据标签获取用户权限元"""
        # 传进来的是__name__包路径，去掉前缀才是菜单项
        menu_item_name = module_path.replace('dash_view.application.', '')
        # 回调的路径转换为view的路径
        menu_item_name = menu_item_name.replace('dash_callback.application.', '')
        menu_item_name = re.sub(r'_c$', '', menu_item_name)
        menu_item_access_meta = AccessFactory.dict_label2menu_item_access_meta.get(label, None)
        if menu_item_access_meta is None:
            e = AccessException(f'{module_path}模块： 权限标签({label})不存在，请检查模块代码，权限标签在数据库表sys_menu_item_access_meta中是否存在')
            logger.warning(e)
            raise e
        else:
            menu_item_, access_meta_ = menu_item_access_meta.split(':')
            if menu_item_name != menu_item_:
                e = AccessException(f'{module_path}模块： 权限标签({label})非本模块的授权，请检查模块代码')
                logger.warning(e)
                raise e
            else:
                return access_meta_

# view入口权限检查器
def enter_access_check(module_path):
    def wrap(func):
        def inner(*args, **kwargs):
            if 'menu_access' in kwargs:
                menu_access = kwargs['menu_access']
            else:
                menu_access = args[0]
            print(menu_access.get_access_metas(module_path))
            try:
                access_metas: List[str] = menu_access.get_access_metas(module_path)
                if 'show' not in access_metas:
                    return _('您没有权限显示该页面')
                rt = func(*args, **kwargs)
            except AccessException as e:
                return _('内部错误：权限异常，请联系开发者')
            else:
                return rt

        return inner

    return wrap


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
