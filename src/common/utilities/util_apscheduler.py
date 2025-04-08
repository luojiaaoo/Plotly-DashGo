import rpyc
import json
from dataclasses import dataclass
from typing import Optional, Dict


def add_ssh_interval_job(ip, username, password, script_text, interval, timeout, job_id, update_by, update_datetime, create_by, create_datetime, extract_names=None):
    try:
        conn = rpyc.connect('127.0.0.1', 8091)
        job = conn.root.add_job(
            'app_apscheduler:run_script',
            'interval',
            kwargs=dict(
                ('type', 'ssh'),
                ('script_text', script_text),
                ('timeout', timeout),
                ('ip', ip),
                ('username', username),
                ('password', password),
                ('extract_names', extract_names),
                ('update_by', update_by),
                ('update_datetime', update_datetime),
                ('create_by', create_by),
                ('create_datetime', create_datetime),
            ),
            seconds=interval,
            id=job_id,
        )
        return job.id
    except Exception as e:
        raise e
    finally:
        conn.close()


def add_ssh_cron_job(
    ip, username, password, script_text, cron_text, timeout, job_id, update_by, update_datetime, create_by, create_datetime, extract_names=None, year=None, week=None
):
    """https://apscheduler.readthedocs.io/en/master/api.html#apscheduler.triggers.cron.CronTrigger"""
    try:
        conn = rpyc.connect('localhost', 8091)
        if len(cron_text) == 5:
            minute, hour, day, month, day_of_week = cron_text
            second = None
        elif len(cron_text) == 6:
            second, minute, hour, day, month, day_of_week = cron_text
        else:
            raise Exception('cron_text error')
        job = conn.root.add_job(
            'app_apscheduler:run_script',
            'cron',
            kwargs=[
                ('type', 'ssh'),
                ('script_text', script_text),
                ('timeout', timeout),
                ('ip', ip),
                ('username', username),
                ('password', password),
                ('extract_names', extract_names),
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


def add_local_interval_job(script_text, interval, timeout, job_id, update_by, update_datetime, create_by, create_datetime, extract_names=None):
    try:
        conn = rpyc.connect('localhost', 8091)
        job = conn.root.add_job(
            'app_apscheduler:run_script',
            'interval',
            kwargs=[
                ('type', 'local'),
                ('script_text', script_text),
                ('timeout', timeout),
                ('extract_names', extract_names),
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


@dataclass
class JobInfo:
    job_id: str
    status: bool
    job_next_run_time: str
    trigger: str
    plan: Dict
    type: str
    script_text: str
    timeout: int
    extract_names: Optional[Dict]
    update_by: str
    update_datetime: str
    create_by: str
    create_datetime: str


def get_apscheduler_all_jobs():
    try:
        conn = rpyc.connect('localhost', 8091)
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
                timeout=job_json['kwargs']['timeout'],
                extract_names=job_json['kwargs']['extract_names'],
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
