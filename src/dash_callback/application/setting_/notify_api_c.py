from dash.dependencies import Input, Output, State
from server import app
import feffery_antd_components as fac
from dash_components import MessageManager
from database.sql_db.dao import dao_notify
import json
import time
from common.notify.server_jiang import send_notify, is_send_success
from i18n import t__setting


def get_tabs_items():
    items = []
    # server酱配置
    server_jiang = dao_notify.get_notify_api_by_name(api_name='Server酱')
    if server_jiang is not None:
        server_jiang_json = json.loads(server_jiang.params_json)
        SendKey = server_jiang_json['SendKey']
        Noip = server_jiang_json['Noip']
        Channel = server_jiang_json['Channel']
        Openid = server_jiang_json['Openid']
    else:
        SendKey, Noip, Channel, Openid = '', True, '', ''
    items.append(
        {
            'key': 'Server酱',
            'label': 'Server酱',
            'children': fac.AntdSpace(
                [
                    fac.AntdDivider('Server酱', innerTextOrientation='left'),
                    fac.AntdForm(
                        [
                            fac.AntdFormItem(fac.AntdInput(id='notify-server-jiang-SendKey', value=SendKey), label='SendKey'),
                            fac.AntdFormItem(fac.AntdSwitch(id='notify-server-jiang-Noip', checked=Noip), label='Noip', tooltip='是否隐藏IP'),
                            fac.AntdFormItem(fac.AntdInput(id='notify-server-jiang-Channel', value=Channel), label='Channel', tooltip='发送通道'),
                            fac.AntdFormItem(fac.AntdInput(id='notify-server-jiang-Openid', value=Openid), label='Openid', tooltip='只有测试号和企业微信应用消息需要填写'),
                        ],
                        labelCol={'span': 5},
                        wrapperCol={'span': 20},
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdButton(t__setting('保存'), id='notify-api-server-jiang-save', type='primary'),
                            fac.AntdButton(t__setting('消息测试'), id='notify-api-server-jiang-test', type='default'),
                        ],
                    ),
                    fac.AntdButton(
                        '💕' + t__setting('一天1毛钱的极简微信等消息接口，点击此处购买Server酱消息推送') + '💕',
                        variant='dashed',
                        color='primary',
                        href='https://sct.ftqq.com/r/16293',
                        target='_blank',
                    ),
                ],
                direction='vertical',
            ),
        }
    )
    # Server酱-No2配置
    server_jiang = dao_notify.get_notify_api_by_name(api_name='Server酱-No2')
    if server_jiang is not None:
        server_jiang_json = json.loads(server_jiang.params_json)
        SendKey = server_jiang_json['SendKey']
        Noip = server_jiang_json['Noip']
        Channel = server_jiang_json['Channel']
        Openid = server_jiang_json['Openid']
    else:
        SendKey, Noip, Channel, Openid = '', True, '', ''
    items.append(
        {
            'key': 'Server酱-No2',
            'label': 'Server酱-No2',
            'children': fac.AntdSpace(
                [
                    fac.AntdDivider('Server酱-No2', innerTextOrientation='left'),
                    fac.AntdForm(
                        [
                            fac.AntdFormItem(fac.AntdInput(id='notify-server-jiang-no2-SendKey', value=SendKey), label='SendKey'),
                            fac.AntdFormItem(fac.AntdSwitch(id='notify-server-jiang-no2-Noip', checked=Noip), label='Noip', tooltip='是否隐藏IP'),
                            fac.AntdFormItem(fac.AntdInput(id='notify-server-jiang-no2-Channel', value=Channel), label='Channel', tooltip='发送通道'),
                            fac.AntdFormItem(fac.AntdInput(id='notify-server-jiang-no2-Openid', value=Openid), label='Openid', tooltip='只有测试号和企业微信应用消息需要填写'),
                        ],
                        labelCol={'span': 5},
                        wrapperCol={'span': 20},
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdButton(t__setting('保存'), id='notify-api-server-jiang-no2-save', type='primary'),
                            fac.AntdButton(t__setting('消息测试'), id='notify-api-server-jiang-no2-test', type='default'),
                        ],
                    ),
                    fac.AntdButton(
                        '💕' + t__setting('一天1毛钱的极简微信等消息接口，点击此处购买Server酱消息推送') + '💕',
                        variant='dashed',
                        color='primary',
                        href='https://sct.ftqq.com/r/16293',
                        target='_blank',
                    ),
                ],
                direction='vertical',
            ),
        }
    )
    return items


def get_notify_api_activate():
    no_config = []
    enables = []
    for api_name in dao_notify.api_names:
        rt = dao_notify.get_notify_api_by_name(api_name=api_name)
        if rt is None:
            no_config.append(api_name)
        elif rt.enable:
            enables.append(api_name)
        else:
            pass
    return [
        {
            'label': api_name,
            'value': api_name,
            'disabled': api_name in no_config,
        }
        for api_name in dao_notify.api_names
    ], enables


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
    return [get_tabs_items(), *get_notify_api_activate()]


