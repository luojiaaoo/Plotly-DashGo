from dash.dependencies import Input, Output, State, MATCH
from server import app
import feffery_antd_components as fac
from dash_components import MessageManager
from database.sql_db.dao import dao_notify
import dash
from uuid import uuid4
from dash import dcc
import json
import time
import json
from common.notify.server_jiang import send_notify, is_send_success
from feffery_dash_utils.style_utils import style
from i18n import t__setting


def api_name_value2label(api_name: str):
    return api_name.split('***', 1)[0]


def get_tabs_items():
    items = []
    # server酱配置
    notify_apis = dao_notify.get_notify_api_by_name(api_name=None)
    for notify_api in notify_apis:
        api_type = notify_api.api_type
        if api_type not in dao_notify.support_api_types:
            raise Exception(f'不支持{api_type}类型的消息推送')
        api_name = notify_api.api_name
        label_api_name = api_name_value2label(api_name)
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
                    'label': label_api_name + f' ({t__setting(api_type)})',
                    'children': fac.AntdSpace(
                        [
                            dcc.Store(id={'type': 'notify-api-server-jiang-api-name', 'name': api_name}),
                            fac.AntdDivider(label_api_name, innerTextOrientation='left'),
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
        elif api_type == '企业微信群机器人':
            if params_json and (params_json := json.loads(params_json)):
                Key = params_json['Key']
            else:
                Key = ''
            items.append(
                {
                    'key': api_name,
                    'label': label_api_name + f' ({t__setting(api_type)})',
                    'children': fac.AntdSpace(
                        [
                            dcc.Store(id={'type': 'notify-api-wecom-group-robot-api-name', 'name': api_name}),
                            fac.AntdDivider(label_api_name, innerTextOrientation='left'),
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
    return items


def get_notify_api():
    api_names = []
    api_names_enabled = []
    for notify_api in dao_notify.get_notify_api_by_name(api_name=None):
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
    for i in dao_notify.get_notify_api_by_name(api_name=None):
        if api_name_value2label(i.api_name) == api_name_label:
            MessageManager.error(content=api_name_label + t__setting('已存在'))
            return dash.no_update
    dao_notify.insert_notify_api(api_name=api_name_label + f'***{uuid4().hex}', api_type='Server酱', enable=False, params_json='{}')
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
    for i in dao_notify.get_notify_api_by_name(api_name=None):
        if api_name_value2label(i.api_name) == api_name_label:
            MessageManager.error(content=api_name_label + t__setting('已存在'))
            return dash.no_update
    dao_notify.insert_notify_api(api_name=api_name_label + f'***{uuid4().hex}', api_type='企业微信群机器人', enable=False, params_json='{}')
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
# @app.callback(
#     Input({'type': 'notify-api-server-jiang-save', 'name': MATCH}, 'nClicks'),
#     [
#         State({'type': 'notify-api-server-jiang-SendKey', 'name': MATCH}, 'value'),
#         State({'type': 'notify-api-server-jiang-Noip', 'name': MATCH}, 'checked'),
#         State({'type': 'notify-api-server-jiang-Channel', 'name': MATCH}, 'value'),
#         State({'type': 'notify-api-server-jiang-Openid', 'name': MATCH}, 'value'),
#         State({'type': 'notify-api-server-jiang-api-name', 'name': MATCH}, 'data'),
#     ],
#     prevent_initial_call=True,
# )
# def save_server_jiang_api(nClick, SendKey, Noip, Channel, Openid, api_name):
#     print(SendKey, Noip, Channel, Openid, api_name)
    # name = 'Server酱'
    # values = dict(
    #     SendKey=SendKey,
    #     Noip=Noip,
    #     Channel=Channel,
    #     Openid=Openid,
    # )
    # dao_notify.delete_notify_api_by_name(api_name=name)
    # if dao_notify.insert_notify_api(api_name=name, enable=True, params_json=json.dumps(values)):
    #     MessageManager.success(content=name + t__setting('配置保存成功'))
    # else:
    #     MessageManager.error(content=name + t__setting('配置保存失败'))


# # server酱测试通道
# @app.callback(
#     Input('notify-api-server-jiang-test', 'nClicks'),
#     [
#         State('notify-server-jiang-SendKey', 'value'),
#         State('notify-server-jiang-Noip', 'checked'),
#         State('notify-server-jiang-Channel', 'value'),
#         State('notify-server-jiang-Openid', 'value'),
#     ],
#     prevent_initial_call=True,
# )
# def test_server_jiang_api(nClick, SendKey, Noip, Channel, Openid):
#     is_ok, rt = send_notify(
#         SendKey=SendKey,
#         Noip=Noip,
#         Channel=Channel,
#         title=t__setting('测试'),
#         desp=t__setting('这是一条测试消息，用于验证推送功能。'),
#         Openid=Openid,
#     )
#     if is_ok:
#         pushid = rt['pushid']
#         readkey = rt['readkey']
#         time.sleep(5)
#         is_ok_test, rt_test = is_send_success(pushid, readkey)
#         if is_ok_test:
#             MessageManager.success(content=t__setting('Server酱测试发送成功'))
#         else:
#             MessageManager.error(content=t__setting('消息加入Server酱队列成功，但可能未发送成功') + 'ERROR:' + str(rt_test))
#     else:
#         MessageManager.error(content=t__setting('Server酱测试发送失败') + 'ERROR:' + str(rt))
