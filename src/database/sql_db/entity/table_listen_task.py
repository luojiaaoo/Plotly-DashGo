from peewee import Model, CharField, TextField, DateTimeField, BooleanField, IntegerField
from ..conn import db
from datetime import datetime
import secrets


class BaseModel(Model):
    class Meta:
        database = db()


class ApschedulerJobsActiveListen(BaseModel):
    """主动监听触发器表"""

    # 执行配置
    job_id = CharField(max_length=64, help_text='job名称')
    script_text = TextField(help_text='脚本内容')
    script_type = CharField(max_length=32, help_text='脚本类型')
    update_by = CharField(max_length=32, help_text='被谁更新')
    update_datetime = DateTimeField(help_text='更新时间')
    create_by = CharField(max_length=32, help_text='被谁创建')
    create_datetime = DateTimeField(help_text='创建时间')
    notify_channels = TextField(help_text='通知渠道')
    extract_names = TextField(help_text='数据抽取配置')
    timeout = IntegerField(help_text='超时时间')
    # 监听配置
    listen_channels = TextField(help_text='通知渠道')
    listen_keyword = CharField(max_length=64, help_text='监听关键字')  # 监听关键字，如遇到关键词就会主动触发任务

    class Meta:
        table_name = 'apscheduler_jobs_active_listen'
        indexes = ((('job_id', 'listen_keyword'), True),)
