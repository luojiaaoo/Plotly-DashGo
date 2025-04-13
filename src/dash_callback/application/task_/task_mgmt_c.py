from server import app
from dash.dependencies import Input, Output, State
import feffery_antd_components as fac
import feffery_utils_components as fuc
from dash_components import Table
import dash
from dash import set_props, html, dcc
from dash_components import MessageManager
import time
import json
import random
import re
from common.utilities.util_apscheduler import (
    get_apscheduler_all_jobs,
    start_stop_job,
    get_platform,
    add_local_interval_job,
    add_ssh_interval_job,
    add_local_cron_job,
    add_ssh_cron_job,
    remove_job,
    get_job,
)
from feffery_dash_utils.style_utils import style
from uuid import uuid4
from datetime import datetime
from common.utilities.util_menu_access import get_menu_access


def get_table_data():
    return [
        {
            'job_id': job.job_id,
            'type': job.type,
            'extract_names': '-' if job.extract_names is None else str(job.extract_names),
            'trigger': job.trigger,
            'plan': f'{job.plan}',
            'job_next_run_time': job.job_next_run_time,
            'create_by': job.create_by,
            'create_datetime': job.create_datetime,
            'enable': {
                'checked': job.status,
                'checkedChildren': 'Run',
                'unCheckedChildren': 'Close',
                'custom': job.job_id,
            },
            'action': [
                {
                    'content': 'Edit',
                    'type': 'primary',
                    'custom': f'edit:{job.job_id}',
                },
                {
                    'content': 'View',
                    'type': 'primary',
                    'custom': f'view:{job.job_id}',
                },
            ],
        }
        for job in sorted(get_apscheduler_all_jobs(), key=lambda job: job.create_datetime, reverse=True)
    ]


@app.callback(
    Output('task-mgmt-table-container', 'children'),
    Input('task-mgmt-init-timeout', 'timeoutCount'),
    prevent_initial_call=True,
)
def init_table(timeoutCount):
    """页面加载时初始化渲染表格"""
    return [
        fac.AntdModal(
            title=[
                fac.AntdText(id='task-mgmt-table-add-modal-title'),
                dcc.Store(id='task-mgmt-table-add-modal-task-type-store'),
            ],
            id='task-mgmt-table-add-modal',
            renderFooter=True,
            okClickClose=False,
            width=800,
        ),
        fac.AntdSpin(
            Table(
                id='task-mgmt-table',
                columns=[
                    {'title': '任务名', 'dataIndex': 'job_id', 'width': 'calc(100% / 10)'},
                    {'title': '类型', 'dataIndex': 'type', 'width': 'calc(100% / 10)'},
                    {'title': '数据采集', 'dataIndex': 'extract_names', 'width': 'calc(100% / 10)'},
                    {'title': '触发器', 'dataIndex': 'trigger', 'width': 'calc(100% / 10)'},
                    {'title': '执行计划', 'dataIndex': 'plan', 'width': 'calc(100% / 10)'},
                    {'title': '下一次执行时间', 'dataIndex': 'job_next_run_time', 'width': 'calc(100% / 10)'},
                    {'title': '创建人', 'dataIndex': 'create_by', 'width': 'calc(100% / 10)'},
                    {'title': '创建时间', 'dataIndex': 'create_datetime', 'width': 'calc(100% / 10)'},
                    {'title': '启用', 'dataIndex': 'enable', 'renderOptions': {'renderType': 'switch'}, 'width': 'calc(100% / 10)'},
                    {'title': '操作', 'dataIndex': 'action', 'renderOptions': {'renderType': 'button'}, 'width': 'calc(100% / 10)'},
                ],
                rowSelectionType='checkbox',
                data=get_table_data(),
                pageSize=10,
            ),
            indicator=fuc.FefferyExtraSpinner(type='classic', color='#335efb'),
        ),
    ]


