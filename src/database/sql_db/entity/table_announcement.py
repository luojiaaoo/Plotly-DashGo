from peewee import CharField, Model, DateTimeField, BooleanField
from ..conn import db


class BaseModel(Model):
    class Meta:
        database = db()


class SysAnnouncement(BaseModel):
    datetime = DateTimeField(help_text='添加时间')
    announcement = CharField(max_length=512, help_text='公告')
    user_name = CharField(max_length=32, help_text='用户名')
    status = BooleanField(help_text='状态（0：停用，1：启用）')

    class Meta:
        table_name = 'sys_announcement'
        indexes = ((('datetime',), False),)
