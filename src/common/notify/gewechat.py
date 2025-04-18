import requests
from common.constant import HttpStatusConstant
from config.dashgo_conf import ShowConf


def send_notify(token, app_id, base_url, title, wxid, desp):
    url = f'{base_url}/message/postText'
    data = {'appId': app_id, 'toWxid': wxid, 'content': (title + f'【from {ShowConf.APP_NAME}】' + '\n' + desp)[:1200]}
    headers = {
        'X-GEWE-TOKEN': token,
        'Content-Type': 'application/json',
    }
    response = requests.post(url, json=data, headers=headers)
    result = response.json()

    if response.status_code == HttpStatusConstant.SUCCESS and result.get('msg') == '操作成功':
        return True, result
    else:
        return False, result
