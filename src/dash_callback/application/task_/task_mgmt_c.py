from server import app
from dash.dependencies import Input, Output, State
import feffery_antd_components as fac
import feffery_utils_components as fuc
from dash_components import Table
import dash
from dash import set_props, html
from dash_components import MessageManager
import time
from database.sql_db.dao import dao_apscheduler
from common.utilities.util_apscheduler import add_local_interval_job, get_apscheduler_all_jobs, start_stop_job, get_platform
from feffery_dash_utils.style_utils import style
from uuid import uuid4


def get_table_data():
    return [
        {
            'job_id': job.job_id,
            'type': job.type,
            'extract_names': '-' if job.extract_names is None else str(job.extract_names),
            'trigger': job.trigger,
            'plan': f'{job.plan}',
            'job_next_run_time': job.job_next_run_time,
            'enable': {
                'checked': job.status,
                'checkedChildren': 'open',
                'unCheckedChildren': 'close',
                'custom': job.job_id,
            },
            'view_log': {
                'content': 'View Log',
                'type': 'primary',
                'custom': f'view_log:{job.job_id}',
            },
        }
        for job in get_apscheduler_all_jobs()
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
            id='task-mgmt-table-add-interval-modal',
            title='新增周期任务',
            renderFooter=True,
            okClickClose=False,
            width=800,
        ),
        fac.AntdModal(
            id='task-mgmt-table-add-cron-modal',
            title='新增定时任务',
            renderFooter=True,
            okClickClose=False,
            width=800,
        ),
        Table(
            id='task-mgmt-table',
            columns=[
                {'title': '任务名', 'dataIndex': 'job_id', 'width': 'calc(100% / 8)'},
                {'title': '类型', 'dataIndex': 'type', 'width': 'calc(100% / 8)'},
                {'title': '数据采集', 'dataIndex': 'extract_names', 'width': 'calc(100% / 8)'},
                {'title': '触发器', 'dataIndex': 'trigger', 'width': 'calc(100% / 8)'},
                {'title': '执行计划', 'dataIndex': 'plan', 'width': 'calc(100% / 8)'},
                {'title': '下一次执行时间', 'dataIndex': 'job_next_run_time', 'width': 'calc(100% / 8)'},
                {'title': '启用', 'dataIndex': 'enable', 'renderOptions': {'renderType': 'switch'}, 'width': 'calc(100% / 8)'},
                {'title': '执行记录', 'dataIndex': 'view_log', 'renderOptions': {'renderType': 'button'}, 'width': 'calc(100% / 8)'},
            ],
            rowSelectionType='radio',
            data=get_table_data(),
            pageSize=10,
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
    Output('task-mgmt-table-add-interval-modal', 'visible'),
    Input('task-mgmt-button-add-interval', 'nClicks'),
    prevent_initial_call=True,
)
def open_add_modal(nClicks):
    """显示新增interval数据模态框"""
    return True


