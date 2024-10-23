from enum import Enum


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
                },
                {
                    'name': 'workbench',
                    'module_name': 'workbench',
                    'show_name': '工作台',
                },
            ],
        },
    }

    # 权限配置枚举，供view和callback注入拦截
    class Dashboard_Statistics_Accesses(Enum):
        STATISTISC_FUNC1 = 'STATISTISC_FUNC1'
        STATISTISC_FUNC2 = 'STATISTISC_FUNC2'

    class Dashboard_Workbench_Accesses(Enum):
        WORKBENCH_FUNC1 = 'WORKBENCH_FUNC1'
        WORKBENCH_FUNC2 = 'WORKBENCH_FUNC2'

    @classmethod
    def get_level1_items(cls):
        return [item for item in cls.access_items if item['level'] == 1]
