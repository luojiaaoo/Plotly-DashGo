class AccessItems:
    access_items = {
        {
            'name': 'dashboard',
            'module_name': 'dashboard',
            'show_name': '仪表盘',
            'icon': 'antd-dashboard',
            'apps': [
                {
                    'name': 'statistics',
                    'module_name': 'statistics',
                    'show_name': '分析页',
                    'accesses': [
                        '登录排名',
                        '应用使用统计',
                    ],
                },
                {
                    'name': 'workbench',
                    'module_name': 'workbench',
                    'show_name': '工作台',
                    'accesses': [
                        '动态',
                        '定时任务执行',
                    ],
                },
            ],
        },
    }

    @classmethod
    def get_level1_items(cls):
        return [item for item in cls.access_items if item['level'] == 1]
