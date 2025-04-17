import rpyc
import json
from dataclasses import dataclass
from typing import Optional, Dict, List
from config.dashgo_conf import ApSchedulerConf


def get_connect():
    return rpyc.connect(ApSchedulerConf.HOST, ApSchedulerConf.PORT)


def add_ssh_interval_job(
    host, port, username, password, script_text, script_type, interval, timeout, job_id, update_by, update_datetime, create_by, create_datetime, extract_names, notify_channels
):
    if not extract_names:
        extract_names = None
    try:
        conn = get_connect()
        job = conn.root.add_job(
            'app_apscheduler:run_script',
            'interval',
            kwargs=[
                ('type', 'ssh'),
                ('script_text', script_text),
                ('script_type', script_type),
                ('timeout', timeout),
                ('host', host),
                ('port', port),
                ('username', username),
                ('password', password),
                ('extract_names', extract_names),
                ('notify_channels', notify_channels),
                ('update_by', update_by),
                ('update_datetime', update_datetime),
                ('create_by', create_by),
                ('create_datetime', create_datetime),
            ],
            seconds=interval,
            id=job_id,
        )
        return job.id
    except Exception as e:
        raise e
    finally:
        conn.close()


def add_ssh_cron_job(
    host, port, username, password, script_text, script_type, cron_list, timeout, job_id, update_by, update_datetime, create_by, create_datetime, extract_names, notify_channels
):
    """https://apscheduler.readthedocs.io/en/master/api.html#apscheduler.triggers.cron.CronTrigger"""
    if not extract_names:
        extract_names = None
    try:
        conn = get_connect()
        second, minute, hour, day, month, day_of_week, year, week = cron_list
        job = conn.root.add_job(
            'app_apscheduler:run_script',
            'cron',
            kwargs=[
                ('type', 'ssh'),
                ('script_text', script_text),
                ('script_type', script_type),
                ('timeout', timeout),
                ('host', host),
                ('port', port),
                ('username', username),
                ('password', password),
                ('extract_names', extract_names),
                ('notify_channels', notify_channels),
                ('update_by', update_by),
                ('update_datetime', update_datetime),
                ('create_by', create_by),
                ('create_datetime', create_datetime),
            ],
            year=year,
            week=week,
            second=second,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=job_id,
        )
        return job.id
    except Exception as e:
        raise e
    finally:
        conn.close()


def add_local_interval_job(script_text, script_type, interval, timeout, job_id, update_by, update_datetime, create_by, create_datetime, extract_names, notify_channels):
    if not extract_names:
        extract_names = None
    try:
        conn = get_connect()
        job = conn.root.add_job(
            'app_apscheduler:run_script',
            'interval',
            kwargs=[
                ('type', 'local'),
                ('script_text', script_text),
                ('script_type', script_type),
                ('timeout', timeout),
                ('extract_names', extract_names),
                ('notify_channels', notify_channels),
                ('update_by', update_by),
                ('update_datetime', update_datetime),
                ('create_by', create_by),
                ('create_datetime', create_datetime),
            ],
            seconds=interval,
            id=job_id,
        )
        return job.id
    except Exception as e:
        raise e
    finally:
        conn.close()


def add_local_cron_job(script_text, script_type, cron_list, timeout, job_id, update_by, update_datetime, create_by, create_datetime, extract_names, notify_channels):
    if not extract_names:
        extract_names = None
    try:
        conn = get_connect()
        second, minute, hour, day, month, day_of_week, year, week = cron_list
        job = conn.root.add_job(
            'app_apscheduler:run_script',
            'cron',
            kwargs=[
                ('type', 'local'),
                ('script_text', script_text),
                ('script_type', script_type),
                ('timeout', timeout),
                ('extract_names', extract_names),
                ('notify_channels', notify_channels),
                ('update_by', update_by),
                ('update_datetime', update_datetime),
                ('create_by', create_by),
                ('create_datetime', create_datetime),
            ],
            year=year,
            week=week,
            second=second,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=job_id,
        )
        return job.id
    except Exception as e:
        raise e
    finally:
        conn.close()


@dataclass
class JobInfo:
    job_id: str
    status: bool
    job_next_run_time: str
    trigger: str
    plan: Dict
    type: str
    script_text: str
    script_type: str
    timeout: int
    extract_names: Optional[List]
    notify_channels: Optional[List]
    update_by: str
    update_datetime: str
    create_by: str
    create_datetime: str


def get_apscheduler_all_jobs():
    try:
        conn = get_connect()
        job_jsons = json.loads(conn.root.get_jobs())
        return [
            JobInfo(
                job_id=job_json['id'],
                status=job_json['status'],
                job_next_run_time=job_json['next_run_time'],
                trigger=job_json['trigger'],
                plan=job_json['plan'],
                type=job_json['kwargs']['type'],
                script_text=job_json['kwargs']['script_text'],
                script_type=job_json['kwargs']['script_type'],
                timeout=job_json['kwargs']['timeout'],
                extract_names=job_json['kwargs']['extract_names'],
                notify_channels=job_json['kwargs']['notify_channels'],
                update_by=job_json['kwargs']['update_by'],
                update_datetime=job_json['kwargs']['update_datetime'],
                create_by=job_json['kwargs']['create_by'],
                create_datetime=job_json['kwargs']['create_datetime'],
                # 'extract_names': job_json['kwargs']['extract_names'] if job_json['kwargs'].get('extract_names', None) is not None else '',
            )
            for job_json in job_jsons
        ]
    except Exception as e:
        raise e
    finally:
        conn.close()


def start_stop_job(job_id, is_start: bool):
    try:
        conn = get_connect()
        if is_start:
            conn.root.resume_job(job_id=job_id)
        else:
            conn.root.pause_job(job_id=job_id)
    except Exception as e:
        raise e
    finally:
        conn.close()


def remove_job(job_id):
    try:
        conn = get_connect()
        conn.root.remove_job(job_id=job_id)
    except Exception as e:
        raise e
    finally:
        conn.close()


def modify_job(job_id, **kwargs):
    try:
        conn = get_connect()
        conn.root.modify_job(job_id=job_id, **kwargs)
    except Exception as e:
        raise e
    finally:
        conn.close()


def reschedule_job_cron(job_id, second, minute, hour, day, month, day_of_week, year=None, week=None):
    try:
        conn = get_connect()
        conn.root.reschedule_job(
            job_id,
            'cron',
            year=year,
            week=week,
            second=second,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
        )
    except Exception as e:
        raise e
    finally:
        conn.close()


def reschedule_job_interval(job_id, seconds):
    try:
        conn = get_connect()
        conn.root.reschedule_job(
            job_id,
            'interval',
            seconds=seconds,
        )
    except Exception as e:
        raise e
    finally:
        conn.close()


def get_platform():
    try:
        conn = get_connect()
        return conn.root.get_platform()
    except Exception as e:
        raise e
    finally:
        conn.close()


def get_job(job_id):
    try:
        conn = get_connect()
        return json.loads(conn.root.get_job(job_id))
    except Exception as e:
        raise e
    finally:
        conn.close()
