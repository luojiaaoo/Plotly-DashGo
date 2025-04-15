from database.sql_db.conn import db
from peewee import DoesNotExist, IntegrityError
from common.utilities.util_logger import Log
from ..entity.table_notify_api import NotifyApi
from datetime import datetime, timedelta
import re
from typing import Iterator

logger = Log.get_logger(__name__)
api_names = [
    'Server酱',
]


def get_notify_api_by_name(api_name: str) -> NotifyApi:
    database = db()
    try:
        with database.atomic():
            result = NotifyApi.select().where(NotifyApi.api_name == api_name).get()
            return result
    except DoesNotExist:
        return None


def insert_notify_api(api_name: str, enable: bool, params_json: str) -> bool:
    database = db()
    try:
        with database.atomic():
            NotifyApi.create(api_name=api_name, enable=enable, params_json=params_json)
        return True
    except IntegrityError as e:
        logger.error(e, exc_info=True)
        return False


def delete_notify_api_by_name(api_name: str) -> bool:
    database = db()
    try:
        with database.atomic():
            NotifyApi.delete().where(NotifyApi.api_name == api_name).execute()
        return True
    except IntegrityError:
        return False


def modify_enable(api_name: str, enable: bool) -> bool:
    database = db()
    try:
        with database.atomic():
            NotifyApi.update(enable=enable).where(NotifyApi.api_name == api_name).execute()
        return True
    except IntegrityError:
        return False
