from dash.dependencies import Input, Output, State, MATCH
from server import app
import feffery_antd_components as fac
from dash_components import MessageManager
from database.sql_db.dao import dao_listen
import dash
from uuid import uuid4
from dash import dcc
import json
from typing import List
from common.listen import email_imap
from datetime import datetime, timedelta
from feffery_dash_utils.style_utils import style
from i18n import t__setting


def api_name_value2label(api_name: str):
    return api_name.split('\0', 1)[0]


def get_tabs_items():
    items = []
    # server酱配置
    listen_apis = dao_listen.get_listen_api_by_name(api_name=None)
    for listen_api in listen_apis:
        api_type = listen_api.api_type
        if api_type not in dao_listen.support_api_types:
            raise Exception(f'不支持{api_type}类型的消息监听')
        api_name = listen_api.api_name
        api_name_label = api_name_value2label(api_name)
        params_json = listen_api.params_json
        if api_type == '邮件IMAP协议':
            if params_json and (params_json := json.loads(params_json)):
                imap_server = params_json['imap_server']
                port = params_json['port']
                email_account = params_json['email_account']
                password = params_json['password']
            else:
                imap_server = ''
                port = ''
                email_account = ''
                password = ''
            items.append(
                {
                    'key': api_name,
                    'label': api_name_label + f' ({t__setting(api_type)})',
                    'contextMenu': [{'key': api_name, 'label': t__setting('删除')}],
                    'children': fac.AntdSpace(
                        [
                            dcc.Store(id={'type': 'notify-api-imap-api-name', 'name': api_name}, data=api_name),
                            fac.AntdDivider(api_name_label, innerTextOrientation='left'),
                            fac.AntdForm(
                                [
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-imap-imap-server', 'name': api_name}, value=imap_server),
                                        label='imap-server',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-imap-port', 'name': api_name}, value=port if port else '993'),
                                        label='port',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-imap-email-account', 'name': api_name}, value=email_account),
                                        label='email-account',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-imap-password', 'name': api_name}, value=password),
                                        label='password',
                                    ),
                                ],
                                labelCol={'span': 5},
                                wrapperCol={'span': 20},
                            ),
                            fac.AntdSpace(
                                [
                                    fac.AntdButton(
                                        t__setting('保存'),
                                        id={'type': 'notify-api-imap-save', 'name': api_name},
                                        type='primary',
                                    ),
                                    fac.AntdButton(
                                        t__setting('消息测试'),
                                        id={'type': 'notify-api-imap-test', 'name': api_name},
                                        type='default',
                                    ),
                                ],
                            ),
                        ],
                        direction='vertical',
                        style=style(width='100%'),
                    ),
                }
            )
    return items


def get_listen_api():
    api_names = []
    api_names_enabled = []
    listen_apis = dao_listen.get_listen_api_by_name(api_name=None)
    for listen_api in listen_apis:
        api_name = listen_api.api_name
        enable = listen_api.enable
        if enable:
            api_names_enabled.append(api_name)
        api_names.append(api_name)
    return [
        {
            'label': api_name_value2label(api_name),
            'value': api_name,
        }
        for api_name in api_names
    ], api_names_enabled


# 新建邮件IMAP协议
@app.callback(
    [
        Output('listen-api-edit-tabs', 'items', allow_duplicate=True),
        Output('listen-api-activate', 'options', allow_duplicate=True),
        Output('listen-api-activate', 'value', allow_duplicate=True),
    ],
    Input('listen-api-add-email-imap', 'nClicks'),
    State('listen-api-add-name', 'value'),
    prevent_initial_call=True,
)
def add_server_imap_listen_api(nClick, api_name_label):
    if not api_name_label:
        MessageManager.error(content=t__setting('请输入API名称'))
        return dash.no_update
    for i in dao_listen.get_listen_api_by_name(api_name=None):
        if api_name_value2label(i.api_name) == api_name_label:
            MessageManager.error(content=api_name_label + t__setting('已存在'))
            return dash.no_update
    dao_listen.insert_listen_api(api_name=api_name_label + f'\0{uuid4().hex[:12]}', api_type='邮件IMAP协议', enable=False, params_json='{}')
    MessageManager.success(content=api_name_label + t__setting('创建成功'))
    return [get_tabs_items(), *get_listen_api()]


# server酱保存回调
@app.callback(
    Output({'type': 'notify-api-imap-save', 'name': MATCH}, 'id'),
    Input({'type': 'notify-api-imap-save', 'name': MATCH}, 'nClicks'),
    [
        State({'type': 'notify-api-imap-imap-server', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-imap-port', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-imap-email-account', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-imap-password', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-imap-api-name', 'name': MATCH}, 'data'),
    ],
    prevent_initial_call=True,
)
def save_server_jiang_api(nClick, imap_server, port, email_account, password, api_name):
    values = dict(
        imap_server=imap_server,
        port=port,
        email_account=email_account,
        password=password,
    )
    api_name_label = api_name_value2label(api_name)
    dao_listen.delete_listen_api_by_name(api_name=api_name)
    if dao_listen.insert_listen_api(api_name=api_name, api_type='邮件IMAP协议', enable=True, params_json=json.dumps(values)):
        MessageManager.success(content=api_name_label + t__setting('配置保存成功'))
    else:
        MessageManager.error(content=api_name_label + t__setting('配置保存失败'))
    return dash.no_update


# 测试邮件IMAP协议
@app.callback(
    Output({'type': 'notify-api-imap-test', 'name': MATCH}, 'id'),
    Input({'type': 'notify-api-imap-test', 'name': MATCH}, 'nClicks'),
    [
        State({'type': 'notify-api-imap-imap-server', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-imap-port', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-imap-email-account', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-imap-password', 'name': MATCH}, 'value'),
    ],
    prevent_initial_call=True,
)
def test_Gewechat_api(nClicks, imap_server, port, email_account, password):
    try:
        email_imap.get_email_context_from_subject_during(
            imap_server=imap_server,
            port=port,
            emal_account=email_account,
            password=password,
            subject='xxx',
            since_time=datetime.now() - timedelta(days=1),
            before_time=datetime.now(),
        )
    except Exception as e:
        MessageManager.error(content=t__setting('IMAP测试接收失败') + ' [ERROR]' + str(e))
    else:
        MessageManager.success(content=t__setting('IMAP测试接收成功'))
    return dash.no_update