@app.callback(
    Output('task-mgmt-table-add-interval-modal', 'children'),
    Input('task-mgmt-table-add-interval-modal', 'visible'),
    running=[Output('task-mgmt-table-add-interval-modal', 'loading'), True, False],
    prevent_initial_call=True,
)
def refresh_add_modal(visible):
    """刷新新增interval数据模态框内容"""

    if visible:
        time.sleep(0.5)
        return fac.AntdForm(
            [
                fac.AntdFormItem(
                    fac.AntdSegmented(
                        key=uuid4().hex,
                        id='task-mgmt-table-add-interval-modal-type-select',
                        options=[
                            {'label': '本地脚本' + f'<系统类型为{get_platform()}>', 'value': 'local', 'icon': 'md-home'},
                            {'label': 'ssh远程执行', 'value': 'ssh', 'icon': 'antd-cloud'},
                        ],
                        defaultValue='local',
                        block=True,
                    ),
                    label='类型',
                ),
                fac.AntdSpace(
                    [
                        fac.AntdFormItem(
                            fac.AntdInput(
                                id='task-mgmt-table-add-interval-modal-ssh-username',
                            ),
                            label='ssh用户名',
                        ),
                        fac.AntdFormItem(
                            fac.AntdInput(
                                mode='password',
                                id='task-mgmt-table-add-interval-modal-ssh-password',
                            ),
                            label='ssh密码',
                        ),
                    ],
                    id='task-mgmt-table-add-interval-modal-ssh-container',
                    style=style(display='none'),
                ),
                fac.AntdFormItem(
                    fac.AntdSpace(
                        [
                            fac.AntdSpace(
                                [
                                    fac.AntdRadioGroup(
                                        id='task-mgmt-table-add-interval-modal-update-editor-language',
                                        options=['Bat', 'Shell'],
                                        optionType='button',
                                        buttonStyle='solid',
                                        value='Bat',
                                    ),
                                    fuc.FefferyFullscreen(
                                        id='task-mgmt-table-add-interval-modal-editor-fullscreen',
                                        targetId='task-mgmt-table-add-interval-modal-editor-mount-target',
                                    ),
                                    fac.AntdButton('收起/展开', id='task-mgmt-table-add-interval-modal-editor-collapse-btn'),
                                    fac.AntdButton('全屏', id='task-mgmt-table-add-interval-modal-editor-fullscreen-btn'),
                                ],
                            ),
                            # 代码编辑器挂载点
                            html.Div(id='task-mgmt-table-add-interval-modal-editor-mount-target'),
                        ],
                        direction='vertical',
                        style=style(width=600),
                    ),
                    label='脚本',
                ),
            ],
            labelCol={'span': 3},
            wrapperCol={'span': 20},
            style={'width': 700},
        )
    return dash.no_update


# interval-ssh参数隐藏/显示
app.clientside_callback(
    """(value) => {
        if(value=='ssh'){
            return {'display':'block'}
        }else{
            return {'display':'None'}
        }
    }""",
    Output('task-mgmt-table-add-interval-modal-ssh-container', 'style'),
    Input('task-mgmt-table-add-interval-modal-type-select', 'value'),
)

# interval代码编辑器折叠
app.clientside_callback(
    """(value,style) => {
        if(style === undefined || style['display']!='None'){
            return {'display':'None','height': '300px'}
        }else{
            return {'display':'block','height': '300px'}
        }
    }""",
    Output('task-mgmt-table-add-interval-modal-editor-mount-target', 'style'),
    Input('task-mgmt-table-add-interval-modal-editor-collapse-btn', 'nClicks'),
    State('task-mgmt-table-add-interval-modal-editor-mount-target', 'style'),
)


# interval全屏代码编辑器
@app.callback(
    [
        Output('task-mgmt-table-add-interval-modal-editor-mount-target', 'style', allow_duplicate=True),
        Output('task-mgmt-table-add-interval-modal-editor-fullscreen', 'isFullscreen'),
    ],
    Input('task-mgmt-table-add-interval-modal-editor-fullscreen-btn', 'nClicks'),
    State('task-mgmt-table-add-interval-modal-editor-fullscreen', 'isFullscreen'),
    prevent_initial_call=True,
)
def toggle_fullscreen(nClicks, isFullscreen):
    return style(display='block', height='300px'), not isFullscreen

# 注入interval代码编辑器
app.clientside_callback(
    """(language, id) => {

    // 销毁先前已存在的编辑器实例
    if ( window.myEditor ) {
        window.myEditor.dispose();
    }
    window.myEditor = monaco.editor.create(document.getElementById(id), {
        value: null,
        language: language.toLowerCase(),
        automaticLayout: true,
        lineNumbers: "on",
        theme: "vs-dark"
    });
    return window.dash_clientside.no_update;
}""",
    Output('task-mgmt-table-add-interval-modal-editor-mount-target', 'children', allow_duplicate=True),
    Input('task-mgmt-table-add-interval-modal-update-editor-language', 'value'),
    State('task-mgmt-table-add-interval-modal-editor-mount-target', 'id'),
    prevent_initial_call='initial_duplicate',
)
