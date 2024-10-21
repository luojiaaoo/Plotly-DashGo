class Menu:
    items = [
        {
            'component': 'Item',
            'props': {
                'title': '数据总览',
                'key': '数据总览',
                'module_name': 'index',
                'icon': 'antd-dashboard',
                'href': '/',
            },
        },
        {
            'component': 'SubMenu',
            'props': {'title': 'app1', 'icon': 'antd-car'},
            'children': [
                {
                    'component': 'Item',
                    'props': {
                        'title': 'Application1',
                        # 用于权限控制
                        'key': 'app1.Application1',
                        # 用于自动模块导入
                        'module_name': 'app1.aa',
                        'icon': 'antd-dashboard',
                        'href': '/app1/aa',
                    },
                },
                {
                    'component': 'Item',
                    'props': {
                        'title': 'Application2',
                        'key': 'app1.Application2',
                        'module_name': 'app1.bb',
                        'icon': 'antd-dashboard',
                        'href': '/app1/bb',
                    },
                },
            ],
        },
    ]

    @staticmethod
    def get_accessible_menu_items(role, access_items):
        return Menu.items
