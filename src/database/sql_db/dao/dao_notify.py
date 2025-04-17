from database.sql_db.conn import db
from peewee import DoesNotExist, IntegrityError
from common.utilities.util_logger import Log
from ..entity.table_notify_api import NotifyApi
from datetime import datetime, timedelta
from typing import Optional, Iterator, List, Union

logger = Log.get_logger(__name__)
support_api_types = [
    'Server酱',
    '企业微信群机器人',
]


def insert_notify_api(api_name: str, api_type: str, enable: bool, params_json: str) -> bool:
    database = db()
    try:
        with database.atomic():
            NotifyApi.create(api_name=api_name, api_type=api_type, enable=enable, params_json=params_json)
        return True
    except IntegrityError as e:
        logger.error(e, exc_info=True)
        return False


def get_notify_api_by_name(api_name: Optional[str] = None) -> Union[NotifyApi, List[NotifyApi]]:
    database = db()
    if api_name is None:
        notify_apis = [i for i in NotifyApi.select()]
        notify_apis.sort(key=lambda x: x.api_name)
        return notify_apis
    else:
        try:
            with database.atomic():
                result = NotifyApi.select().where(NotifyApi.api_name == api_name).get()
                return result
        except DoesNotExist:
            return None


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
