from server import app
from dash.dependencies import Input, Output
from common.utilities import util_sys
import feffery_antd_components as fac
from functools import partial
from i18n import translator

__ = partial(translator.t)


@app.callback(
    [
        Output('monitor-sys-desc', 'items'),
        Output('monitor-cpu-load-desc', 'items'),
        Output('monitor-mem-load-desc', 'items'),
        Output('monitor-process-desc', 'items'),
        Output('monitor-disk-desc', 'data'),
    ],
    [
        Input('monitor-intervals', 'n_intervals'),
        Input('monitor-intervals-init', 'timeoutCount'),
    ],
    prevent_initial_call=True,
)
def callback_func(n_intervals, timeoutCount):
    sys_info = util_sys.get_sys_info()
    return [
        [
            {'label': fac.AntdText(__('域名')), 'children': sys_info['hostname']},
            {'label': fac.AntdText(__('系统类型')), 'children': sys_info['os_name']},
            {'label': fac.AntdText(__('计算机名')), 'children': sys_info['computer_name']},
            {'label': fac.AntdText(__('核心架构')), 'children': sys_info['os_arch']},
        ],
        [
            {'label': fac.AntdText(__('型号')), 'children': sys_info['cpu_name']},
            {'label': fac.AntdText(__('逻辑核数')), 'children': sys_info['cpu_num']},
            {'label': fac.AntdText(__('空闲率')), 'children': f"{sys_info['cpu_free_percent']*100}%"},
            {'label': fac.AntdText(__('总使用率')), 'children': f"{sys_info['cpu_user_usage_percent']*100}%"},
            {'label': fac.AntdText(__('用户使用率')), 'children': f"{sys_info['cpu_user_usage_percent']*100}%"},
            {'label': fac.AntdText(__('系统使用率')), 'children': f"{sys_info['cpu_user_usage_percent']*100}%"},
        ],
        [
            {'label': fac.AntdText(__('总量')), 'children': sys_info['memory_total']},
            {'label': fac.AntdText(__('已用')), 'children': sys_info['memory_used']},
            {'label': fac.AntdText(__('剩余')), 'children': sys_info['memory_free']},
            {'label': fac.AntdText(__('使用率')), 'children': f"{sys_info['memory_usage_percent']*100}%"},
        ],
        [
            {'label': fac.AntdText(__('Python版本')), 'children': sys_info['python_version']},
            {'label': fac.AntdText(__('启动时间')), 'children': sys_info['start_time']},
            {'label': fac.AntdText(__('运行时长')), 'children': sys_info['run_time']},
            {'label': fac.AntdText(__('内存使用量')), 'children': sys_info['current_process_memory_usage']},
        ],
        sys_info['sys_files'],
    ]