@app.callback(
    Output('task-mgmt-table', 'data', allow_duplicate=True),
    [
        Input('task-mgmt-table', 'recentlySwitchDataIndex'),
        Input('task-mgmt-table', 'recentlySwitchStatus'),
        Input('task-mgmt-table', 'recentlySwitchRow'),
    ],
    prevent_initial_call=True,
)
def handle_enable_eow(recentlySwitchDataIndex, recentlySwitchStatus, recentlySwitchRow):
    """处理启用、关闭逻辑"""
    status = recentlySwitchRow['enable']['checked']
    job_id = recentlySwitchRow['enable']['custom']
    start_stop_job(job_id=job_id, is_start=status)
    if status:
        MessageManager.success(content=f'{job_id}任务启用成功')
    else:
        MessageManager.success(content=f'{job_id}任务停用成功')
    return get_table_data()


@app.callback(
    Output('task-mgmt-table', 'data', allow_duplicate=True),
    Input('task-mgmt-button-flash', 'nClicks'),
    prevent_initial_call=True,
)
def flash_table(nClicks):
    time.sleep(0.5)
    return get_table_data()


@app.callback(
    [
        Output('task-mgmt-table-add-modal', 'visible'),
        Output('task-mgmt-table-add-modal-title', 'children'),
        Output('task-mgmt-table-add-modal-task-type-store', 'data'),  # 任务类型 cron/interval
    ],
    [
        Input('task-mgmt-button-add-interval', 'nClicks'),
        Input('task-mgmt-button-add-cron', 'nClicks'),
        Input('task-mgmt-table', 'nClicksButton'),
    ],
    [
        State('task-mgmt-table', 'clickedCustom'),
        State('task-mgmt-table', 'recentlyButtonClickedRow'),
    ],
    prevent_initial_call=True,
)
def show_modal(nClicks, nClicks_, nClicksButton, clickedCustom, recentlyButtonClickedRow):
    """显示新增interval数据模态框"""
    if dash.ctx.triggered_id == 'task-mgmt-button-add-interval':
        return True, '新增周期任务', 'interval'
    elif dash.ctx.triggered_id == 'task-mgmt-button-add-cron':
        return True, '新增定时任务', 'cron'
    elif dash.ctx.triggered_id == 'task-mgmt-table' and clickedCustom.startswith('edit'):
        job_id = clickedCustom.split(':', 1)[-1]
        trigger = recentlyButtonClickedRow['trigger']
        return True, '编辑任务' + '⠆' + job_id, trigger  # ⠆特殊盲文符号，用于对编辑任务的识别，并且不影响阅读
    elif dash.ctx.triggered_id == 'task-mgmt-table' and clickedCustom.startswith('view'):
        set_props('main-dcc-url', {'pathname': '/task_/task_log'})
        job_id = clickedCustom.split(':', 1)[-1]
        set_props('task-mgmt-view-jump-job-id', {'data': job_id})
        set_props('task-mgmt-view-jump-timeout', {'delay': 1000})  # 1秒后触发jump_to_log_view对view的参数进行填写
        return dash.no_update
    MessageManager.error(content='不支持的任务类型')
    return dash.no_update


@app.callback(
    Input('task-mgmt-view-jump-timeout', 'timeoutCount'),
    [
        State('task-mgmt-view-jump-job-id', 'data'),
        State('task-log-get-log-btn', 'nClicks'),
    ],
    prevent_initial_call=True,
)
def jump_to_log_view(timeoutCount, job_id, nClicks):
    from dash_callback.application.task_.task_log_c import get_start_datetime_options_by_job_id

    all_job = [{'label': job.job_id, 'value': job.job_id} for job in get_apscheduler_all_jobs()]
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
    set_props('task-log-start-datetime-select', {'value': all_time_of_job[0]['value']})
    set_props('task-log-get-log-btn', {'nClicks': (nClicks or 0) + 1})


