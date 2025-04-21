from database.sql_db.conn import db
from peewee import DoesNotExist, IntegrityError
from common.utilities.util_logger import Log
from ..entity.table_listen_api import SysListenApi
from datetime import datetime, timedelta
from typing import Optional, Iterator, List, Union

logger = Log.get_logger(__name__)
support_api_types = [
    '邮件POP3协议',
]


def insert_listen_api(api_name: str, api_type: str, enable: bool, params_json: str) -> bool:
    database = db()
    try:
        with database.atomic():
            SysListenApi.create(api_name=api_name, api_type=api_type, enable=enable, params_json=params_json)
        return True
    except IntegrityError as e:
        logger.error(e, exc_info=True)
        return False


def get_listen_api_by_name(api_name: Optional[str] = None) -> Union[SysListenApi, List[SysListenApi]]:
    database = db()
    if api_name is None:
        listen_apis = [i for i in SysListenApi.select()]
        listen_apis.sort(key=lambda x: x.api_name)
        return listen_apis
    else:
        try:
            with database.atomic():
                result = SysListenApi.select().where(SysListenApi.api_name == api_name).get()
                return result
        except DoesNotExist:
            return None


def delete_listen_api_by_name(api_name: str) -> bool:
    database = db()
    try:
        with database.atomic():
            SysListenApi.delete().where(SysListenApi.api_name == api_name).execute()
        return True
    except IntegrityError:
        return False


def modify_enable(api_name: str, enable: bool) -> bool:
    database = db()
    try:
        with database.atomic():
            SysListenApi.update(enable=enable).where(SysListenApi.api_name == api_name).execute()
        return True
    except IntegrityError:
        return False
