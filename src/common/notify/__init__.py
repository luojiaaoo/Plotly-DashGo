from . import server_jiang, enterprise_wechat, email_smtp
from database.sql_db.dao.dao_notify import get_notify_api_by_name
from common.utilities.util_logger import Log
from typing import List


__all__ = [
    'send_notify',
]

logger = Log.get_logger('send_notify')


def send_text_notify(title: str, short: str, desp: str, notify_channels: List):
    import json

    for notify_api in get_notify_api_by_name(api_name=None):
        if not notify_api.enable:
            continue
        api_name = notify_api.api_name
        api_type = notify_api.api_type
        params_json = json.loads(notify_api.params_json)
        if api_type == 'Server酱' and api_name in notify_channels:
            if not notify_api.params_json:
                logger.error(f'{api_name}的SendKey未配置')
                continue
            server_jiang_json = params_json
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
        elif api_type == '企业微信群机器人' and api_name in notify_channels:
            if not notify_api.params_json:
                logger.error(f'{api_name}的Key未配置')
                continue
            Key = params_json['Key']
            is_ok, rt = enterprise_wechat.wechat_text(
                title=title,
                content=desp,
                key=Key,
            )
            if not is_ok:
                logger.error(f'发送{api_name}通知失败，错误信息：{rt}')
        elif api_type == '邮件SMTP协议' and api_name in notify_channels:
            if not notify_api.params_json:
                logger.error(f'{api_name}的Key未配置')
                continue
            Host = params_json['Host']
            Port = params_json['Port']
            User = params_json['User']
            Password = params_json['Password']
            Receivers = params_json['Receivers']
            is_ok, rt = email_smtp.send_mail(
                host=Host,
                port=Port,
                user=User,
                password=Password,
                receivers=Receivers.split(','),
                title=title,
                content=desp,
            )
            if not is_ok:
                logger.error(f'发送{api_name}通知失败，错误信息：{rt}')
