from server import app
from dash.dependencies import Input, Output, State
from common.utilities import util_sys
import feffery_antd_components as fac
from dash import html


@app.callback(
    [
        Output('monitor-sys-desc', 'items'),
        Output('monitor-cpu-load-desc', 'items'),
    ],
    [
        Input('monitor-intervals', 'n_intervals'),
        Input('monitor-intervals-init', 'timeoutCount'),
    ],
)
def callback_func(n_intervals, timeoutCount):
    sys_info = util_sys.get_sys_info()
    return [
        [
            {'label': fac.AntdText('域名'), 'children': sys_info['hostname']},
            {'label': fac.AntdText('系统类型'), 'children': sys_info['os_name']},
            {'label': fac.AntdText('计算机名'), 'children': sys_info['computer_name']},
            {'label': fac.AntdText('核心架构'), 'children': sys_info['os_arch']},
        ],
        [
            {'label': fac.AntdText('型号'), 'children': sys_info['cpu_name']},
            {'label': fac.AntdText('逻辑核数'), 'children': sys_info['cpu_num']},
            {'label': fac.AntdText('空闲率'), 'children': sys_info['cpu_free_percent']},
            {'label': fac.AntdText('总使用率'), 'children': sys_info['cpu_user_usage_percent']},
            {'label': fac.AntdText('用户使用率'), 'children': sys_info['cpu_user_usage_percent']},
            {'label': fac.AntdText('系统使用率'), 'children': sys_info['cpu_user_usage_percent']},
        ],
    ]
