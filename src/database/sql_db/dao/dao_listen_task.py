from database.sql_db.conn import db
from peewee import DoesNotExist, IntegrityError
from common.utilities.util_logger import Log
from ..entity.table_listen_task import ApschedulerJobsActiveListen
from datetime import datetime, timedelta
from typing import Optional, Iterator, List, Union

logger = Log.get_logger(__name__)


def get_activa_listen_job(job_id: Optional[str] = None, listen_keyword: Optional[str] = None) -> List[ApschedulerJobsActiveListen]:
    if job_id is None:
        activa_listen_jobs = [i for i in ApschedulerJobsActiveListen.select()]
        return activa_listen_jobs
    else:
        activa_listen_jobs = [
            i for i in ApschedulerJobsActiveListen.select().where(ApschedulerJobsActiveListen.job_id == job_id and ApschedulerJobsActiveListen.listen_keyword == listen_keyword)
        ]
        return activa_listen_jobs


def delete_activa_listen_job(job_id: str, listen_keyword: str) -> bool:
    database = db()
    try:
        with database.atomic():
            ApschedulerJobsActiveListen.delete().where(ApschedulerJobsActiveListen.job_id == job_id and ApschedulerJobsActiveListen.listen_keyword == listen_keyword).execute()
        return True
    except IntegrityError:
        return False


def insert_activa_listen_job(
    job_id,
    script_text,
    script_type,
    update_by,
    update_datetime,
    create_by,
    create_datetime,
    notify_channels,
    extract_names,
    timeout,
    listen_channels,
    listen_keyword,
) -> bool:
    database = db()
    try:
        with database.atomic():
            ApschedulerJobsActiveListen.create(
                job_id=job_id,
                script_text=script_text,
                script_type=script_type,
                update_by=update_by,
                update_datetime=update_datetime,
                create_by=create_by,
                create_datetime=create_datetime,
                notify_channels=notify_channels,
                extract_names=extract_names,
                timeout=timeout,
                listen_channels=listen_channels,
                listen_keyword=listen_keyword,
            )
        return True
    except IntegrityError:
        return False
