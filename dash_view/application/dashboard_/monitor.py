from common.utilities.util_menu_access import MenuAccess
import feffery_utils_components as fuc
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash import html, dcc
from flask_babel import gettext as _  # noqa
from dash_components import Card
import dash_callback.application.dashboard_.monitor_c  # noqa


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('监控页')


icon = None
order = 2
logger = Log.get_logger(__name__)

access_metas = ('监控页-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return html.Div(
        [
            dcc.Interval(id='monitor-intervals', interval=5000),
            fuc.FefferyTimeout(id='monitor-intervals-init', delay=0),
            fac.AntdFlex(
                [
                    Card(
                        fac.AntdDescriptions(
                            id='monitor-sys-desc',
                            items=[],
                            labelStyle={'fontWeight': 'bold'},
                            bordered=True,
                            layout='vertical',
                            column=2,
                        ),
                        title=_('系统信息'),
                    ),
                    Card(
                        fac.AntdDescriptions(
                            id='monitor-cpu-load-desc',
                            items=[],
                            labelStyle={'fontWeight': 'bold'},
                            bordered=True,
                            layout='vertical',
                            column=3,
                        ),
                        title='CPU',
                    ),
                    Card(
                        fac.AntdDescriptions(
                            id='monitor-mem-load-desc',
                            items=[],
                            labelStyle={'fontWeight': 'bold'},
                            bordered=True,
                            layout='vertical',
                            column=2,
                        ),
                        title=_('内存'),
                    ),
                    Card(
                        fac.AntdDescriptions(
                            id='monitor-process-desc',
                            items=[],
                            labelStyle={'fontWeight': 'bold'},
                            bordered=True,
                            layout='vertical',
                            column=2,
                        ),
                        title=_('进程运行状态'),
                    ),
                    Card(
                        fac.AntdTable(
                            id='monitor-disk-desc',
                            columns=[
                                {'title': '设备名', 'dataIndex': 'dir_name'},
                                {'title': '文件系统类型', 'dataIndex': 'sys_type_name'},
                                {'title': '总容量', 'dataIndex': 'total'},
                                {'title': '已用', 'dataIndex': 'used'},
                                {'title': '可用', 'dataIndex': 'free'},
                                {'title': '使用率', 'dataIndex': 'usage'},
                                {'title': '挂载点', 'dataIndex': 'type_name'},
                            ],
                            data=[],
                            bordered=True,
                            pagination=False,
                        ),
                        title=_('磁盘状态'),
                    ),
                ],
                gap='small',
                wrap='wrap',
            ),
        ]
    )
