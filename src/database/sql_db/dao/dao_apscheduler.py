from database.sql_db.conn import db
from typing import Dict, List, Set, Union, Optional, Iterator
from itertools import chain, repeat
from dataclasses import dataclass
from datetime import datetime
from common.utilities import util_menu_access
import json
import hashlib
from peewee import DoesNotExist, fn, MySQLDatabase, SqliteDatabase, IntegrityError, JOIN, Case
from common.utilities.util_logger import Log
from ..entity.table_apscheduler import ApschedulerResults, ApschedulerExtractValue
from datetime import datetime, timedelta

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
