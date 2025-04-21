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
from dash_callback.application.setting_.notify_api_c import api_name_value2label
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
from database.sql_db.dao.dao_notify import get_notify_api_by_name
from database.sql_db.dao.dao_listen import get_listen_api_by_name
from feffery_dash_utils.style_utils import style
from uuid import uuid4
from datetime import datetime
from i18n import t__task
from database.sql_db.dao import dao_listen_task
from common.utilities.util_menu_access import get_menu_access
import json


def get_table_data():
    return [
        {
            'job_id': job.job_id,
            'type': job.type,
            'extract_names': str(json.loads(job.extract_names)) if job.extract_names and json.loads(job.extract_names) else '-',
            'trigger': job.trigger,
            'notify_channels': str([api_name_value2label(i) for i in json.loads(job.notify_channels)]) if job.notify_channels and json.loads(job.notify_channels) else '-',
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
            width=900,
        ),
        fac.AntdSpin(
            Table(
                id='task-mgmt-table',
                columns=[
                    {'title': t__task('任务名'), 'dataIndex': 'job_id', 'width': 'calc(100% / 11)'},
                    {'title': t__task('类型'), 'dataIndex': 'type', 'width': 'calc(100% / 11)'},
                    {'title': t__task('数据采集'), 'dataIndex': 'extract_names', 'width': 'calc(100% / 11)'},
                    {'title': t__task('通知渠道'), 'dataIndex': 'notify_channels', 'width': 'calc(100% / 11)'},
                    {'title': t__task('触发器'), 'dataIndex': 'trigger', 'width': 'calc(100% / 11)'},
                    {'title': t__task('执行计划'), 'dataIndex': 'plan', 'width': 'calc(100% / 11)'},
                    {'title': t__task('下一次执行时间'), 'dataIndex': 'job_next_run_time', 'width': 'calc(100% / 11)'},
                    {'title': t__task('创建人'), 'dataIndex': 'create_by', 'width': 'calc(100% / 11)'},
                    {'title': t__task('创建时间'), 'dataIndex': 'create_datetime', 'width': 'calc(100% / 11)'},
                    {'title': t__task('启用'), 'dataIndex': 'enable', 'renderOptions': {'renderType': 'switch'}, 'width': 'calc(100% / 11)'},
                    {'title': t__task('操作'), 'dataIndex': 'action', 'renderOptions': {'renderType': 'button'}, 'width': 'calc(100% / 11)'},
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
    type_task = recentlySwitchRow['trigger']
    status = recentlySwitchRow['enable']['checked']
    job_id = recentlySwitchRow['enable']['custom']
    start_stop_job(job_id=job_id, is_start=status, type_task=type_task)
    if status:
        MessageManager.success(content=f'{job_id}' + t__task('任务启用成功'))
    else:
        MessageManager.success(content=f'{job_id}' + t__task('任务停用成功'))
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
        Input('task-mgmt-button-add-listen', 'nClicks'),
        Input('task-mgmt-table', 'nClicksButton'),
    ],
    [
        State('task-mgmt-table', 'clickedCustom'),
        State('task-mgmt-table', 'recentlyButtonClickedRow'),
    ],
    prevent_initial_call=True,
)
def show_modal(nClicks, nClicks_, nClicks__, nClicksButton, clickedCustom, recentlyButtonClickedRow):
    """显示新增interval数据模态框"""
    if dash.ctx.triggered_id == 'task-mgmt-button-add-interval':
        return True, t__task('新增周期任务'), 'interval'
    elif dash.ctx.triggered_id == 'task-mgmt-button-add-cron':
        return True, t__task('新增定时任务'), 'cron'
    elif dash.ctx.triggered_id == 'task-mgmt-button-add-listen':
        return True, t__task('新增监听接口触发任务'), 'listen'
    elif dash.ctx.triggered_id == 'task-mgmt-table' and clickedCustom.startswith('edit'):
        job_id = clickedCustom.split(':', 1)[-1]
        trigger = recentlyButtonClickedRow['trigger']
        return True, t__task('编辑任务') + '⠆' + job_id, trigger  # ⠆特殊盲文符号，用于对编辑任务的识别，并且不影响阅读
    elif dash.ctx.triggered_id == 'task-mgmt-table' and clickedCustom.startswith('view'):
        set_props('main-dcc-url', {'pathname': '/task_/task_log'})
        job_id = clickedCustom.split(':', 1)[-1]
        set_props('main-task-mgmt-jump-to-task-log-job-id-store', {'data': job_id})
        return dash.no_update
    MessageManager.error(content=t__task('不支持的任务类型'))
    return dash.no_update


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
            fac.AntdInputNumber(id='task-mgmt-table-add-modal-interval', value=30), label=t__task('周期（秒）'), style=style(display='block' if task_type == 'interval' else 'none')
        ),
        fac.AntdFormItem(
            fac.AntdSpace(
                [
                    fac.AntdInput(id='task-mgmt-table-add-modal-cron-minute', value='*', addonAfter=t__task('分')),
                    fac.AntdInput(id='task-mgmt-table-add-modal-cron-hour', value='*', addonAfter=t__task('时')),
                    fac.AntdInput(id='task-mgmt-table-add-modal-cron-day', value='*', addonAfter=t__task('日')),
                    fac.AntdInput(id='task-mgmt-table-add-modal-cron-month', value='*', addonAfter=t__task('月')),
                    fac.AntdInput(id='task-mgmt-table-add-modal-cron-day-of-week', value='*', addonAfter=t__task('周')),
                ],
            ),
            label=t__task('Cron定时字串'),
            tooltip="""
『minute: minute (0-59)』
『hour: hour (0-23)』
『day: day of month (1-31)』
『month: month (1-12)』
『day_of_week: number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)』
""",
            style=style(display='block' if task_type == 'cron' else 'none'),
        ),
    ]
    return fac.AntdForm(
        [
            dcc.Store(id='task-mgmt-table-add-modal-ok-store', data=''),
            dcc.Store(id='task-mgmt-table-add-modal-editor-script-text-store'),
            fac.AntdFormItem(
                fac.AntdSegmented(
                    key=uuid4().hex,
                    id='task-mgmt-table-add-modal-run-type-select',
                    options=[
                        {'label': t__task('本地脚本') + t__task('<系统类型为') + f'{get_platform()}>', 'value': 'local', 'icon': 'md-home'},
                        {'label': t__task('ssh远程执行'), 'value': 'ssh', 'icon': 'antd-cloud'},
                    ],
                    defaultValue='local',
                    block=True,
                ),
                label=t__task('执行类型'),
            ),
            fac.AntdFormItem(
                fac.AntdInput(id='task-mgmt-table-add-modal-job-id'),
                label=t__task('任务名'),
                id='task-mgmt-table-add-modal-job-id-item',
            ),
            fac.AntdFormItem(
                fac.AntdSpace(
                    [
                        fac.AntdInput(id='task-mgmt-table-add-modal-listen-keyword', value=uuid4().hex,style=style(width=300)),
                        fac.AntdCheckboxGroup(
                            options=[{'label': api_name_value2label(listen_api.api_name), 'value': listen_api.api_name} for listen_api in get_listen_api_by_name(api_name=None)],
                            value=[],
                            id='task-mgmt-table-add-modal-listen-channels',
                            style=style(marginLeft=10),
                        ),
                    ],
                ),
                label=t__task('监听接口触发任务的验证关键词/渠道'),
                id='task-mgmt-table-add-modal-listen-keyword-item',
                tooltip=t__task('选择的监听渠道如果title字段包含该关键词，则会自动触发该任务'),
                style=style(display='block' if task_type == 'listen' else 'none'),
            ),
            fac.AntdSpace(
                [
                    fac.AntdFormItem(
                        fac.AntdSpace(
                            [fac.AntdInput(id='task-mgmt-table-add-modal-ssh-host'), fac.AntdInputNumber(id='task-mgmt-table-add-modal-ssh-port', value=22)],
                        ),
                        label=t__task('主机/端口'),
                        id='task-mgmt-table-add-modal-ssh-host-port-item',
                    ),
                    fac.AntdFormItem(
                        fac.AntdSpace(
                            [
                                fac.AntdInput(id='task-mgmt-table-add-modal-ssh-username'),
                                fac.AntdInput(mode='password', id='task-mgmt-table-add-modal-ssh-password'),
                                fac.AntdButton(t__task('测试连接'), id='task-mgmt-table-add-modal-ssh-test-btn', color='primary', variant='outlined'),
                            ],
                        ),
                        id='task-mgmt-table-add-modal-ssh-username-password-item',
                        label=t__task('用户名/密码'),
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
                                    options=['Shell', 'Bat', 'Python'],
                                    optionType='button',
                                    buttonStyle='solid',
                                    value='Shell',
                                ),
                                fuc.FefferyFullscreen(
                                    id='task-mgmt-table-add-modal-editor-fullscreen',
                                    targetId='task-mgmt-table-add-modal-editor-mount-target',
                                ),
                                fac.AntdButton(t__task('收起/展开'), color='primary', variant='outlined', id='task-mgmt-table-add-modal-editor-collapse-btn'),
                                fac.AntdButton(t__task('全屏'), color='primary', variant='outlined', id='task-mgmt-table-add-modal-editor-fullscreen-btn'),
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
            fac.AntdParagraph(
                t__task('以下选项为数据抽取，输出格式为：<SOPS_VAR>name:val</SOPS_VAR>，name为变量名，val为变量值')
                + '\n'
                + t__task('1、符合格式要求的数值类型/字符类型，会写入数据库sys_apscheduler_extract_value表中；')
                + '\n'
                + t__task('2、符合格式要求的通知类型，会把name当作标题，val为内容，通过配置的“系统设置/通知接口”发送出去。')
                + '\n'
                + t__task('！！ 当脚本失败/超时自动进行消息推送。'),
                ellipsis={'expandable': 'collapsible', 'rows': 1},
                style=style(whiteSpace='pre-wrap'),
            ),
            fac.AntdFormItem(
                fac.AntdSelect(id='task-mgmt-table-add-modal-extract-names-type-number', mode='tags', allowClear=False, value=[]),
                label=t__task('抽取-数值类型'),
            ),
            fac.AntdFormItem(
                fac.AntdSelect(id='task-mgmt-table-add-modal-extract-names-type-string', mode='tags', allowClear=False, value=[]),
                label=t__task('抽取-字符类型'),
            ),
            fac.AntdFormItem(
                fac.AntdSelect(id='task-mgmt-table-add-modal-extract-names-type-notify', mode='tags', allowClear=False, value=[]),
                label=t__task('抽取-通知类型'),
            ),
            fac.AntdFormItem(
                fac.AntdCheckboxGroup(
                    options=[{'label': api_name_value2label(notify_api.api_name), 'value': notify_api.api_name} for notify_api in get_notify_api_by_name(api_name=None)],
                    value=[],
                    id='task-mgmt-table-add-modal-extract-names-type-notify-for-notify-channels',
                ),
                label=t__task('通知类型-通知渠道'),
            ),
        ],
        labelWrap=True,
        labelCol={'span': 4},
        wrapperCol={'span': 20},
        style={'width': 800},
    )


@app.callback(
    Output('task-mgmt-table-add-modal-editor-script-text-store', 'id'),
    Input('task-mgmt-table-add-modal-editor-script-text-store', 'id'),
    [
        State('task-mgmt-table-add-modal-title', 'children'),
        State('task-mgmt-table-add-modal-extract-names-type-notify-for-notify-channels', 'options'),
        State('task-mgmt-table-add-modal-listen-channels', 'options'),
        State('task-mgmt-table-add-modal-task-type-store', 'data'),
    ],
)
def full_value_for_edit(id, title, notify_channels_options, listen_channels_options, task_type):
    # 如果是编辑，初始化数据
    if '⠆' not in title:  # 特殊盲文符号，作为编辑动作的标志位
        return dash.no_update
    notify_channels_options_value = [notify_channels_option['value'] for notify_channels_option in notify_channels_options]
    job_id = title.split('⠆')[-1]
    set_props('task-mgmt-table-add-modal-job-id', {'value': job_id})  # 任务名
    set_props('task-mgmt-table-add-modal-job-id-item', {'style': {'display': 'none'}})  # 任务名, 不给看
    if task_type != 'listen':
        # aps自带任务
        job_dict = get_job(job_id)
        set_props('task-mgmt-table-add-modal-update-editor-language', {'value': job_dict['kwargs']['script_type']})
        set_props('task-mgmt-table-add-modal-editor-full-timeout', {'delay': 100})  # 间接代码填充
        set_props('task-mgmt-table-add-modal-run-type-select', {'value': job_dict['kwargs']['type']})  # 任务名
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
            )  # 抽取数据-字符串类型
            set_props(
                'task-mgmt-table-add-modal-extract-names-type-notify',
                {'value': [extract_name['name'] for extract_name in extract_names if extract_name['type'] == 'notify']},
            )  # 抽取数据-通知类型
        if job_dict['kwargs']['notify_channels']:
            notify_channels = json.loads(job_dict['kwargs']['notify_channels'])
            set_props(
                'task-mgmt-table-add-modal-extract-names-type-notify-for-notify-channels',
                {'value': [notify_channel for notify_channel in notify_channels if notify_channel in notify_channels_options_value]},
            )  # 通知类型-通知渠道
        if job_dict['trigger'] == 'interval':
            set_props('task-mgmt-table-add-modal-interval', {'value': job_dict['plan']['seconds']})  # interval周期
        if job_dict['trigger'] == 'cron':
            set_props('task-mgmt-table-add-modal-cron-minute', {'value': job_dict['plan']['minute']})  # cron 分
            set_props('task-mgmt-table-add-modal-cron-hour', {'value': job_dict['plan']['hour']})  # cron 小时
            set_props('task-mgmt-table-add-modal-cron-day', {'value': job_dict['plan']['day']})  # cron 天
            set_props('task-mgmt-table-add-modal-cron-month', {'value': job_dict['plan']['month']})  # cron 月
            set_props('task-mgmt-table-add-modal-cron-day-of-week', {'value': job_dict['plan']['day_of_week']})  # cron 周
    else:
        # listen监听接口触发任务
        job = dao_listen_task.get_activa_listen_job(job_id=job_id)[0]
        set_props('task-mgmt-table-add-modal-listen-keyword', {'value': job.listen_keyword})
        set_props('task-mgmt-table-add-modal-update-editor-language', {'value': job.script_type})
        set_props('task-mgmt-table-add-modal-editor-full-timeout', {'delay': 100})  # 间接代码填充
        set_props('task-mgmt-table-add-modal-run-type-select', {'value': job.type})  # 任务名
        if job.type == 'ssh':
            set_props('task-mgmt-table-add-modal-ssh-host', {'value': job.host})  # ssh主机
            set_props('task-mgmt-table-add-modal-ssh-port', {'value': job.port})  # ssh 端口
            set_props('task-mgmt-table-add-modal-ssh-username', {'value': job.username})  # ssh用户名
            set_props('task-mgmt-table-add-modal-ssh-password', {'value': job.password})  # ssh密码
        set_props('task-mgmt-table-add-modal-timeout', {'value': job.timeout})  # 超时时间
        if job.extract_names:
            extract_names = json.loads(job.extract_names)
            set_props(
                'task-mgmt-table-add-modal-extract-names-type-number',
                {'value': [extract_name['name'] for extract_name in extract_names if extract_name['type'] == 'number']},
            )  # 抽取数据-数值类型
            set_props(
                'task-mgmt-table-add-modal-extract-names-type-string',
                {'value': [extract_name['name'] for extract_name in extract_names if extract_name['type'] == 'string']},
            )  # 抽取数据-字符串类型
            set_props(
                'task-mgmt-table-add-modal-extract-names-type-notify',
                {'value': [extract_name['name'] for extract_name in extract_names if extract_name['type'] == 'notify']},
            )  # 抽取数据-通知类型
        if job.notify_channels:
            notify_channels = json.loads(job.notify_channels)
            set_props(
                'task-mgmt-table-add-modal-extract-names-type-notify-for-notify-channels',
                {'value': [notify_channel for notify_channel in notify_channels if notify_channel in notify_channels_options_value]},
            )  # 通知类型-通知渠道
        if job.listen_channels:
            listen_channels_options_value = [listen_channels_option['value'] for listen_channels_option in listen_channels_options]
            listen_channels = json.loads(job.listen_channels)
            set_props(
                'task-mgmt-table-add-modal-listen-channels',
                {'value': [listen_channel for listen_channel in listen_channels if listen_channel in listen_channels_options_value]},
            )  # 监听渠道
    return dash.no_update


@app.callback(
    Input('task-mgmt-table-add-modal-editor-full-timeout', 'timeoutCount'),
    [
        State('task-mgmt-table-add-modal-title', 'children'),
        State('task-mgmt-table-add-modal-task-type-store', 'data'),
    ],
    prevent_initial_call=True,
)
def full_script_for_edit(timeoutCount, title, task_type):
    job_id = title.split('⠆')[-1]
    if task_type != 'listen':
        job_dict = get_job(job_id)
        # 设置editor的代码
        script_text = job_dict['kwargs']['script_text']
    else:
        script_text = dao_listen_task.get_activa_listen_job(job_id=job_id)[0].script_text
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


# 测试ssh连接
@app.callback(
    [
        Output('task-mgmt-table-add-modal-ssh-host-port-item', 'validateStatus'),
        Output('task-mgmt-table-add-modal-ssh-username-password-item', 'validateStatus'),
    ],
    Input('task-mgmt-table-add-modal-ssh-test-btn', 'nClicks'),
    [
        State('task-mgmt-table-add-modal-ssh-host', 'value'),
        State('task-mgmt-table-add-modal-ssh-port', 'value'),
        State('task-mgmt-table-add-modal-ssh-username', 'value'),
        State('task-mgmt-table-add-modal-ssh-password', 'value'),
    ],
    running=[
        (Output('task-mgmt-table-add-modal-ssh-test-btn', 'loading'), True, False),
    ],
    prevent_initial_call=True,
)
def test_connection(nClicks, host, port, username, password):
    """测试ssh连接"""
    from common.utilities import util_ssh

    if not (host and port and username):
        MessageManager.error(content=t__task('主机/端口/用户名不能为空'))
    try:
        util_ssh.connect_ssh(hostname=host, port=port, username=username, password=password)
    except:
        MessageManager.error(content=t__task('连接错误，请检查主机/端口/用户名/密码'))
        return 'error', 'error'
    MessageManager.success(content=t__task('连接成功'))
    return 'success', 'success'


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


# 注入vscode代码编辑器
app.clientside_callback(
    """(language, id) => {

    // 销毁先前已存在的编辑器实例
    if ( window.taskEditor ) {
        window.taskEditor.dispose();
    };
    value=null;
    if (language.toLowerCase() === 'bat'){
        value="@echo off\\n:: Python Example \\nconda activate env1\\npython E:\\\\script\\\\example.py\\n:: Echo Example\\necho \\"<SOPS_VAR>name:val</SOPS_VAR>\\"";
    }else if(language.toLowerCase() === 'shell'){
        value="# Python Example \\nconda activate env1\\npython /app/script/example.py\\n# Echo Example\\necho \\"<SOPS_VAR>name:val</SOPS_VAR>\\"";
    }else if(language.toLowerCase() === 'python'){
        value="# Echo Example\\nprint(\\"<SOPS_VAR>name:val</SOPS_VAR>\\")";
    }

    monaco.languages.register({ id: 'python' });
    monaco.languages.setMonarchTokensProvider('python', {
        tokenizer: {
            root: [
                [/print|def|class|if|else|elif|for|while|return|try|except|finally|with|import|from|as|pass|break|continue/, 'keyword'],
                [/#.*$/, 'comment'],
                [/"[^"]*"|'[^']*'/, 'string'],
                [/\d+/, 'number'],
                [/[a-zA-Z_]\w*/, 'identifier'],
            ]
        }
    });

    window.taskEditor = monaco.editor.create(document.getElementById(id), {
        value: value,
        language: language.toLowerCase(),
        wordWrap: "on",
        wrappingIndent: "same",
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
        Output('task-mgmt-table-add-modal-ok-store', 'data'),
        Output('task-mgmt-table-add-modal-editor-script-text-store', 'data'),
    ],
    Input('task-mgmt-table-add-modal', 'okCounts'),
    prevent_initial_call=True,
)


@app.callback(
    Output('task-mgmt-table', 'data', allow_duplicate=True),
    Input('task-mgmt-table-add-modal-ok-store', 'data'),
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
        State('task-mgmt-table-add-modal-extract-names-type-string', 'value'),  # 抽取数据-字符串类型
        State('task-mgmt-table-add-modal-extract-names-type-notify', 'value'),  # 抽取数据-通知类型
        State('task-mgmt-table-add-modal-extract-names-type-notify-for-notify-channels', 'value'),  # 通知类型-通知渠道
        State('task-mgmt-table-add-modal-interval', 'value'),  # interval周期
        State('task-mgmt-table-add-modal-cron-minute', 'value'),  # cron 分
        State('task-mgmt-table-add-modal-cron-hour', 'value'),  # cron 小时
        State('task-mgmt-table-add-modal-cron-day', 'value'),  # cron 天
        State('task-mgmt-table-add-modal-cron-month', 'value'),  # cron 月
        State('task-mgmt-table-add-modal-cron-day-of-week', 'value'),  # cron 周
        State('task-mgmt-table-add-modal-listen-keyword', 'value'),  # listen 关键词
        State('task-mgmt-table-add-modal-listen-channels', 'value'),  # listen 渠道
        State('task-mgmt-table-add-modal-title', 'children'),
    ],
    prevent_initial_call=True,
)
def add_edit_job(
    modal_ok,
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
    extract_names_notify,
    notify_channels,
    interval,
    cron_minute,
    cron_hour,
    cron_day,
    cron_month,
    cron_day_of_week,
    listen_keyword,
    listen_channels,
    title,
):
    if not modal_ok:  # fix: 无法避免初始化调用
        return dash.no_update
    # 如果任务类型是cron，需要提前检查cron表达式是否正确
    cron_verify = r'^((?<![\d\-\*])((\*\/)?([0-5]?[0-9])((\,|\-|\/)([0-5]?[0-9]))*|\*)[^\S\r\n]+((\*\/)?((2[0-3]|1[0-9]|[0-9]|00))((\,|\-|\/)(2[0-3]|1[0-9]|[0-9]|00))*|\*)[^\S\r\n]+((\*\/)?([1-9]|[12][0-9]|3[01])((\,|\-|\/)([1-9]|[12][0-9]|3[01]))*|\*)[^\S\r\n]+((\*\/)?([1-9]|1[0-2])((\,|\-|\/)([1-9]|1[0-2]))*|\*|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))[^\S\r\n]+((\*\/)?[0-6]((\,|\-|\/)[0-6])*|\*|00|(sun|mon|tue|wed|thu|fri|sat))[^\S\r\n]*(?:\bexpr \x60date \+\\\%W\x60 \\\% \d{1,2} \> \/dev\/null \|\|)?(?=$| |\'|\"))|@(annually|yearly|monthly|weekly|daily|hourly|reboot)$'
    if task_type == 'cron' and not re.match(cron_verify, f'{cron_minute} {cron_hour} {cron_day} {cron_month} {cron_day_of_week}'):
        MessageManager.error(content='cron表达式不正确')
        return dash.no_update
    is_edit = False
    status = True
    create_by, create_datetime = None, None
    if '⠆' in title:  # 特殊盲文符号，作为编辑动作的标志位，先删后增
        if task_type != 'listen':
            job_dict = get_job(job_id)
            status = job_dict['status']
            create_by = job_dict['kwargs']['create_by']
            create_datetime = job_dict['kwargs']['create_datetime']
        else:
            job = dao_listen_task.get_activa_listen_job(job_id=job_id)[0]
            status = job.status
            create_by = job.create_by
            create_datetime = f'{job.create_datetime:%Y-%m-%dT%H:%M:%S}'
        remove_job(job_id, task_type)  # 删除
        is_edit = True
    else:
        # 新增
        if dao_listen_task.get_activa_listen_job(job_id=job_id) or get_job(job_id):
            MessageManager.error(content=t__task('任务名已存在，请修改后重试'))
            return dash.no_update
    op_user_name = get_menu_access(only_get_user_name=True)
    now = f'{datetime.now():%Y-%m-%dT%H:%M:%S}'
    create_by = create_by or op_user_name
    create_datetime = create_datetime or now
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
                    *[{'type': 'notify', 'name': i} for i in extract_names_notify],
                ]
            ),
            notify_channels=json.dumps(notify_channels),
            is_pause=not status,
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
                    *[{'type': 'notify', 'name': i} for i in extract_names_notify],
                ]
            ),
            notify_channels=json.dumps(notify_channels),
            is_pause=not status,
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
                    *[{'type': 'notify', 'name': i} for i in extract_names_notify],
                ]
            ),
            notify_channels=json.dumps(notify_channels),
            is_pause=not status,
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
                    *[{'type': 'notify', 'name': i} for i in extract_names_notify],
                ]
            ),
            notify_channels=json.dumps(notify_channels),
            is_pause=not status,
        )
    elif type_run == 'local' and task_type == 'listen':
        dao_listen_task.insert_activa_listen_job(
            type=type_run,
            job_id=job_id,
            status=status,
            script_text=script_text,
            script_type=script_type,
            update_by=op_user_name,
            update_datetime=datetime.strptime(now, '%Y-%m-%dT%H:%M:%S'),
            create_by=create_by,
            create_datetime=datetime.strptime(create_datetime, '%Y-%m-%dT%H:%M:%S'),
            notify_channels=json.dumps(notify_channels),
            extract_names=json.dumps(
                [
                    *[{'type': 'string', 'name': i} for i in extract_names_string],
                    *[{'type': 'number', 'name': i} for i in extract_names_number],
                    *[{'type': 'notify', 'name': i} for i in extract_names_notify],
                ]
            ),
            timeout=int(timeout),
            listen_channels=json.dumps(listen_channels),
            listen_keyword=listen_keyword,
        )
    elif type_run == 'ssh' and task_type == 'listen':
        dao_listen_task.insert_activa_listen_job(
            type=type_run,
            job_id=job_id,
            status=status,
            script_text=script_text,
            script_type=script_type,
            update_by=op_user_name,
            update_datetime=datetime.strptime(now, '%Y-%m-%dT%H:%M:%S'),
            create_by=create_by,
            create_datetime=datetime.strptime(create_datetime, '%Y-%m-%dT%H:%M:%S'),
            notify_channels=json.dumps(notify_channels),
            extract_names=json.dumps(
                [
                    *[{'type': 'string', 'name': i} for i in extract_names_string],
                    *[{'type': 'number', 'name': i} for i in extract_names_number],
                    *[{'type': 'notify', 'name': i} for i in extract_names_notify],
                ]
            ),
            timeout=int(timeout),
            host=ssh_host,
            port=ssh_port,
            username=ssh_username,
            password=ssh_password,
            listen_channels=json.dumps(listen_channels),
            listen_keyword=listen_keyword,
        )
    else:
        MessageManager.error(content=t__task('不支持的运行类型') + type_run)
        return
    if not is_edit:
        MessageManager.success(content=t__task('添加任务成功'))
    else:
        MessageManager.success(content=t__task('修改任务成功'))
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
        MessageManager.warning(content=t__task('请先选择要删除的行'))
        return dash.no_update

    # 删除选中行
    [remove_job(row['job_id'], row['trigger']) for row in selectedRows]
    MessageManager.success(content=t__task('选中行删除成功'))

    # 重置选中行
    set_props('task-mgmt-table', {'selectedRows': []})
    set_props('task-mgmt-table', {'selectedRowKeys': []})

    return get_table_data()
