from database.sql_db.dao.user import get_all_menu_item_and_app_meta
from typing import Dict, List, Set, Union


class MenuAccess:
    @classmethod
    def get_dict_menu_item_and_app_meta(cls, user_name: str) -> Dict[str, str]:
        """获取用户可访问的菜单项权限字典

        根据用户名获取该用户可以访问的所有菜单项和应用权限，并将其整理为字典格式。
        这个方法主要用于权限控制，快速查找用户是否有特定菜单项的访问权限。

        参数:
        user_name (str): 用户名，用于查询用户权限。

        返回:
        Dict[str, str]: 一个字典，其中键是菜单项的模块路径，值是对应的权限列表。
        """
        # 比如 menu_item:  dashboard.workbench:log_info,冒号前为视图的包路径，后面为权限列表
        all_menu_item_and_app_meta: Set[str] = get_all_menu_item_and_app_meta(user_name=user_name)
        dict_menu_item_and_app_meta = dict()
        for _menu_item_and_app_meta in all_menu_item_and_app_meta:
            module_path, access = _menu_item_and_app_meta.split(':')
            dict_menu_item_and_app_meta[module_path] = access
        return dict_menu_item_and_app_meta

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

            return eval(f'{module_path}.title')

        def get_icon(module_path):
            from dash_view import application  # noqa

            return eval(f'{module_path}.icon')

        menu = [
            {
                'component': 'SubMenu',
                'props': {
                    'key': f'{level1_name}',
                    'title': get_title(f'application.{level1_name}'),
                    'icon': get_icon(f'application.{level1_name}'),
                },
                'children': [
                    {
                        'component': 'Item',
                        'props': {
                            'key': f'{level2_name}.{level2_name}',
                            'title': get_title(f'application.{level1_name}.{level2_name}'),
                        },
                    }
                    for level2_name in level2_name_list
                ],
            }
            for level1_name, level2_name_list in dict_level1_level2.items()
        ]
        return menu

    def __init__(self, user_name) -> None:
        self.dict_menu_item_and_app_meta = self.get_dict_menu_item_and_app_meta(user_name)
        self.menu_item = set(list(self.dict_menu_item_and_app_meta.keys()))
        self.menu = self.gen_menu(self.menu_item)
