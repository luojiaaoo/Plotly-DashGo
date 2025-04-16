import requests
from common.constant import HttpStatusConstant
from config.dashgo_conf import ShowConf


def send_notify(SendKey, Noip, Channel, title, desp, short=None, Openid=None):
    if short and len(short) > 64:
        short = short[:64]
    url = f'https://sctapi.ftqq.com/{SendKey}.send'
    data = {
        'title': title + f'[from {ShowConf.APP_NAME}]',
        'desp': desp,
        **({'short': short} if short else {'short': desp[:64]}),
        **({'Noip': 1} if Noip else {}),
        'channel': Channel,
        **({'openid': Openid} if Openid else {}),
    }
    response = requests.post(url, data=data)
    # {'code': 0, 'message': '', 'data': {'pushid': '198288704', 'readkey': 'SCT0UbSug2AZx8w', 'error': 'SUCCESS', 'errno': 0}}
    result = response.json()

    if response.status_code == HttpStatusConstant.SUCCESS and result.get('code') == 0:
        pushid = result.get('data', {}).get('pushid')
        readkey = result.get('data', {}).get('readkey')
        return True, {'pushid': pushid, 'readkey': readkey}
    else:
        return False, result


def is_send_success(pushid, readkey):
    status_url = f'https://sctapi.ftqq.com/push?id={pushid}&readkey={readkey}'
    status_response = requests.get(status_url)
    status_result = status_response.json()
    # {'code': 0, 'message': '', 'data': {'id': 198289285, 'uid': '156502', 'title': '[2/5]测试', 'desp': '这是一条测试消息，用于验证推送功能。\r\n\r\n\r\n\r\n今日免费额度:2/5 · [可访问 sct.ftqq.com 购买或续期订阅会员](https://sct.ftqq.com/donate)', 'encoded': '', 'readkey': 'SCT1hfWc0v1o0O1', 'wxstatus': '{"errcode":0,"errmsg":"ok","msgid":3945301017750585345}', 'ip': '', 'created_at': '2025-04-16T04:55:35+08:00', 'updated_at': '2025-04-16T04:55:35+08:00'}}
    if status_response.status_code == HttpStatusConstant.SUCCESS and status_result.get('code') == 0:
        return True, status_result
    else:
        return False, status_result
