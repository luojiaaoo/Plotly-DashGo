from peewee import Model, CharField, TextField, DateTimeField, BooleanField, IntegerField
from ..conn import db
from datetime import datetime


class BaseModel(Model):
    class Meta:
        database = db()


class SysOrcaRouterCredential(BaseModel):
    """OrcaRouter credential held for this installation.

    One row per authentication method, so the API-key and PKCE choices can coexist
    and are revoked, re-authorized and diagnosed independently. The key itself is
    stored encrypted with the project's existing ``util_encrypt`` helper — the same
    mechanism already used for other provider secrets.
    """

    auth_method = CharField(max_length=32, primary_key=True, help_text='认证方式 orcarouter / orcarouter-oauth')
    api_key_encrypted = TextField(help_text='加密后的API Key')
    scope = CharField(max_length=32, help_text='授权范围', default='')
    user_id = CharField(max_length=64, help_text='OrcaRouter 用户ID', default='')
    generation = IntegerField(help_text='凭据代数，每次写入自增，用于隔离过期异步响应', default=1)
    needs_reauth = BooleanField(help_text='是否需要重新认证', default=False)
    create_datetime = DateTimeField(help_text='创建时间', default=datetime.now)
    update_datetime = DateTimeField(help_text='更新时间', default=datetime.now)

    class Meta:
        table_name = 'sys_orcarouter_credential'
