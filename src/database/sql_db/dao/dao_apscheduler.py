from database.sql_db.conn import db
from peewee import DoesNotExist, IntegrityError
from common.utilities.util_logger import Log
from ..entity.table_apscheduler import ApschedulerResults, ApschedulerExtractValue, ApschedulerRunning
from datetime import datetime, timedelta
from common.notify import send_notify
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


def get_apscheduler_start_finish_datetime_with_status_by_job_id(job_id: str) -> datetime:
    """查询指定job_id的开始时间"""
    try:
        result_running = (
            ApschedulerRunning.select(ApschedulerRunning.start_datetime).where(ApschedulerRunning.job_id == job_id).distinct().order_by(ApschedulerRunning.start_datetime.desc())
        )
        result_done = (
            ApschedulerResults.select(ApschedulerResults.start_datetime, ApschedulerResults.finish_datetime, ApschedulerResults.status)
            .where(ApschedulerResults.job_id == job_id)
            .order_by(ApschedulerResults.start_datetime.desc())
        )
        start_datetimes_running = [(i.start_datetime, '...', 'running') for i in result_running]
        start_datetimes_done = [(i.start_datetime, i.finish_datetime, i.status) for i in result_done]
        return [*start_datetimes_running, *start_datetimes_done]
    except DoesNotExist as e:
        raise Exception('Job start datetime not found') from e


def get_running_log(job_id: str, start_datetime: datetime, order: int = None) -> str:
    """查询指定job_id的日志log"""
    try:
        return (
            ApschedulerRunning.select(ApschedulerRunning.log)
            .where(ApschedulerRunning.job_id == job_id and ApschedulerRunning.start_datetime == start_datetime and ApschedulerRunning.order == order)
            .dicts()
            .get()['log']
        )
    except DoesNotExist:
        return None
    except Exception as e:
        raise e


def get_done_log(job_id: str, start_datetime: datetime) -> str:
    """查询指定job_id的日志log"""
    try:
        return (
            ApschedulerResults.select(ApschedulerResults.log)
            .where(ApschedulerResults.job_id == job_id and ApschedulerResults.start_datetime == start_datetime)
            .dicts()
            .get()['log']
        )
    except DoesNotExist:
        return None
    except Exception as e:
        raise e


def insert_apscheduler_running(job_id, log, order, start_datetime):
    """插入实时日志到数据库"""
    database = db()
    try:
        with database.atomic():
            ApschedulerRunning.create(job_id=job_id, log=log, order=order, start_datetime=start_datetime)
    except IntegrityError as e:
        logger.error(f'插入实时日志时发生数据库完整性错误: {e}')
        raise Exception('Failed to insert apscheduler running log due to integrity error') from e
    except Exception as e:
        logger.error(f'插入实时日志时发生未知错误: {e}')
        raise Exception('Failed to insert apscheduler running log due to an unknown error') from e


def select_apscheduler_running_log(job_id, start_datetime, order=None):
    """查询指定job_id的实时日志log"""
    try:
        if order is None:
            results = (
                ApschedulerRunning.select(ApschedulerRunning.log)
                .where(ApschedulerRunning.job_id == job_id and ApschedulerRunning.start_datetime == start_datetime)
                .order_by(ApschedulerRunning.order.asc())
            )
        else:
            results = ApschedulerRunning.select(ApschedulerRunning.log).where(
                ApschedulerRunning.job_id == job_id and ApschedulerRunning.start_datetime == start_datetime and ApschedulerRunning.order == order
            )
        result = [result.log for result in results]
        return ''.join(result)
    except DoesNotExist as e:
        raise Exception('Job log not found') from e


def delete_apscheduler_running(job_id, start_datetime):
    """删除指定job_id的实时日志log"""
    database = db()
    try:
        with database.atomic():
            ApschedulerRunning.delete().where(ApschedulerRunning.job_id == job_id and ApschedulerRunning.start_datetime == start_datetime).execute()
    except IntegrityError as e:
        logger.error(f'删除实时日志时发生数据库完整性错误: {e}')
        raise Exception('Failed to delete apscheduler running log due to integrity error') from e
    except Exception as e:
        logger.error(f'删除实时日志时发生未知错误: {e}')
        raise Exception('Failed to delete apscheduler running log due to an unknown error') from e


def truncate_apscheduler_running():
    database = db()
    try:
        with database.atomic():
            ApschedulerRunning.delete().execute()
    except IntegrityError as e:
        logger.error(f'清空实时日志时发生数据库完整性错误: {e}')


def insert_apscheduler_result(job_id, status, log, start_datetime, extract_names):
    database = db()
    try:
        now = datetime.now()
        with database.atomic():
            ApschedulerResults.create(job_id=job_id, status=status, log=log, start_datetime=start_datetime, finish_datetime=now)
        if not extract_names:
            return
        with database.atomic():
            for extract_name in extract_names:
                type_ = extract_name['type']
                name = extract_name['name']
                re_search = re.search(r'<SOPS_VAR>%s:(.+?)</SOPS_VAR>' % name, log, flags=re.DOTALL)
                if re_search:
                    value = re_search.group(1)
                    if type_ == 'string':
                        try:
                            value = str(value)
                        except:
                            logger.warning(f'提取数据类型为string，但无法转换为字符串: {value}')
                            continue
                    elif type_ == 'number':
                        try:
                            value = float(value)
                        except:
                            logger.warning(f'提取数据类型为string，但无法转换为字符串: {value}')
                            continue
                    elif type_ == 'notify':
                        send_notify(title=name, short=value, desp=value + f'\nThe message from Job {job_id}')
                    else:
                        raise ValueError('不支持的提取数据类型')
                    ApschedulerExtractValue.create(
                        job_id=job_id,
                        extract_name=extract_name,
                        value_type=type_,
                        value=value,
                        start_datetime=start_datetime,
                        finish_datetime=now,
                    )
    except IntegrityError as e:
        logger.error(f'插入任务结果时发生数据库完整性错误: {e}')
        raise Exception('Failed to insert apscheduler result due to integrity error') from e
    except Exception as e:
        logger.error(f'插入任务结果时发生未知错误: {e}')
        raise Exception('Failed to insert apscheduler result due to an unknown error') from e


def delete_expire_data(day):
    # 删除ApschedulerResults和ApschedulerExtractValue超时的数据
    try:
        database = db()
        with database.atomic():
            expire_time = datetime.now() - timedelta(days=day)
            ApschedulerResults.delete().where(ApschedulerResults.start_datetime < expire_time).execute()
            ApschedulerExtractValue.delete().where(ApschedulerExtractValue.start_datetime < expire_time).execute()
    except IntegrityError as e:
        logger.error(f'删除超时数据时发生数据库完整性错误: {e}')
        raise Exception('Failed to delete expired data due to integrity error') from e
    except Exception as e:
        logger.error(f'删除超时数据时发生未知错误: {e}')
        raise Exception('Failed to delete expired data due to an unknown error') from e
