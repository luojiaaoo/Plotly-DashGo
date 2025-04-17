from peewee import Model, CharField, TextField, DateTimeField, BooleanField
from ..conn import db
from datetime import datetime
import secrets


class BaseModel(Model):
    class Meta:
        database = db()


class NotifyApi(BaseModel):
    """通知API"""

    api_name = CharField(max_length=64, primary_key=True, help_text='通知API名')
    api_type = CharField(max_length=32, help_text='接口类型')
    enable = BooleanField(help_text='是否启用')
    params_json = TextField(help_text='参数Json格式')

    class Meta:
        table_name = 'sys_notify_api'
