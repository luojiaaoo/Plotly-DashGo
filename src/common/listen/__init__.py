from . import email_pop3
from database.sql_db.dao.dao_listen import get_listen_api_by_name
from database.sql_db.dao.dao_listen_task import get_activa_listen_job
from common.utilities.util_logger import Log
from typing import List, Dict
import json
from datetime import datetime, timedelta
from common.utilities.util_apscheduler import add_ssh_date_job, add_local_date_job

logger = Log.get_logger('active_listen_task')


def email_to_run_date_job(email, jobs):
    title = email['subject']
    datetime_ = email['datetime'].astimezone().strftime('%Y-%m-%dT%H:%M:%S')
    from_ = email['from']
    desp = email['context']
    env_vars = {'__title__': title, '__from__': from_, '__desp__': desp, '__datetime__': datetime_}
    for job in jobs:
        if job['listen_keyword'] in title:
            logger.info(f'{email["subject"]}符合{job["job_id"]}的关键词检测正在发起任务')
            if job['type'] == 'ssh':
                add_ssh_date_job(
                    host=job['host'],
                    port=job['port'],
                    username=job['username'],
                    password=job['password'],
                    script_text=job['script_text'],
                    script_type=job['script_type'],
                    timeout=job['timeout'],
                    job_id=job['job_id'],
                    extract_names=job['extract_names'],
                    notify_channels=job['notify_channels'],
                    env_vars=json.dumps(env_vars),
                )
            elif job['type'] == 'local':
                add_local_date_job(
                    script_text=job['script_text'],
                    script_type=job['script_type'],
                    timeout=job['timeout'],
                    job_id=job['job_id'],
                    extract_names=job['extract_names'],
                    notify_channels=job['notify_channels'],
                    env_vars=json.dumps(env_vars),
                )
            else:
                logger.error(f'不支持的类型运行类型: {job["type"]}')
                continue
            logger.info(f'{job["job_id"]}任务已发起')


def active_listen(shared_datetime):
    last_datetime = shared_datetime.get('last_datetime')
    end_datetime = datetime.now().astimezone()
    shared_datetime['last_datetime'] = end_datetime
    logger.info(f'上次时间: {last_datetime} 当前时间: {end_datetime}  准备发起监听任务')
    mapping_listen_job: Dict[str, List[Dict]] = {}
    for activa_listen_job in get_activa_listen_job(job_id=None):
        if not activa_listen_job.status:
            continue
        listen_channels = json.loads(activa_listen_job.listen_channels)
        for listen_channel in listen_channels:
            dict_job = dict(
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
            if listen_channel not in mapping_listen_job:
                mapping_listen_job[listen_channel] = [dict_job]
            else:
                mapping_listen_job[listen_channel].append(dict_job)
    for listen_api in get_listen_api_by_name(api_name=None):
        api_name = listen_api.api_name
        api_type = listen_api.api_type
        if not listen_api.enable:
            logger.info(f'{api_name}接口监听未启用，跳过')
            continue
        logger.info(f'准备扫描{api_name}接口监听消息')
        params_json = json.loads(listen_api.params_json)
        if api_type == '邮件POP3协议':
            if mapping_listen_job.get(api_name, None) is None:  # 都不需要检测这个通道
                logger.info(f'没有任务配置{api_name}接口监听，跳过')
                continue
            if not listen_api.params_json:
                logger.error(f'{api_name}的接口未配置')
                continue
            pop3_server = params_json['pop3_server']
            port = params_json['port']
            email_account = params_json['email_account']
            password = params_json['password']
            emails = email_pop3.get_email_context_from_subject_during(
                pop3_server=pop3_server,
                port=int(port),
                emal_account=email_account,
                password=password,
                since_time=last_datetime,
                before_time=end_datetime,
            )
            if emails:
                logger.info(f'接口{api_name}发现新增邮件，主题为: {",".join([email["subject"] for email in emails])}')
            else:
                logger.info(f'接口{api_name}没有发现新增邮件')
            for email in emails:
                email_to_run_date_job(email, mapping_listen_job[api_name])