@app.callback(
    Output('task-mgmt-table-add-modal', 'children'),
    Input('task-mgmt-table-add-modal', 'visible'),
    State('task-mgmt-table-add-modal-task-type-store', 'data'),
    running=[Output('task-mgmt-table-add-modal', 'loading'), True, False],
    prevent_initial_call=True,
)
def refresh_add_modal(visible, task_type):
    """刷新新增数据模态框内容"""

    if not visible:
        return dash.no_update
    time.sleep(0.2)
    custom_items = [
        fac.AntdFormItem(
            fac.AntdInputNumber(id='task-mgmt-table-add-modal-interval', value=30), label='周期（秒）', style=style(display='block' if task_type == 'interval' else 'none')
        ),
        fac.AntdFormItem(
            fac.AntdSpace(
                [
                    fac.AntdInput(id='task-mgmt-table-add-modal-cron-minute', value='*', addonAfter='分'),
                    fac.AntdInput(id='task-mgmt-table-add-modal-cron-hour', value='*', addonAfter='时'),
                    fac.AntdInput(id='task-mgmt-table-add-modal-cron-day', value='*', addonAfter='日'),
                    fac.AntdInput(id='task-mgmt-table-add-modal-cron-month', value='*', addonAfter='月'),
                    fac.AntdInput(id='task-mgmt-table-add-modal-cron-day-of-week', value='*', addonAfter='周'),
                ],
            ),
            label='Cron定时字串',
            tooltip="""
『int|str minute: minute (0-59)』
『int|str hour: hour (0-23)』
『int|str day: day of month (1-31)』
『int|str month: month (1-12)』
『int|str day_of_week: number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)』
""",
            style=style(display='block' if task_type == 'cron' else 'none'),
        ),
    ]
    return fac.AntdForm(
        [
            dcc.Store(id='task-mgmt-table-add-modal-ok-trigger-store', data=''),
            dcc.Store(id='task-mgmt-table-add-modal-editor-script-text-store'),
            fac.AntdFormItem(
                fac.AntdSegmented(
                    key=uuid4().hex,
                    id='task-mgmt-table-add-modal-run-type-select',
                    options=[
                        {'label': '本地脚本' + f'<系统类型为{get_platform()}>', 'value': 'local', 'icon': 'md-home'},
                        {'label': 'ssh远程执行', 'value': 'ssh', 'icon': 'antd-cloud'},
                    ],
                    defaultValue='local',
                    block=True,
                ),
                label='类型',
            ),
            fac.AntdFormItem(
                fac.AntdInput(id='task-mgmt-table-add-modal-job-id'),
                label='任务名',
                id='task-mgmt-table-add-modal-job-id-item',
            ),
            fac.AntdSpace(
                [
                    fac.AntdFormItem(
                        fac.AntdSpace(
                            [fac.AntdInput(id='task-mgmt-table-add-modal-ssh-host'), fac.AntdInputNumber(id='task-mgmt-table-add-modal-ssh-port', value=22)],
                        ),
                        label='主机/端口',
                    ),
                    fac.AntdFormItem(
                        fac.AntdSpace(
                            [fac.AntdInput(id='task-mgmt-table-add-modal-ssh-username'), fac.AntdInput(mode='password', id='task-mgmt-table-add-modal-ssh-password')],
                        ),
                        label='用户名/密码',
                    ),
                ],
                id='task-mgmt-table-add-modal-ssh-container',
                style=style(display='none'),
            ),
            *custom_items,
            fac.AntdFormItem(fac.AntdInputNumber(id='task-mgmt-table-add-modal-timeout', value=20), label='超时时间（秒）'),
            fac.AntdFormItem(
                fac.AntdSpace(
                    [
                        fac.AntdSpace(
                            [
                                fac.AntdRadioGroup(
                                    id='task-mgmt-table-add-modal-update-editor-language',
                                    options=['Shell', 'Bat'],
                                    optionType='button',
                                    buttonStyle='solid',
                                    value='Shell',
                                ),
                                fuc.FefferyFullscreen(
                                    id='task-mgmt-table-add-modal-editor-fullscreen',
                                    targetId='task-mgmt-table-add-modal-editor-mount-target',
                                ),
                                fac.AntdButton('收起/展开', color='primary', variant='outlined', id='task-mgmt-table-add-modal-editor-collapse-btn'),
                                fac.AntdButton('全屏', color='primary', variant='outlined', id='task-mgmt-table-add-modal-editor-fullscreen-btn'),
                            ],
                        ),
                        fuc.FefferyTimeout(id='task-mgmt-table-add-modal-editor-full-timeout'),
                        # 代码编辑器挂载点
                        html.Div(id='task-mgmt-table-add-modal-editor-mount-target'),
                    ],
                    direction='vertical',
                    style=style(width=600),
                ),
                label='脚本',
            ),
            fac.AntdFormItem(
                fac.AntdSelect(id='task-mgmt-table-add-modal-extract-names-type-number', mode='tags', allowClear=False, value=[]),
                label='抽取-数值类型',
                tooltip='日志格式要求：<SOPS_VAR>name:val</SOPS_VAR>，name为变量值',
            ),
            fac.AntdFormItem(
                fac.AntdSelect(id='task-mgmt-table-add-modal-extract-names-type-string', mode='tags', allowClear=False, value=[]),
                label='抽取-字符类型',
                tooltip='日志格式要求：<SOPS_VAR>name:val</SOPS_VAR>，name为变量值',
            ),
        ],
        labelCol={'span': 4},
        wrapperCol={'span': 20},
        style={'width': 700},
    )


