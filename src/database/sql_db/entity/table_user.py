from peewee import CharField, Model, IntegerField, DateTimeField, ForeignKeyField, BooleanField
from ..conn import db


class BaseModel(Model):
    class Meta:
        database = db()


class SysGroup(BaseModel):
    group_name = CharField(primary_key=True, max_length=128, help_text='团队名称')
    group_status = BooleanField(help_text='团队状态（0：停用，1：启用）')
    update_datetime = DateTimeField(help_text='更新时间')
    update_by = CharField(max_length=32, help_text='被谁更新')
    create_datetime = DateTimeField(help_text='创建时间')
    create_by = CharField(max_length=32, help_text='被谁创建')
    group_remark = CharField(max_length=255, help_text='团队描述')

    class Meta:
        table_name = 'sys_group'


class SysRole(BaseModel):
    role_name = CharField(primary_key=True, max_length=32, help_text='角色名')
    role_status = BooleanField(help_text='角色状态（0：停用，1：启用）')
    update_datetime = DateTimeField(help_text='更新时间')
    update_by = CharField(max_length=32, help_text='被谁更新')
    create_datetime = DateTimeField(help_text='创建时间')
    create_by = CharField(max_length=32, help_text='被谁创建')
    role_remark = CharField(max_length=255, help_text='角色描述')

    class Meta:
        table_name = 'sys_role'


class SysGroupRole(BaseModel):
    group_name = ForeignKeyField(SysGroup, backref='roles', column_name='group_name', help_text='团队名称')
    role_name = ForeignKeyField(SysRole, backref='groups', column_name='role_name', help_text='角色名')

    class Meta:
        table_name = 'sys_group_role'
        indexes = ((('group_name', 'role_name'), True),)


class SysGroupUser(BaseModel):
    group_name = ForeignKeyField(SysGroup, backref='users', column_name='group_name', help_text='团队名称')
    user_name = CharField(max_length=32, help_text='用户名')
    is_admin = IntegerField(help_text='是否为管理员')

    class Meta:
        table_name = 'sys_group_user'
        indexes = ((('group_name', 'user_name'), True),)


class SysUser(BaseModel):
    user_name = CharField(primary_key=True, max_length=32, help_text='用户名')
    user_full_name = CharField(max_length=32, help_text='全名')
    user_status = BooleanField(help_text='用户状态（0：停用，1：启用）')
    password_sha256 = CharField(max_length=64, help_text='密码SHA256值')
    user_sex = CharField(max_length=64, help_text='性别')
    user_email = CharField(max_length=128, help_text='电子邮箱')
    phone_number = CharField(max_length=16, help_text='电话号码')
    update_by = CharField(max_length=32, help_text='被谁更新')
    update_datetime = DateTimeField(help_text='更新时间')
    create_by = CharField(max_length=32, help_text='被谁创建')
    create_datetime = DateTimeField(help_text='创建时间')
    user_remark = CharField(max_length=255, help_text='用户描述')
    otp_secret = CharField(max_length=16, help_text='OTP密钥')

    class Meta:
        table_name = 'sys_user'


class SysUserRole(BaseModel):
    user_name = ForeignKeyField(SysUser, backref='roles', column_name='user_name', help_text='用户名')
    role_name = ForeignKeyField(SysRole, backref='users', column_name='role_name', help_text='角色名')

    class Meta:
        table_name = 'sys_user_role'
        indexes = ((('user_name', 'role_name'), True),)


class SysRoleAccessMeta(BaseModel):
    role_name = ForeignKeyField(SysRole, backref='access_meta', column_name='role_name', help_text='角色名')
    access_meta = CharField(max_length=32, help_text='访问元数据')

    class Meta:
        table_name = 'sys_role_access_meta'
        indexes = ((('role_name', 'access_meta'), True),)
