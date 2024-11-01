# from server import app
# from dash.dependencies import Input, Output, State
# from common.utilities import util_sys


# @app.callback(
#     [
#         Output('monitor-cpu-num', 'children'),
#         Output('monitor-cpu-use-percent', 'value'),
#         Output('monitor-cpu-use-percent', 'children'),
#     ],
#     Input('monitor-intervals', 'n_intervals'),
# )
# def callback_func(n_intervals):
#     sys_info = util_sys.get_sys_info()
#     return (
#         sys_info.get('cpu_num'),
#         *([str(sys_info.get('cpu_use_percent'))] * 2),
#     )
