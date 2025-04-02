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
from ..entity.table_apscheduler import ApschedulerDataResults, ApschedulerConsoleResults

logger = Log.get_logger(__name__)

def select_apscheduler_data_results(job_id: str) -> ApschedulerDataResults:
    """查询指定job_id的数据结果"""

    try:
        return ApschedulerDataResults.get(ApschedulerDataResults.job_id == job_id)
    except DoesNotExist:
        return None

