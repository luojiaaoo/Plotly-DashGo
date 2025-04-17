from . import server_jiang
from database.sql_db.dao.dao_notify import api_names, get_notify_api_by_name
from common.utilities.util_logger import Log
from typing import List


__all__ = [
    'send_notify',
]

logger = Log.get_logger('send_notify')


def send_text_notify(title: str, short: str, desp: str, notify_channels: List):
    import json

    for api_name in api_names:
        if api_name in ('Server酱', 'Server酱-No2') and api_name in notify_channels:
            notify_api = get_notify_api_by_name(api_name=api_name)
            if notify_api and notify_api.enable:
                if not notify_api.params_json:
                    logger.error(f'{api_name}的SendKey未配置')
                    continue
                server_jiang_json = json.loads(notify_api.params_json)
                SendKey = server_jiang_json['SendKey']
                Noip = server_jiang_json['Noip']
                Channel = server_jiang_json['Channel']
                Openid = server_jiang_json['Openid']
                is_ok, rt = server_jiang.send_notify(
                    SendKey=SendKey,
                    Noip=Noip,
                    Channel=Channel,
                    title=title,
                    desp=desp,
                    short=short,
                    Openid=Openid,
                )
                if not is_ok:
                    logger.error(f'发送{api_name}通知失败，错误信息：{rt}')