@app.callback(
    Output('task-mgmt-table-add-modal-editor-script-text-store', 'id'),
    Input('task-mgmt-table-add-modal-editor-script-text-store', 'id'),
    State('task-mgmt-table-add-modal-title', 'children'),
)
def full_value_for_edit(id, title):
    # 如果是编辑，初始化数据
    if '⠆' not in title:  # 特殊盲文符号，作为编辑动作的标志位
        return dash.no_update
    job_id = title.split('⠆')[-1]
    job_dict = get_job(job_id)
    set_props('task-mgmt-table-add-modal-update-editor-language', {'value': job_dict['kwargs']['script_type']})
    set_props('task-mgmt-table-add-modal-editor-full-timeout', {'delay': 100})  # 间接代码填充
    set_props('task-mgmt-table-add-modal-run-type-select', {'value': job_dict['kwargs']['type']})  # 任务名
    set_props('task-mgmt-table-add-modal-job-id', {'value': job_id})  # 任务名
    set_props('task-mgmt-table-add-modal-job-id-item', {'style': {'display': 'none'}})  # 任务名, 不给看
    if job_dict['kwargs']['type'] == 'ssh':
        set_props('task-mgmt-table-add-modal-ssh-host', {'value': job_dict['kwargs']['host']})  # ssh主机
        set_props('task-mgmt-table-add-modal-ssh-port', {'value': job_dict['kwargs']['port']})  # ssh 端口
        set_props('task-mgmt-table-add-modal-ssh-username', {'value': job_dict['kwargs']['username']})  # ssh用户名
        set_props('task-mgmt-table-add-modal-ssh-password', {'value': job_dict['kwargs']['password']})  # ssh密码
    set_props('task-mgmt-table-add-modal-timeout', {'value': job_dict['kwargs']['timeout']})  # 超时时间
    if job_dict['kwargs']['extract_names']:
        extract_names = json.loads(job_dict['kwargs']['extract_names'])
        set_props(
            'task-mgmt-table-add-modal-extract-names-type-number',
            {'value': [extract_name['name'] for extract_name in extract_names if extract_name['type'] == 'number']},
        )  # 抽取数据-数值类型
        set_props(
            'task-mgmt-table-add-modal-extract-names-type-string',
            {'value': [extract_name['name'] for extract_name in extract_names if extract_name['type'] == 'string']},
        )  # 超时时间-字符串类型
    if job_dict['trigger'] == 'interval':
        set_props('task-mgmt-table-add-modal-interval', {'value': job_dict['plan']['seconds']})  # interval周期
    if job_dict['trigger'] == 'cron':
        set_props('task-mgmt-table-add-modal-cron-minute', {'value': job_dict['plan']['minute']})  # cron 分
        set_props('task-mgmt-table-add-modal-cron-hour', {'value': job_dict['plan']['hour']})  # cron 小时
        set_props('task-mgmt-table-add-modal-cron-day', {'value': job_dict['plan']['day']})  # cron 天
        set_props('task-mgmt-table-add-modal-cron-month', {'value': job_dict['plan']['month']})  # cron 月
        set_props('task-mgmt-table-add-modal-cron-day-of-week', {'value': job_dict['plan']['day_of_week']})  # cron 周
    return dash.no_update


