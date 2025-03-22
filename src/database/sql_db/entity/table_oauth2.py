from peewee import Model, CharField, TextField, DateTimeField
from ..conn import db
from datetime import datetime
import secrets


class BaseModel(Model):
    class Meta:
        database = db()


class OAuth2Client(BaseModel):
    """注册的三方客户端信息"""

    client_id = CharField(max_length=48, help_text='客户端ID')
    client_secret = CharField(max_length=120, help_text='客户端密钥')
    redirect_uris = TextField(help_text='允许的回调地址')
    scope = TextField(help_text='权限范围')

    class Meta:
        indexes = ((('client_id',), True),)

    # grant阶段验证
    def check_redirect_uri(self, redirect_uri):
        return redirect_uri in self.redirect_uris.split()

    def check_scope(self, redirect_uris):
        return set(redirect_uris).issubset(set(self.redirect_uris.split()))

    # token阶段验证
    def check_client_secret(self, client_secret):
        return secrets.compare_digest(self.client_secret, client_secret)

    def check_grant_type(self, grant_type):
        return grant_type == 'authorization_code'


class OAuth2AuthorizationCode(BaseModel):
    """生成的随机授权码"""

    code = CharField(max_length=120, help_text='授权码')
    client_id = CharField(max_length=48, help_text='客户端ID')
    user_name = CharField(max_length=32, help_text='用户名')
    redirect_uri = CharField(max_length=120, help_text='回调地址')
    expires_at = DateTimeField(help_text='过期时间')
    scope = TextField(help_text='权限范围')

    class Meta:
        indexes = ((('code',), True),)

    def is_valid(self):
        return self.expires_at > datetime.now()

    def check_redirect_uri(self, redirect_uri):
        return redirect_uri == self.redirect_uri

    def check_client_id(self, client_id):
        return client_id == self.client_id


class OAuth2Token(BaseModel):
    """颁发的访问令牌"""

    token = CharField(max_length=256, help_text='访问令牌')
    client_id = CharField(max_length=48, help_text='客户端ID')
    user_name = CharField(max_length=32, help_text='用户名')
    expires_at = DateTimeField(help_text='过期时间')
    scope = TextField(help_text='权限范围')

    class Meta:
        indexes = ((('token',), True),)

    def is_valid(self):
        """检查令牌是否有效"""
        from datetime import datetime
        from common.utilities.util_jwt import jwt_decode

        try:
            jwt_decode(self.token, verify_exp=True)
        except Exception:
            return False
        return self.expires_at > datetime.now()