# server酱保存回调
@app.callback(
    [
        Output('notify-api-edit-tabs', 'items', allow_duplicate=True),
        Output('notify-api-activate', 'options', allow_duplicate=True),
        Output('notify-api-activate', 'value', allow_duplicate=True),
    ],
    Input('notify-api-server-jiang-save', 'nClicks'),
    [
        State('notify-server-jiang-SendKey', 'value'),
        State('notify-server-jiang-Noip', 'checked'),
        State('notify-server-jiang-Channel', 'value'),
        State('notify-server-jiang-Openid', 'value'),
    ],
    prevent_initial_call=True,
)
def save_server_jiang_api(nClick, SendKey, Noip, Channel, Openid):
    import json

    name = 'Server酱'
    values = dict(
        SendKey=SendKey,
        Noip=Noip,
        Channel=Channel,
        Openid=Openid,
    )
    dao_notify.delete_notify_api_by_name(api_name=name)
    if dao_notify.insert_notify_api(api_name=name, enable=True, params_json=json.dumps(values)):
        MessageManager.success(content=name + t__setting('配置保存成功'))
    else:
        MessageManager.error(content=name + t__setting('配置保存失败'))
    return [get_tabs_items(), *get_notify_api_activate()]


# server酱测试通道
@app.callback(
    Input('notify-api-server-jiang-test', 'nClicks'),
    [
        State('notify-server-jiang-SendKey', 'value'),
        State('notify-server-jiang-Noip', 'checked'),
        State('notify-server-jiang-Channel', 'value'),
        State('notify-server-jiang-Openid', 'value'),
    ],
    prevent_initial_call=True,
)
def test_server_jiang_api(nClick, SendKey, Noip, Channel, Openid):
    is_ok, rt = send_notify(
        SendKey=SendKey,
        Noip=Noip,
        Channel=Channel,
        title=t__setting('测试'),
        desp=t__setting('这是一条测试消息，用于验证推送功能。'),
        Openid=Openid,
    )
    if is_ok:
        pushid = rt['pushid']
        readkey = rt['readkey']
        time.sleep(5)
        is_ok_test, rt_test = is_send_success(pushid, readkey)
        if is_ok_test:
            MessageManager.success(content=t__setting('Server酱测试发送成功'))
        else:
            MessageManager.error(content=t__setting('消息加入Server酱队列成功，但可能未发送成功') + 'ERROR:' + str(rt_test))
    else:
        MessageManager.error(content=t__setting('Server酱测试发送失败') + 'ERROR:' + str(rt))


# server酱-No2保存回调
@app.callback(
    [
        Output('notify-api-edit-tabs', 'items', allow_duplicate=True),
        Output('notify-api-activate', 'options', allow_duplicate=True),
        Output('notify-api-activate', 'value', allow_duplicate=True),
    ],
    Input('notify-api-server-jiang-no2-save', 'nClicks'),
    [
        State('notify-server-jiang-no2-SendKey', 'value'),
        State('notify-server-jiang-no2-Noip', 'checked'),
        State('notify-server-jiang-no2-Channel', 'value'),
        State('notify-server-jiang-no2-Openid', 'value'),
    ],
    prevent_initial_call=True,
)
def save_server_jiang_no2_api(nClick, SendKey, Noip, Channel, Openid):
    import json

    name = 'Server酱-No2'
    values = dict(
        SendKey=SendKey,
        Noip=Noip,
        Channel=Channel,
        Openid=Openid,
    )
    dao_notify.delete_notify_api_by_name(api_name=name)
    if dao_notify.insert_notify_api(api_name=name, enable=True, params_json=json.dumps(values)):
        MessageManager.success(content=name + t__setting('配置保存成功'))
    else:
        MessageManager.error(content=name + t__setting('配置保存失败'))
    return [get_tabs_items(), *get_notify_api_activate()]


# server酱测试通道
@app.callback(
    Input('notify-api-server-jiang-no2-test', 'nClicks'),
    [
        State('notify-server-jiang-no2-SendKey', 'value'),
        State('notify-server-jiang-no2-Noip', 'checked'),
        State('notify-server-jiang-no2-Channel', 'value'),
        State('notify-server-jiang-no2-Openid', 'value'),
    ],
    prevent_initial_call=True,
)
def test_server_jiang_no2_api(nClick, SendKey, Noip, Channel, Openid):
    is_ok, rt = send_notify(
        SendKey=SendKey,
        Noip=Noip,
        Channel=Channel,
        title=t__setting('测试'),
        desp=t__setting('这是一条测试消息，用于验证推送功能。'),
        Openid=Openid,
    )
    if is_ok:
        pushid = rt['pushid']
        readkey = rt['readkey']
        time.sleep(5)
        is_ok_test, rt_test = is_send_success(pushid, readkey)
        if is_ok_test:
            MessageManager.success(content=t__setting('Server酱测试发送成功'))
        else:
            MessageManager.error(content=t__setting('消息加入Server酱队列成功，但可能未发送成功') + 'ERROR:' + str(rt_test))
    else:
        MessageManager.error(content=t__setting('Server酱测试发送失败') + 'ERROR:' + str(rt))