@app.callback(
    Input('task-mgmt-table-add-modal-editor-full-timeout', 'timeoutCount'),
    State('task-mgmt-table-add-modal-title', 'children'),
    prevent_initial_call=True,
)
def full_script_for_edit(timeoutCount, title):
    job_id = title.split('⠆')[-1]
    job_dict = get_job(job_id)
    # 设置editor的代码
    script_text = job_dict['kwargs']['script_text']
    json_str = json.dumps({'script_text': script_text})
    set_props('main-execute-js-output', {'jsString': f'const obj = {json_str};window.taskEditor.setValue(obj.script_text);'})


# ssh参数隐藏/显示
app.clientside_callback(
    """(value) => {
        if(value=='ssh'){
            return {'display':'block'}
        }else{
            return {'display':'None'}
        }
    }""",
    Output('task-mgmt-table-add-modal-ssh-container', 'style'),
    Input('task-mgmt-table-add-modal-run-type-select', 'value'),
)

# 代码编辑器折叠
app.clientside_callback(
    """(value,style) => {
        if(style === undefined || style['display']!='None'){
            return {'display':'None','height': '300px'}
        }else{
            return {'display':'block','height': '300px'}
        }
    }""",
    Output('task-mgmt-table-add-modal-editor-mount-target', 'style'),
    Input('task-mgmt-table-add-modal-editor-collapse-btn', 'nClicks'),
    State('task-mgmt-table-add-modal-editor-mount-target', 'style'),
)


# 全屏代码编辑器
@app.callback(
    [
        Output('task-mgmt-table-add-modal-editor-mount-target', 'style', allow_duplicate=True),
        Output('task-mgmt-table-add-modal-editor-fullscreen', 'isFullscreen'),
    ],
    Input('task-mgmt-table-add-modal-editor-fullscreen-btn', 'nClicks'),
    State('task-mgmt-table-add-modal-editor-fullscreen', 'isFullscreen'),
    prevent_initial_call=True,
)
def toggle_fullscreen(nClicks, isFullscreen):
    return style(display='block', height='300px'), not isFullscreen


# 注入代码编辑器
app.clientside_callback(
    """(language, id) => {

    // 销毁先前已存在的编辑器实例
    if ( window.taskEditor ) {
        window.taskEditor.dispose();
    }
    window.taskEditor = monaco.editor.create(document.getElementById(id), {
        value: null,
        language: language.toLowerCase(),
        automaticLayout: true,
        lineNumbers: "on",
        theme: "vs-dark"
    });
    return window.dash_clientside.no_update;
}""",
    Output('task-mgmt-table-add-modal-editor-mount-target', 'children', allow_duplicate=True),
    Input('task-mgmt-table-add-modal-update-editor-language', 'value'),
    State('task-mgmt-table-add-modal-editor-mount-target', 'id'),
    prevent_initial_call='initial_duplicate',
)

app.clientside_callback(
    """
        (okCounts) => {
            return [Date.now(), window.taskEditor.getValue()]
        }
    """,
    [
        Output('task-mgmt-table-add-modal-ok-trigger-store', 'data'),
        Output('task-mgmt-table-add-modal-editor-script-text-store', 'data'),
    ],
    Input('task-mgmt-table-add-modal', 'okCounts'),
    prevent_initial_call=True,
)


