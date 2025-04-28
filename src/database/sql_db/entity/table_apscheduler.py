from peewee import Model, CharField, TextField, DateTimeField, ForeignKeyField, IntegerField
from ..conn import db


class BaseModel(Model):
    class Meta:
        database = db()


class SysApschedulerRunning(BaseModel):
    """保存控制台任务实时输出日志"""

    job_id = CharField(max_length=191, help_text='Job名')
    log = TextField(help_text='返回的日志')
    order = IntegerField(help_text='输出顺序')
    start_datetime = DateTimeField(help_text='开始时间')

    class Meta:
        table_name = 'sys_apscheduler_running'
        indexes = ((('job_id', 'start_datetime', 'order'), False),)


class SysApschedulerResults(BaseModel):
    """保存控制台任务输出日志"""

    job_id = CharField(max_length=191, help_text='Job名')
    status = CharField(max_length=8, help_text='执行状态')
    log = TextField(help_text='返回的日志')
    start_datetime = DateTimeField(help_text='开始时间')
    finish_datetime = DateTimeField(help_text='完成时间')

    class Meta:
        table_name = 'sys_apscheduler_results'
        indexes = ((('job_id', 'start_datetime'), True),)


class SysApschedulerExtractValue(BaseModel):
    """保存任务输出提取数据"""

    job_id = CharField(max_length=191, help_text='Job名')
    extract_name = CharField(max_length=32, help_text='提取数据名')
    value_type = CharField(max_length=16, help_text='提取数据类型')
    value = CharField(max_length=64, help_text='提取数据值')
    start_datetime = DateTimeField(help_text='开始时间')
    finish_datetime = DateTimeField(help_text='完成时间')

    class Meta:
        table_name = 'sys_apscheduler_extract_value'
        indexes = ((('extract_name', 'job_id', 'start_datetime'), True),)
