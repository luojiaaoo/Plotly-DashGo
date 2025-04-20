from . import email_imap
from database.sql_db.dao.dao_listen import get_listen_api_by_name
from database.sql_db.dao.dao_listen_task import get_activa_listen_job
from common.utilities.util_logger import Log
from typing import List, Dict
import json
from datetime import datetime, timedelta

logger = Log.get_logger('active_listen_task')


def active_listen(shared_datetime):
    last_datetime = shared_datetime.get('last_datetime')
    end_datetime = datetime.now()
    shared_datetime['last_datetime'] = end_datetime
    mapping_listen_job: Dict[str, List] = {}
    for activa_listen_job in get_activa_listen_job(job_id=None):
        if not activa_listen_job.status:
            continue
        listen_channels = json.loads(activa_listen_job.listen_channels)
        for listen_channel in listen_channels:
            if listen_channel not in mapping_listen_job:
                mapping_listen_job[listen_channel] = []
            else:
                mapping_listen_job[listen_channel].append(
                    dict(
                        job_id=activa_listen_job.job_id,
                        listen_keyword=activa_listen_job.listen_keyword,
                        type=activa_listen_job.type,
                        script_text=activa_listen_job.script_text,
                        script_type=activa_listen_job.script_type,
                        notify_channels=activa_listen_job.notify_channels,
                        extract_names=activa_listen_job.extract_names,
                        timeout=activa_listen_job.timeout,
                        host=activa_listen_job.host,
                        port=activa_listen_job.port,
                        username=activa_listen_job.username,
                        password=activa_listen_job.password,
                    )
                )
    for listen_api in get_listen_api_by_name(job_id=None):
        if not listen_api.enable:
            continue
        api_name = listen_api.api_name
        api_type = listen_api.api_type
        params_json = json.loads(listen_api.params_json)
        if api_type == '邮件IMAP协议':
            if mapping_listen_job.get(api_name, None) is None:  # 都不需要检测这个通道
                continue
            if not listen_api.params_json:
                logger.error(f'{api_name}的接口未配置')
                continue
            imap_server = params_json['imap_server']
            port = params_json['port']
            email_account = params_json['email_account']
            password = params_json['password']
            emails = email_imap.get_email_context_from_subject_during(
                imap_server=imap_server,
                port=int(port),
                emal_account=email_account,
                password=password,
                subjects=[i['listen_keyword'] for i in mapping_listen_job[api_name]],
                since_time=last_datetime,
                before_time=end_datetime,
            )
            for email in emails:
                ...
                
