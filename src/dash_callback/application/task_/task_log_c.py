from server import app
from dash.dependencies import Input, Output, State
import feffery_antd_components as fac
import feffery_utils_components as fuc
import dash
from uuid import uuid4
from dash import set_props
from common.utilities.util_apscheduler import get_apscheduler_all_jobs
from dash_components import MessageManager
from i18n import t__task


def color_job_finish_status(status):
    if status == 'success':
        return 'green'
    elif status == 'error':
        return 'red'
    elif status == 'timeout':
        return 'orange'
    elif status == 'running':
        return 'purple'
    else:
        raise ValueError(f'未知的status：{status}')


def get_start_datetime_options_by_job_id(job_id):
    from database.sql_db.dao.dao_apscheduler import get_apscheduler_start_finish_datetime_with_status_by_job_id
    from datetime import datetime

    return [
        {
            'label': [
                fac.AntdText(job_id, keyboard=True),
                f' Run Time:{start_datetime:%Y-%m-%dT%H:%M:%S} - {f"{finish_datetime:%Y-%m-%dT%H:%M:%S}" if isinstance(finish_datetime, datetime) else finish_datetime} (Duration:{f"{int((finish_datetime - start_datetime).total_seconds())}s" if isinstance(finish_datetime, datetime) else "unfinish"}) ',
                fac.AntdTag(
                    key=uuid4().hex,
                    content=f'Status:{status.upper()}',
                    color=color_job_finish_status(status),
                ),
            ],
            'value': f'{start_datetime:%Y-%m-%dT%H:%M:%S.%f}',
        }
        for start_datetime, finish_datetime, status in get_apscheduler_start_finish_datetime_with_status_by_job_id(job_id)
    ]


@app.callback(
    [
        Output('task-log-start-datetime-select', 'options'),
        Output('task-log-start-datetime-select', 'value'),
        Output('task-log-start-datetime-select', 'key'),
    ],
    Input('task-log-get-start-datetime-btn', 'nClicks'),
    State('task-log-job-id-select', 'value'),
    prevent_initial_call=True,
)
def get_run_times(nClicks, job_id):
    if not job_id:
        MessageManager.warning(content=t__task('请选择任务'))
        return dash.no_update
    all_time_of_job = get_start_datetime_options_by_job_id(job_id)
    if not all_time_of_job:
        MessageManager.warning(content=t__task('任务日志不存在，等待任务运行'))
        return all_time_of_job, None, uuid4().hex
    return all_time_of_job, all_time_of_job[0]['value'], uuid4().hex


# app.clientside_callback(
#     """(value) =>{
#             return [[], null]
#         }
#     """,
#     [
#         Output('task-log-start-datetime-select', 'options', allow_duplicate=True),
#         Output('task-log-start-datetime-select', 'value'),
#     ],
#     Input('task-log-job-id-select', 'value'),
#     prevent_initial_call=True,
# )


@app.callback(
    [
        Output('task-log-sse-container', 'children'),
        Output('task-log-command-output-records', 'children'),
    ],
    Input('task-log-get-log-btn', 'nClicks'),
    [
        State('task-log-job-id-select', 'value'),
        State('task-log-start-datetime-select', 'value'),
    ],
    prevent_initial_call=True,
)
def start_sse(nClick, job_id, start_datetime):
    from urllib.parse import quote
    import uuid

    if not (job_id and start_datetime):
        MessageManager.warning(content=t__task('请选择任务和开始时间'))
        return dash.no_update
    return (
        fuc.FefferyPostEventSource(
            key=uuid.uuid4().hex,
            id='task-log-sse',
            autoReconnect=dict(retries=3, delay=5000),
            withCredentials=True,
            headers={'job-id': quote(job_id), 'start-datetime': start_datetime},
            immediate=True,
            url='/task_log_sse',
        ),
        [],
    )


app.clientside_callback(
    """(data, children, checked) => {
        if (data) {
            if (data.startsWith('<响应结束>')) {
                window.dash_clientside.set_props(
                    'task-log-sse',
                    {
                        operation: 'close'
                    }
                )
                window.dash_clientside.set_props(
                    'task-log-command-output-records',
                    {
                        children: [data.replaceAll('<响应结束>', '').replaceAll('<换行符>', '\\n')]
                    }
                )
            } else {
                window.dash_clientside.set_props(
                    'task-log-command-output-records',
                    {
                        children: [...children, data.replaceAll('<换行符>', '\\n')]
                    }
                )
            }
            return checked
        }
    }""",
    Output('task-log-scroll-bottom', 'executeScroll'),
    Input('task-log-sse', 'data'),
    [
        State('task-log-command-output-records', 'children'),
        State('task-log-scroll-log', 'checked'),
    ],
    prevent_initial_call=True,
)


@app.callback(
    Output('main-task-mgmt-jump-to-task-log-job-id-store', 'data'),
    Input('task-log-viewport', 'inViewport'),
    [
        State('main-task-mgmt-jump-to-task-log-job-id-store', 'data'),
        State('task-log-get-log-btn', 'nClicks'),
    ],
    prevent_initial_call=True,
)
def jump_to_log_view(inViewport, job_id, nClicks):
    if not inViewport or not job_id:
        return dash.no_update
    from dash_callback.application.task_.task_log_c import get_start_datetime_options_by_job_id

    all_job = [{'label': job.job_id, 'value': job.job_id} for job in get_apscheduler_all_jobs()]
    all_job.sort(key=lambda job: job['label'], reverse=True)
    set_props(
        'task-log-job-id-select',
        {'options': all_job},
    )
    set_props('task-log-job-id-select', {'value': job_id})
    all_time_of_job = get_start_datetime_options_by_job_id(job_id)
    set_props(
        'task-log-start-datetime-select',
        {'options': all_time_of_job},
    )
    set_props(
        'task-log-start-datetime-select',
        {'key': uuid4().hex},
    )
    if not all_time_of_job:
        MessageManager.warning(content=t__task('任务日志不存在，等待任务运行'))
        set_props('task-log-start-datetime-select', {'value': None})
    else:
        datetime_select = all_time_of_job[0]['value']
        set_props('task-log-start-datetime-select', {'value': datetime_select})
        set_props('task-log-get-log-btn', {'nClicks': (nClicks or 0) + 1})
    return None