@app.callback(
    Output('task-mgmt-table', 'data', allow_duplicate=True),
    Input('task-mgmt-table-add-modal-ok-trigger-store', 'data'),
    [
        State('task-mgmt-table-add-modal-task-type-store', 'data'),  # 任务类型 周期/定时
        State('task-mgmt-table-add-modal-run-type-select', 'value'),  # 执行类型 ssh/local
        State('task-mgmt-table-add-modal-editor-script-text-store', 'data'),  # 脚本
        State('task-mgmt-table-add-modal-update-editor-language', 'value'),  # 脚本类型
        State('task-mgmt-table-add-modal-job-id', 'value'),  # 任务名
        State('task-mgmt-table-add-modal-ssh-host', 'value'),  # ssh主机
        State('task-mgmt-table-add-modal-ssh-port', 'value'),  # ssh 端口
        State('task-mgmt-table-add-modal-ssh-username', 'value'),  # ssh用户名
        State('task-mgmt-table-add-modal-ssh-password', 'value'),  # ssh密码
        State('task-mgmt-table-add-modal-timeout', 'value'),  # 超时时间
        State('task-mgmt-table-add-modal-extract-names-type-number', 'value'),  # 抽取数据-数值类型
        State('task-mgmt-table-add-modal-extract-names-type-string', 'value'),  # 超时时间-字符串类型
        State('task-mgmt-table-add-modal-interval', 'value'),  # interval周期
        State('task-mgmt-table-add-modal-cron-minute', 'value'),  # cron 分
        State('task-mgmt-table-add-modal-cron-hour', 'value'),  # cron 小时
        State('task-mgmt-table-add-modal-cron-day', 'value'),  # cron 天
        State('task-mgmt-table-add-modal-cron-month', 'value'),  # cron 月
        State('task-mgmt-table-add-modal-cron-day-of-week', 'value'),  # cron 周
        State('task-mgmt-table-add-modal-title', 'children'),
    ],
    prevent_initial_call=True,
)
def add_edit_job(
    trigger,
    task_type,
    type_run,
    script_text,
    script_type,
    job_id,
    ssh_host,
    ssh_port,
    ssh_username,
    ssh_password,
    timeout,
    extract_names_number,
    extract_names_string,
    interval,
    cron_minute,
    cron_hour,
    cron_day,
    cron_month,
    cron_day_of_week,
    title,
):
    if not trigger:  # fix: 无法避免初始化调用
        return dash.no_update
    cron_verify = r'^((?<![\d\-\*])((\*\/)?([0-5]?[0-9])((\,|\-|\/)([0-5]?[0-9]))*|\*)[^\S\r\n]+((\*\/)?((2[0-3]|1[0-9]|[0-9]|00))((\,|\-|\/)(2[0-3]|1[0-9]|[0-9]|00))*|\*)[^\S\r\n]+((\*\/)?([1-9]|[12][0-9]|3[01])((\,|\-|\/)([1-9]|[12][0-9]|3[01]))*|\*)[^\S\r\n]+((\*\/)?([1-9]|1[0-2])((\,|\-|\/)([1-9]|1[0-2]))*|\*|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))[^\S\r\n]+((\*\/)?[0-6]((\,|\-|\/)[0-6])*|\*|00|(sun|mon|tue|wed|thu|fri|sat))[^\S\r\n]*(?:\bexpr \x60date \+\\\%W\x60 \\\% \d{1,2} \> \/dev\/null \|\|)?(?=$| |\'|\"))|@(annually|yearly|monthly|weekly|daily|hourly|reboot)$'
    if not re.match(cron_verify, f'{cron_minute} {cron_hour} {cron_day} {cron_month} {cron_day_of_week}'):
        MessageManager.error(content='cron表达式不正确')
        return dash.no_update
    create_by, create_datetime = None, None
    if '⠆' in title:  # 特殊盲文符号，作为编辑动作的标志位，先删后增
        job_dict = get_job(job_id)
        create_by = job_dict['kwargs']['create_by']
        create_datetime = job_dict['kwargs']['create_datetime']
        remove_job(job_id)  # 删除
    # 新增
    op_user_name = get_menu_access(only_get_user_name=True)
    now = f'{datetime.now():%Y-%m-%dT%H:%M:%S}'
    create_by = create_by or op_user_name
    create_datetime = create_datetime or f'{datetime.now():%Y-%m-%dT%H:%M:%S}'
    if type_run == 'local' and task_type == 'interval':
        add_local_interval_job(
            script_text=script_text,
            script_type=script_type,
            interval=int(interval),
            timeout=int(timeout),
            job_id=job_id,
            update_by=op_user_name,
            update_datetime=now,
            create_by=create_by,
            create_datetime=create_datetime,
            extract_names=json.dumps(
                [
                    *[{'type': 'string', 'name': i} for i in extract_names_string],
                    *[{'type': 'number', 'name': i} for i in extract_names_number],
                ]
            ),
        )
    elif type_run == 'ssh' and task_type == 'interval':
        add_ssh_interval_job(
            host=ssh_host,
            port=ssh_port,
            username=ssh_username,
            password=ssh_password,
            script_text=script_text,
            script_type=script_type,
            interval=int(interval),
            timeout=int(timeout),
            job_id=job_id,
            update_by=op_user_name,
            update_datetime=now,
            create_by=create_by,
            create_datetime=create_datetime,
            extract_names=json.dumps(
                [
                    *[{'type': 'string', 'name': i} for i in extract_names_string],
                    *[{'type': 'number', 'name': i} for i in extract_names_number],
                ]
            ),
        )
    elif type_run == 'local' and task_type == 'cron':
        add_local_cron_job(
            script_text=script_text,
            script_type=script_type,
            #          秒(随机起始秒)                  分                 小时             天                月                    星期              年   第几周
            cron_list=[random.randint(0, 59), cron_minute or '*', cron_hour or '*', cron_day or '*', cron_month or '*', cron_day_of_week or '*', '*', '*'],
            timeout=int(timeout),
            job_id=job_id,
            update_by=op_user_name,
            update_datetime=now,
            create_by=create_by,
            create_datetime=create_datetime,
            extract_names=json.dumps(
                [
                    *[{'type': 'string', 'name': i} for i in extract_names_string],
                    *[{'type': 'number', 'name': i} for i in extract_names_number],
                ]
            ),
        )
    elif type_run == 'ssh' and task_type == 'cron':
        add_ssh_cron_job(
            host=ssh_host,
            port=ssh_port,
            username=ssh_username,
            password=ssh_password,
            script_text=script_text,
            script_type=script_type,
            #          秒(随机起始秒)                 分                 小时             天                月                    星期              年   第几周
            cron_list=[random.randint(0, 59), cron_minute or '*', cron_hour or '*', cron_day or '*', cron_month or '*', cron_day_of_week or '*', '*', '*'],
            timeout=int(timeout),
            job_id=job_id,
            update_by=op_user_name,
            update_datetime=now,
            create_by=create_by,
            create_datetime=create_datetime,
            extract_names=json.dumps(
                [
                    *[{'type': 'string', 'name': i} for i in extract_names_string],
                    *[{'type': 'number', 'name': i} for i in extract_names_number],
                ]
            ),
        )
    else:
        MessageManager.error(content='不支持的运行类型' + type_run)
        return
    MessageManager.success(content='添加任务成功')
    return get_table_data()


@app.callback(
    Output('task-mgmt-table', 'data', allow_duplicate=True),
    Input('task-mgmt-button-delete', 'confirmCounts'),
    State('task-mgmt-table', 'selectedRows'),
    prevent_initial_call=True,
)
def handle_delete(confirmCounts, selectedRows):
    """处理表格数据行删除逻辑"""

    # 若当前无已选中行
    if not selectedRows:
        MessageManager.warning(content='请先选择要删除的行')
        return dash.no_update

    # 删除选中行
    [remove_job(row['job_id']) for row in selectedRows]
    MessageManager.success(content='选中行删除成功')

    # 重置选中行
    set_props('task-mgmt-table', {'selectedRows': []})
    set_props('task-mgmt-table', {'selectedRowKeys': []})

    return get_table_data()
