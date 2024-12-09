from server import app
from dash.dependencies import Input, Output
from common.utilities import util_sys
import feffery_antd_components as fac
from i18n import t__dashboard




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
            {'label': fac.AntdText(t__dashboard('域名')), 'children': sys_info['hostname']},
            {'label': fac.AntdText(t__dashboard('系统类型')), 'children': sys_info['os_name']},
            {'label': fac.AntdText(t__dashboard('计算机名')), 'children': sys_info['computer_name']},
            {'label': fac.AntdText(t__dashboard('核心架构')), 'children': sys_info['os_arch']},
        ],
        [
            {'label': fac.AntdText(t__dashboard('型号')), 'children': sys_info['cpu_name']},
            {'label': fac.AntdText(t__dashboard('逻辑核数')), 'children': sys_info['cpu_num']},
            {'label': fac.AntdText(t__dashboard('空闲率')), 'children': f"{sys_info['cpu_free_percent']*100}%"},
            {'label': fac.AntdText(t__dashboard('总使用率')), 'children': f"{sys_info['cpu_user_usage_percent']*100}%"},
            {'label': fac.AntdText(t__dashboard('用户使用率')), 'children': f"{sys_info['cpu_user_usage_percent']*100}%"},
            {'label': fac.AntdText(t__dashboard('系统使用率')), 'children': f"{sys_info['cpu_user_usage_percent']*100}%"},
        ],
        [
            {'label': fac.AntdText(t__dashboard('总量')), 'children': sys_info['memory_total']},
            {'label': fac.AntdText(t__dashboard('已用')), 'children': sys_info['memory_used']},
            {'label': fac.AntdText(t__dashboard('剩余')), 'children': sys_info['memory_free']},
            {'label': fac.AntdText(t__dashboard('使用率')), 'children': f"{sys_info['memory_usage_percent']*100}%"},
        ],
        [
            {'label': fac.AntdText(t__dashboard('Python版本')), 'children': sys_info['python_version']},
            {'label': fac.AntdText(t__dashboard('启动时间')), 'children': sys_info['start_time']},
            {'label': fac.AntdText(t__dashboard('运行时长')), 'children': sys_info['run_time']},
            {'label': fac.AntdText(t__dashboard('内存使用量')), 'children': sys_info['current_process_memory_usage']},
        ],
        sys_info['sys_files'],
    ]
