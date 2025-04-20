from dash.dependencies import Input, Output, State, MATCH
from server import app
import feffery_antd_components as fac
from dash_components import MessageManager
from database.sql_db.dao import dao_notify
import dash
from uuid import uuid4
from dash import dcc
import json
from typing import List
from common.notify import email_smtp, server_jiang, enterprise_wechat, gewechat
from feffery_dash_utils.style_utils import style
from i18n import t__setting


def api_name_value2label(api_name: str):
    return api_name.split('\0', 1)[0]


def get_tabs_items():
    items = []
    # server酱配置
    notify_apis = dao_notify.get_notify_api_by_name(api_name=None)
    for notify_api in notify_apis:
        api_type = notify_api.api_type
        if api_type not in dao_notify.support_api_types:
            raise Exception(f'不支持{api_type}类型的消息推送')
        api_name = notify_api.api_name
        api_name_label = api_name_value2label(api_name)
        params_json = notify_api.params_json
        if api_type == 'Server酱':
            if params_json and (params_json := json.loads(params_json)):
                SendKey = params_json['SendKey']
                Noip = params_json['Noip']
                Channel = params_json['Channel']
                Openid = params_json['Openid']
            else:
                SendKey, Noip, Channel, Openid = '', True, '', ''
            items.append(
                {
                    'key': api_name,
                    'contextMenu': [{'key': api_name, 'label': t__setting('删除')}],
                    'label': api_name_label + f' ({t__setting(api_type)})',
                    'children': fac.AntdSpace(
                        [
                            dcc.Store(id={'type': 'notify-api-server-jiang-api-name', 'name': api_name}, data=api_name),
                            fac.AntdDivider(api_name_label, innerTextOrientation='left'),
                            fac.AntdForm(
                                [
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-server-jiang-SendKey', 'name': api_name}, value=SendKey),
                                        label='SendKey',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdSwitch(id={'type': 'notify-api-server-jiang-Noip', 'name': api_name}, checked=Noip),
                                        label='Noip',
                                        tooltip='是否隐藏IP',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-server-jiang-Channel', 'name': api_name}, value=Channel),
                                        label='Channel',
                                        tooltip='发送通道',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(
                                            id={'type': 'notify-api-server-jiang-Openid', 'name': api_name},
                                            value=Openid,
                                        ),
                                        label='Openid',
                                        tooltip='只有测试号和企业微信应用消息需要填写',
                                    ),
                                ],
                                labelCol={'span': 5},
                                wrapperCol={'span': 20},
                            ),
                            fac.AntdSpace(
                                [
                                    fac.AntdButton(
                                        t__setting('保存'),
                                        id={'type': 'notify-api-server-jiang-save', 'name': api_name},
                                        type='primary',
                                    ),
                                    fac.AntdButton(
                                        t__setting('消息测试'),
                                        id={'type': 'notify-api-server-jiang-test', 'name': api_name},
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
        elif api_type == 'Gewechat':
            if params_json and (params_json := json.loads(params_json)):
                token = params_json['token']
                app_id = params_json['app_id']
                base_url = params_json['base_url']
                wxid = params_json['wxid']
            else:
                token = ''
                app_id = ''
                base_url = ''
                wxid = ''
            items.append(
                {
                    'key': api_name,
                    'label': api_name_label + f' ({t__setting(api_type)})',
                    'contextMenu': [{'key': api_name, 'label': t__setting('删除')}],
                    'children': fac.AntdSpace(
                        [
                            dcc.Store(id={'type': 'notify-api-Gewechat-api-name', 'name': api_name}, data=api_name),
                            fac.AntdDivider(api_name_label, innerTextOrientation='left'),
                            fac.AntdForm(
                                [
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-Gewechat-token', 'name': api_name}, value=token),
                                        label='token',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-Gewechat-app_id', 'name': api_name}, value=app_id),
                                        label='app_id',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-Gewechat-base_url', 'name': api_name}, value=base_url),
                                        label='base_url',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-Gewechat-wxid', 'name': api_name}, value=wxid),
                                        label='wxid',
                                    ),
                                ],
                                labelCol={'span': 5},
                                wrapperCol={'span': 20},
                            ),
                            fac.AntdSpace(
                                [
                                    fac.AntdButton(
                                        t__setting('保存'),
                                        id={'type': 'notify-api-Gewechat-save', 'name': api_name},
                                        type='primary',
                                    ),
                                    fac.AntdButton(
                                        t__setting('消息测试'),
                                        id={'type': 'notify-api-Gewechat-test', 'name': api_name},
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
        elif api_type == '企业微信群机器人':
            if params_json and (params_json := json.loads(params_json)):
                Key = params_json['Key']
            else:
                Key = ''
            items.append(
                {
                    'key': api_name,
                    'label': api_name_label + f' ({t__setting(api_type)})',
                    'contextMenu': [{'key': api_name, 'label': t__setting('删除')}],
                    'children': fac.AntdSpace(
                        [
                            dcc.Store(id={'type': 'notify-api-wecom-group-robot-api-name', 'name': api_name}, data=api_name),
                            fac.AntdDivider(api_name_label, innerTextOrientation='left'),
                            fac.AntdForm(
                                [
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-wecom-group-robot-Key', 'name': api_name}, value=Key),
                                        label='Key',
                                    ),
                                ],
                                labelCol={'span': 5},
                                wrapperCol={'span': 20},
                            ),
                            fac.AntdSpace(
                                [
                                    fac.AntdButton(
                                        t__setting('保存'),
                                        id={'type': 'notify-api-wecom-group-robot-save', 'name': api_name},
                                        type='primary',
                                    ),
                                    fac.AntdButton(
                                        t__setting('消息测试'),
                                        id={'type': 'notify-api-wecom-group-robot-test', 'name': api_name},
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
        elif api_type == '邮件SMTP协议':
            if params_json and (params_json := json.loads(params_json)):
                Host: str = params_json['Host']
                Port: str = params_json['Port']
                User: str = params_json['User']
                Password: str = params_json['Password']
                Receivers: List = params_json['Receivers']
            else:
                Host = ''
                Port = '465'
                User = ''
                Password = ''
                Receivers = ''
            items.append(
                {
                    'key': api_name,
                    'label': api_name_label + f' ({t__setting(api_type)})',
                    'contextMenu': [{'key': api_name, 'label': t__setting('删除')}],
                    'children': fac.AntdSpace(
                        [
                            dcc.Store(id={'type': 'notify-api-email-smtp-api-name', 'name': api_name}, data=api_name),
                            fac.AntdDivider(api_name_label, innerTextOrientation='left'),
                            fac.AntdForm(
                                [
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-email-smtp-Host', 'name': api_name}, value=Host),
                                        label='Host',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-email-smtp-Port', 'name': api_name}, value=Port if Port else '465'),
                                        label='Port',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-email-smtp-User', 'name': api_name}, value=User),
                                        label='User',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-email-smtp-Password', 'name': api_name}, value=Password),
                                        label='Password',
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id={'type': 'notify-api-email-smtp-Receivers', 'name': api_name}, value=Receivers),
                                        label='Receivers',
                                        tooltip=t__setting('多个邮箱按逗号分割'),
                                    ),
                                ],
                                labelCol={'span': 5},
                                wrapperCol={'span': 20},
                            ),
                            fac.AntdSpace(
                                [
                                    fac.AntdButton(
                                        t__setting('保存'),
                                        id={'type': 'notify-api-email-smtp-save', 'name': api_name},
                                        type='primary',
                                    ),
                                    fac.AntdButton(
                                        t__setting('消息测试'),
                                        id={'type': 'notify-api-email-smtp-test', 'name': api_name},
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


def get_notify_api():
    api_names = []
    api_names_enabled = []
    notify_apis = dao_notify.get_notify_api_by_name(api_name=None)
    for notify_api in notify_apis:
        api_name = notify_api.api_name
        enable = notify_api.enable
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


# 新建Server酱api
@app.callback(
    [
        Output('notify-api-edit-tabs', 'items', allow_duplicate=True),
        Output('notify-api-activate', 'options', allow_duplicate=True),
        Output('notify-api-activate', 'value', allow_duplicate=True),
    ],
    Input('notify-api-add-serverchan', 'nClicks'),
    State('notify-api-add-name', 'value'),
    prevent_initial_call=True,
)
def add_server_chan_notify_api(nClick, api_name_label):
    if not api_name_label:
        MessageManager.error(content=t__setting('请输入API名称'))
        return dash.no_update
    for i in dao_notify.get_notify_api_by_name(api_name=None):
        if api_name_value2label(i.api_name) == api_name_label:
            MessageManager.error(content=api_name_label + t__setting('已存在'))
            return dash.no_update
    dao_notify.insert_notify_api(api_name=api_name_label + f'\0{uuid4().hex[:12]}', api_type='Server酱', enable=False, params_json='{}')
    MessageManager.success(content=api_name_label + t__setting('创建成功'))
    return [get_tabs_items(), *get_notify_api()]


# 新建Gewechat api
@app.callback(
    [
        Output('notify-api-edit-tabs', 'items', allow_duplicate=True),
        Output('notify-api-activate', 'options', allow_duplicate=True),
        Output('notify-api-activate', 'value', allow_duplicate=True),
    ],
    Input('notify-api-add-Gewechat', 'nClicks'),
    State('notify-api-add-name', 'value'),
    prevent_initial_call=True,
)
def add_Gewechat_notify_api(nClick, api_name_label):
    if not api_name_label:
        MessageManager.error(content=t__setting('请输入API名称'))
        return dash.no_update
    for i in dao_notify.get_notify_api_by_name(api_name=None):
        if api_name_value2label(i.api_name) == api_name_label:
            MessageManager.error(content=api_name_label + t__setting('已存在'))
            return dash.no_update
    dao_notify.insert_notify_api(api_name=api_name_label + f'\0{uuid4().hex[:12]}', api_type='Gewechat', enable=False, params_json='{}')
    MessageManager.success(content=api_name_label + t__setting('创建成功'))
    return [get_tabs_items(), *get_notify_api()]


# 新建企业微信群机器人api
@app.callback(
    [
        Output('notify-api-edit-tabs', 'items', allow_duplicate=True),
        Output('notify-api-activate', 'options', allow_duplicate=True),
        Output('notify-api-activate', 'value', allow_duplicate=True),
    ],
    Input('notify-api-add-wecom-group-robot', 'nClicks'),
    State('notify-api-add-name', 'value'),
    prevent_initial_call=True,
)
def add_wecom_group_robot_notify_api(nClick, api_name_label):
    if not api_name_label:
        MessageManager.error(content=t__setting('请输入API名称'))
        return dash.no_update
    for i in dao_notify.get_notify_api_by_name(api_name=None):
        if api_name_value2label(i.api_name) == api_name_label:
            MessageManager.error(content=api_name_label + t__setting('已存在'))
            return dash.no_update
    dao_notify.insert_notify_api(api_name=api_name_label + f'\0{uuid4().hex[:12]}', api_type='企业微信群机器人', enable=False, params_json='{}')
    MessageManager.success(content=api_name_label + t__setting('创建成功'))
    return [get_tabs_items(), *get_notify_api()]


# 新建邮箱API
@app.callback(
    [
        Output('notify-api-edit-tabs', 'items', allow_duplicate=True),
        Output('notify-api-activate', 'options', allow_duplicate=True),
        Output('notify-api-activate', 'value', allow_duplicate=True),
    ],
    Input('notify-api-add-email-smtp', 'nClicks'),
    State('notify-api-add-name', 'value'),
    prevent_initial_call=True,
)
def add_email_smtp_notify_api(nClick, api_name_label):
    if not api_name_label:
        MessageManager.error(content=t__setting('请输入API名称'))
        return dash.no_update
    for i in dao_notify.get_notify_api_by_name(api_name=None):
        if api_name_value2label(i.api_name) == api_name_label:
            MessageManager.error(content=api_name_label + t__setting('已存在'))
            return dash.no_update
    dao_notify.insert_notify_api(api_name=api_name_label + f'\0{uuid4().hex[:12]}', api_type='邮件SMTP协议', enable=False, params_json='{}')
    MessageManager.success(content=api_name_label + t__setting('创建成功'))
    return [get_tabs_items(), *get_notify_api()]


@app.callback(
    [
        Output('notify-api-edit-tabs', 'items', allow_duplicate=True),
        Output('notify-api-activate', 'options', allow_duplicate=True),
        Output('notify-api-activate', 'value', allow_duplicate=True),
    ],
    Input('notify-api-activate', 'value'),
    State('notify-api-activate', 'options'),
    prevent_initial_call=True,
)
def enable_notify_api(enables, options):
    for option in options:
        api_name = option['value']
        if api_name in enables:
            dao_notify.modify_enable(api_name=api_name, enable=True)
        else:
            dao_notify.modify_enable(api_name=api_name, enable=False)
    return [get_tabs_items(), *get_notify_api()]


# server酱保存回调
@app.callback(
    Output({'type': 'notify-api-server-jiang-save', 'name': MATCH}, 'id'),
    Input({'type': 'notify-api-server-jiang-save', 'name': MATCH}, 'nClicks'),
    [
        State({'type': 'notify-api-server-jiang-SendKey', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-server-jiang-Noip', 'name': MATCH}, 'checked'),
        State({'type': 'notify-api-server-jiang-Channel', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-server-jiang-Openid', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-server-jiang-api-name', 'name': MATCH}, 'data'),
    ],
    prevent_initial_call=True,
)
def save_server_jiang_api(nClick, SendKey, Noip, Channel, Openid, api_name):
    values = dict(
        SendKey=SendKey,
        Noip=Noip,
        Channel=Channel,
        Openid=Openid,
    )
    api_name_label = api_name_value2label(api_name)
    dao_notify.delete_notify_api_by_name(api_name=api_name)
    if dao_notify.insert_notify_api(api_name=api_name, api_type='Server酱', enable=True, params_json=json.dumps(values)):
        MessageManager.success(content=api_name_label + t__setting('配置保存成功'))
    else:
        MessageManager.error(content=api_name_label + t__setting('配置保存失败'))
    return dash.no_update


# server酱测试通道
@app.callback(
    Output({'type': 'notify-api-server-jiang-test', 'name': MATCH}, 'id'),
    Input({'type': 'notify-api-server-jiang-test', 'name': MATCH}, 'nClicks'),
    [
        State({'type': 'notify-api-server-jiang-SendKey', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-server-jiang-Noip', 'name': MATCH}, 'checked'),
        State({'type': 'notify-api-server-jiang-Channel', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-server-jiang-Openid', 'name': MATCH}, 'value'),
    ],
    prevent_initial_call=True,
)
def test_server_jiang_api(nClicks, SendKey, Noip, Channel, Openid):
    is_ok, rt = server_jiang.send_notify(
        SendKey=SendKey,
        Noip=Noip,
        Channel=Channel,
        title=t__setting('测试'),
        desp=t__setting('这是一条测试消息，用于验证推送功能。'),
        Openid=Openid,
    )
    if is_ok:
        MessageManager.success(content=t__setting('Server酱测试发送成功'))
        # pushid = rt['pushid']
        # readkey = rt['readkey']
        # time.sleep(5)
        # is_ok_test, rt_test = server_jiang.is_send_success(pushid, readkey)
        # if is_ok_test:
        #     MessageManager.success(content=t__setting('Server酱测试发送成功'))
        # else:
        #     MessageManager.error(content=t__setting('消息加入Server酱队列成功，但可能未发送成功') + 'ERROR:' + str(rt_test))
    else:
        MessageManager.error(content=t__setting('Server酱测试发送失败') + 'ERROR:' + str(rt))
    return dash.no_update


# Gewechat测试通道
@app.callback(
    Output({'type': 'notify-api-Gewechat-test', 'name': MATCH}, 'id'),
    Input({'type': 'notify-api-Gewechat-test', 'name': MATCH}, 'nClicks'),
    [
        State({'type': 'notify-api-Gewechat-token', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-Gewechat-app_id', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-Gewechat-base_url', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-Gewechat-wxid', 'name': MATCH}, 'value'),
    ],
    prevent_initial_call=True,
)
def test_Gewechat_api(nClicks, token, app_id, base_url, wxid):
    is_ok, rt = gewechat.send_notify(
        token=token,
        app_id=app_id,
        base_url=base_url,
        title=t__setting('测试'),
        wxid=wxid,
        desp=t__setting('这是一条测试消息，用于验证推送功能。'),
    )
    if is_ok:
        MessageManager.success(content=t__setting('Gewechat测试发送成功'))
    else:
        MessageManager.error(content=t__setting('Gewechat测试发送失败') + 'ERROR:' + str(rt))
    return dash.no_update


# Gewechat保存回调
@app.callback(
    Output({'type': 'notify-api-Gewechat-save', 'name': MATCH}, 'id'),
    Input({'type': 'notify-api-Gewechat-save', 'name': MATCH}, 'nClicks'),
    [
        State({'type': 'notify-api-Gewechat-token', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-Gewechat-app_id', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-Gewechat-base_url', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-Gewechat-wxid', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-Gewechat-api-name', 'name': MATCH}, 'data'),
    ],
    prevent_initial_call=True,
)
def save_Gewechat_api(nClick, token, app_id, base_url, wxid, api_name):
    values = dict(token=token, app_id=app_id, base_url=base_url, wxid=wxid)
    api_name_label = api_name_value2label(api_name)
    dao_notify.delete_notify_api_by_name(api_name=api_name)
    if dao_notify.insert_notify_api(api_name=api_name, api_type='Gewechat', enable=True, params_json=json.dumps(values)):
        MessageManager.success(content=api_name_label + t__setting('配置保存成功'))
    else:
        MessageManager.error(content=api_name_label + t__setting('配置保存失败'))
    return dash.no_update


# 企业微信群机器人保存回调
@app.callback(
    Output({'type': 'notify-api-wecom-group-robot-save', 'name': MATCH}, 'id'),
    Input({'type': 'notify-api-wecom-group-robot-save', 'name': MATCH}, 'nClicks'),
    [
        State({'type': 'notify-api-wecom-group-robot-Key', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-wecom-group-robot-api-name', 'name': MATCH}, 'data'),
    ],
    prevent_initial_call=True,
)
def save_wecom_group_robot_api(nClick, Key, api_name):
    values = dict(Key=Key)
    api_name_label = api_name_value2label(api_name)
    dao_notify.delete_notify_api_by_name(api_name=api_name)
    if dao_notify.insert_notify_api(api_name=api_name, api_type='企业微信群机器人', enable=True, params_json=json.dumps(values)):
        MessageManager.success(content=api_name_label + t__setting('配置保存成功'))
    else:
        MessageManager.error(content=api_name_label + t__setting('配置保存失败'))
    return dash.no_update


# 企业微信群机器人测试通道
@app.callback(
    Output({'type': 'notify-api-wecom-group-robot-test', 'name': MATCH}, 'id'),
    Input({'type': 'notify-api-wecom-group-robot-test', 'name': MATCH}, 'nClicks'),
    State({'type': 'notify-api-wecom-group-robot-Key', 'name': MATCH}, 'value'),
    prevent_initial_call=True,
)
def test_wecom_group_robot_api(nClicks, Key):
    is_ok, rt = enterprise_wechat.wechat_text(
        title=t__setting('测试'),
        content=t__setting('这是一条测试消息，用于验证推送功能。'),
        key=Key,
    )
    if is_ok:
        MessageManager.success(content=t__setting('企业微信群机器人测试发送成功'))
    else:
        MessageManager.error(content=t__setting('企业微信群机器人测试发送失败') + 'ERROR:' + str(rt))
    return dash.no_update


# 邮件SMTP协议保存回调
@app.callback(
    Output({'type': 'notify-api-email-smtp-save', 'name': MATCH}, 'id'),
    Input({'type': 'notify-api-email-smtp-save', 'name': MATCH}, 'nClicks'),
    [
        State({'type': 'notify-api-email-smtp-Host', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-email-smtp-Port', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-email-smtp-User', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-email-smtp-Password', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-email-smtp-Receivers', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-email-smtp-api-name', 'name': MATCH}, 'data'),
    ],
    prevent_initial_call=True,
)
def save_email_smtp_api(nClick, Host, Port, User, Password, Receivers, api_name):
    values = dict(Host=Host, Port=Port, User=User, Password=Password, Receivers=Receivers)
    api_name_label = api_name_value2label(api_name)
    dao_notify.delete_notify_api_by_name(api_name=api_name)
    if dao_notify.insert_notify_api(api_name=api_name, api_type='邮件SMTP协议', enable=True, params_json=json.dumps(values)):
        MessageManager.success(content=api_name_label + t__setting('配置保存成功'))
    else:
        MessageManager.error(content=api_name_label + t__setting('配置保存失败'))
    return dash.no_update


# 邮件SMTP协议测试通道
@app.callback(
    Output({'type': 'notify-api-email-smtp-test', 'name': MATCH}, 'id'),
    Input({'type': 'notify-api-email-smtp-test', 'name': MATCH}, 'nClicks'),
    [
        State({'type': 'notify-api-email-smtp-Host', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-email-smtp-Port', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-email-smtp-User', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-email-smtp-Password', 'name': MATCH}, 'value'),
        State({'type': 'notify-api-email-smtp-Receivers', 'name': MATCH}, 'value'),
    ],
    prevent_initial_call=True,
)
def test_email_smtp_api(nClicks, Host, Port, User, Password, Receivers):
    is_ok, rt = email_smtp.send_mail(
        host=Host,
        port=Port,
        user=User,
        password=Password,
        receivers=Receivers.split(','),
        title=t__setting('测试'),
        content=t__setting('这是一条测试消息，用于验证推送功能。'),
    )
    if is_ok:
        MessageManager.success(content=t__setting('邮件SMTP协议测试发送成功'))
    else:
        MessageManager.error(content=t__setting('邮件SMTP协议测试发送失败') + 'ERROR:' + str(rt))
    return dash.no_update


# 删除通知渠道
@app.callback(
    [
        Output('notify-api-edit-tabs', 'items', allow_duplicate=True),
        Output('notify-api-activate', 'options', allow_duplicate=True),
        Output('notify-api-activate', 'value', allow_duplicate=True),
    ],
    Input('notify-api-edit-tabs', 'clickedContextMenu'),
    prevent_initial_call=True,
)
def delete_notify_channel(clickedContextMenu):
    api_name = clickedContextMenu['tabKey']
    api_name_label = api_name_value2label(api_name)
    if dao_notify.delete_notify_api_by_name(api_name=api_name):
        MessageManager.success(content=api_name_label + t__setting('删除成功'))
    else:
        MessageManager.error(content=api_name_label + t__setting('删除失败'))
    return [get_tabs_items(), *get_notify_api()]
