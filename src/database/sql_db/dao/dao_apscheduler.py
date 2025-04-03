from database.sql_db.conn import db
from peewee import DoesNotExist, IntegrityError
from common.utilities.util_logger import Log
from ..entity.table_apscheduler import ApschedulerResults, ApschedulerExtractValue
from datetime import datetime, timedelta
import re

logger = Log.get_logger(__name__)


def select_last_log_from_job_id(job_id: str, accept_timedelta: timedelta) -> str:
    """查询指定job_id的最新的日志log"""
    try:
        result = (
            ApschedulerResults.select(ApschedulerResults.log)
            .where(ApschedulerResults.job_id == job_id and ApschedulerResults.finish_datetime > datetime.now() - accept_timedelta)
            .order_by(ApschedulerResults.finish_datetime.desc())
            .get()
        )
        return result[0]
    except DoesNotExist as e:
        raise Exception('Job log not found') from e


def insert_apscheduler_result(job_id, status, log, extract_names):
    database = db()
    try:
        now = datetime.now()
        with database.atomic():
            ApschedulerResults.create(job_id=job_id, status=status, log=log, finish_datetime=now)
        with database.atomic():
            for extract_name in extract_names:
                type_ = extract_name['type']
                name = extract_name['name']
                value = re.search(r'<SOPS_VAR>%s:(.+?)</SOPS_VAR>' % name, log).group(1)
                if type_ == 'enum':
                    value = str(value)
                elif type_ == 'int':
                    value = int(value)
                elif type_ == 'float':
                    value = float(value)
                else:
                    raise ValueError('不支持的提取数据类型')
                ApschedulerExtractValue.create(
                    job_id=job_id,
                    extract_name=extract_name,
                    value_type=type_,
                    value=value,
                    finish_datetime=now,
                )
    except IntegrityError as e:
        logger.error(f'插入任务结果时发生数据库完整性错误: {e}')
        raise Exception('Failed to insert apscheduler result due to integrity error') from e
    except Exception as e:
        logger.error(f'插入任务结果时发生未知错误: {e}')
        raise Exception('Failed to insert apscheduler result due to an unknown error') from e
