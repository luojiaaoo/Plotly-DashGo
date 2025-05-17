from typing import Set
from common.exception import NotFoundUserException, AuthException
from common.utilities.util_logger import Log
from i18n import t__access
from cacheout import Cache

cache = Cache()

logger = Log.get_logger(__name__)


@cache.memoize(ttl=5)
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

        def add_to_nested_dict(nested_dict, keys, value):
            """
            递归地将值添加到嵌套字典中。
            :param nested_dict: 当前的嵌套字典
            :param keys: 菜单层级的列表
            :param value: 要添加的权限元数据
            """
            key = keys[0]
            if len(keys) == 1:
                # 最后一层，直接添加权限元数据
                if key not in nested_dict:
                    nested_dict[key] = [value]
                else:
                    nested_dict[key].append(value)
            else:
                # 递归处理下一层
                if key not in nested_dict:
                    nested_dict[key] = {}
                add_to_nested_dict(nested_dict[key], keys[1:], value)

        json_menu_item_access_meta = {}
        for access_meta, menu_item in dict_access_meta2menu_item.items():
            # 此权限无需分配
            if (
                access_meta in (*AccessFactory.default_access_meta, *AccessFactory.admin_access_meta, *AccessFactory.group_access_meta)
                and access_meta not in AccessFactory.assignable_access_meta
            ):
                continue
            # 将菜单项按层级拆分
            menu_hierarchy = menu_item.split('.')
            add_to_nested_dict(json_menu_item_access_meta, menu_hierarchy, access_meta)
        # json_menu_item_access_meta:
        # {'task_': {'task_mgmt': ['任务管理-页面'], 'task_log': ['任务日志-页面']}, 'example_app': {'subapp2': ['应用2-基础权限', '应用2-权限1', '应用2-权限2'], 'subapp1': ['应用1-基础权限', '应用1-权限1', '应用1-权限2']}}

        # 根据 order 属性排序目录
        def sort_nested_dict(nested_dict, parent_key=''):
            """
            递归地对嵌套字典进行排序。
            :param nested_dict: 当前的嵌套字典
            :param parent_key: 父级菜单的键，用于生成完整路径
            """
            if isinstance(nested_dict, dict):
                return dict(
                    sorted(
                        {k: sort_nested_dict(v, f'{parent_key}.{k}' if parent_key else k) for k, v in nested_dict.items()}.items(),
                        key=lambda x: MenuAccess.get_order.__func__(f'{parent_key}.{x[0]}' if parent_key else x[0]),
                    )
                )
            return nested_dict

        json_menu_item_access_meta = sort_nested_dict(json_menu_item_access_meta)

        # 生成 Ant Design Tree 的格式
        def generate_antd_tree(nested_dict, parent_key=''):
            """
            递归地生成 Ant Design Tree 格式的数据。
            :param nested_dict: 当前的嵌套字典
            :param parent_key: 父级菜单的键，用于生成完整路径
            """
            tree = []
            for key, value in nested_dict.items():
                full_key = f'{parent_key}.{key}' if parent_key else key
                if isinstance(value, dict):
                    # 如果是字典，递归生成子节点
                    tree.append(
                        {
                            'title': t__access(MenuAccess.get_title.__func__(full_key)),
                            'key': f'ignore:{MenuAccess.get_title.__func__(full_key)}',
                            'children': generate_antd_tree(value, full_key),
                        }
                    )
                else:
                    # 如果是列表，生成叶子节点
                    tree.append(
                        {
                            'title': t__access(MenuAccess.get_title.__func__(full_key)),
                            'key': f'ignore:{MenuAccess.get_title.__func__(full_key)}',
                            'children': [{'title': t__access(meta), 'key': meta} for meta in value],
                        }
                    )
            return tree

        antd_tree_data = generate_antd_tree(json_menu_item_access_meta)
        return antd_tree_data

    @classmethod
    def get_user_menu_items(cls, all_access_meta: Set[str]):
        from config.access_factory import AccessFactory

        # 获取所有菜单项
        menu_items = set()
        for access_meta in all_access_meta:
            menu_item = AccessFactory.get_dict_access_meta2menu_item().get(access_meta)
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
        def add_to_nested_dict(nested_dict, keys):
            """
            递归地将菜单项添加到嵌套字典中。
            :param nested_dict: 当前的嵌套字典
            :param keys: 菜单层级的列表
            """
            key = keys[0]
            if len(keys) == 1:
                # 最后一层，标记为叶子节点
                if key not in nested_dict:
                    nested_dict[key] = {}
            else:
                # 递归处理下一层
                if key not in nested_dict:
                    nested_dict[key] = {}
                add_to_nested_dict(nested_dict[key], keys[1:])

        nested_menu = {}
        for per_menu_item in menu_items:
            menu_hierarchy = per_menu_item.split('.')
            add_to_nested_dict(nested_menu, menu_hierarchy)
        # nested_menu:
        # {'dashboard_': {'workbench': {}, 'monitor': {}}, 'setting_': {'notify_api': {}, 'listen_api': {}}, 'example_app': {'subapp2': {}, 'subapp1': {}}, 'task_': {'task_mgmt': {}, 'task_log': {}}, 'access_': {'role_mgmt': {}, 'group_mgmt': {}, 'user_mgmt': {}}, 'person_': {'personal_info': {}}, 'message_': {'announcement': {}}}

        # 根据 order 属性排序嵌套字典
        def sort_nested_dict(nested_dict, parent_key=''):
            """
            递归地对嵌套字典进行排序。
            :param nested_dict: 当前的嵌套字典
            :param parent_key: 父级菜单的键，用于生成完整路径
            """
            return dict(
                sorted(
                    {k: sort_nested_dict(v, f'{parent_key}.{k}' if parent_key else k) for k, v in nested_dict.items()}.items(),
                    key=lambda x: cls.get_order(f'{parent_key}.{x[0]}' if parent_key else x[0]),
                )
            )

        sorted_menu = sort_nested_dict(nested_menu)
        # sorted_menu:
        # {'dashboard_': {'workbench': {}, 'monitor': {}}, 'example_app': {'subapp2': {}, 'subapp1': {}}, 'message_': {'announcement': {}}, 'access_': {'role_mgmt': {}, 'user_mgmt': {}, 'group_mgmt': {}}, 'task_': {'task_mgmt': {}, 'task_log': {}}, 'person_': {'personal_info': {}}, 'setting_': {'notify_api': {}, 'listen_api': {}}}

        # 生成菜单结构
        def generate_menu_structure(nested_dict, parent_path=''):
            """
            递归地生成菜单结构。
            :param nested_dict: 当前的嵌套字典
            :param parent_path: 父级路径，用于生成完整路径
            """
            menu = []
            for key, value in nested_dict.items():
                full_path = f'{parent_path}/{key}'
                package_path = full_path.strip('/').replace('/', '.')
                menu_item = {
                    'component': 'SubMenu' if value else 'Item',
                    'props': {
                        'key': full_path,
                        'title': t__access(cls.get_title(package_path)),
                        'icon': cls.get_icon(package_path),
                    },
                }
                if value:  # 如果有子菜单，递归生成子菜单
                    menu_item['children'] = generate_menu_structure(value, full_path)
                else:  # 如果是叶子节点，添加 href 属性
                    menu_item['props']['href'] = full_path
                menu.append(menu_item)
            return menu

        return generate_menu_structure(sorted_menu)

    def has_access(self, access_meta) -> bool:
        return access_meta in self.all_access_metas

    @property
    def dict_access_meta2menu_item(self):
        from config.access_factory import AccessFactory

        return AccessFactory.get_dict_access_meta2menu_item()

    def __init__(self, user_name) -> None:
        from database.sql_db.dao import dao_user

        # 获取应用全部的权限元和菜单的对应关系
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
    from config.dashgo_conf import LoginConf
    from common.utilities.util_authorization import auth_validate

    rt_access = auth_validate(
        verify_exp=LoginConf.JWT_EXPIRED_FORCE_LOGOUT,  # 查看权限的时候是否检测过期
    )
    if rt_access == util_jwt.AccessFailType.EXPIRED:
        raise AuthException(message='您的授权令牌已过期，请重新登录')
    elif rt_access == util_jwt.AccessFailType.NO_ACCESS:
        raise AuthException(message='没有找到您的授权令牌，请重新登录')
    elif rt_access == util_jwt.AccessFailType.INVALID:
        raise AuthException(message='您的授权令牌无效，请重新登录')
    if only_get_user_name:
        return rt_access['user_name']
    else:
        return MenuAccess(user_name=rt_access['user_name'])
