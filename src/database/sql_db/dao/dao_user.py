from database.sql_db.conn import db
from typing import Dict, List, Set, Union, Optional, Iterator
from itertools import chain, repeat
from dataclasses import dataclass
from datetime import datetime
from common.utilities import util_menu_access
import json
import hashlib
from peewee import DoesNotExist, fn, MySQLDatabase, SqliteDatabase, IntegrityError, JOIN, Case
from common.utilities.util_logger import Log
from common.utilities.util_menu_access import get_menu_access
from ..entity.table_user import SysUser, SysRoleAccessMeta, SysUserRole, SysGroupUser, SysRole, SysGroupRole, SysGroup

logger = Log.get_logger(__name__)


class Status:
    ENABLE = 1
    DISABLE = 0


def exists_user_name(user_name: str) -> bool:
    """是否存在这个用户名"""
    try:
        SysUser.get(SysUser.user_name == user_name)
        return True
    except DoesNotExist:
        return False


def user_password_verify(user_name: str, password_sha256: str) -> bool:
    """密码校验，排除未启用账号"""
    try:
        SysUser.get((SysUser.user_name == user_name) & (SysUser.password_sha256 == password_sha256) & (SysUser.user_status == Status.ENABLE))
        return True
    except DoesNotExist:
        return False


def get_all_access_meta_for_setup_check() -> List[str]:
    """获取所有权限，对应用权限检查"""
    query: Iterator[SysRoleAccessMeta] = SysRoleAccessMeta.select(SysRoleAccessMeta.access_meta)
    return [role.access_meta for role in query]


########################### 用户
@dataclass
class UserInfo:
    user_name: str
    user_full_name: str
    user_status: str
    user_sex: str
    user_roles: List
    user_email: str
    phone_number: str
    update_datetime: datetime
    update_by: str
    create_datetime: datetime
    create_by: str
    user_remark: str


def get_user_info(user_names: Optional[List[str]] = None, exclude_role_admin=False, exclude_disabled=True) -> List[UserInfo]:
    """获取用户信息对象"""
    database = db()
    if isinstance(database, MySQLDatabase):
        user_roles_agg = fn.JSON_ARRAYAGG(SysUserRole.role_name).alias('user_roles')
    elif isinstance(database, SqliteDatabase):
        user_roles_agg = fn.GROUP_CONCAT(SysUserRole.role_name, '○').alias('user_roles')
    else:
        raise NotImplementedError('Unsupported database type')
    query = (
        SysUser.select(
            SysUser.user_name,
            SysUser.user_full_name,
            SysUser.user_status,
            SysUser.user_sex,
            SysUser.user_email,
            SysUser.phone_number,
            SysUser.update_datetime,
            SysUser.update_by,
            SysUser.create_datetime,
            SysUser.create_by,
            SysUser.user_remark,
            user_roles_agg,
        )
        .join(SysUserRole, JOIN.LEFT_OUTER, on=(SysUser.user_name == SysUserRole.user_name))
        .where(SysUser.user_name.in_(user_names) if user_names is not None else (1 == 1))
        .where((SysUser.user_status == Status.ENABLE) if exclude_disabled else (1 == 1))
        .group_by(
            SysUser.user_name,
            SysUser.user_full_name,
            SysUser.user_status,
            SysUser.user_sex,
            SysUser.user_email,
            SysUser.phone_number,
            SysUser.update_datetime,
            SysUser.update_by,
            SysUser.create_datetime,
            SysUser.create_by,
            SysUser.user_remark,
        )
    )
    query_admin = SysUserRole.select(SysUserRole.user_name).where(SysUserRole.role_name == 'admin')
    if exclude_role_admin:
        query.having(query.c.user_name.not_in(query_admin))
    user_infos = []
    for user in query.dicts():
        if isinstance(database, MySQLDatabase):
            user['user_roles'] = [i for i in json.loads(user['user_roles']) if i] if user['user_roles'] else []
        elif isinstance(database, SqliteDatabase):
            user['user_roles'] = user['user_roles'].split('○') if user['user_roles'] else []
        else:
            raise NotImplementedError('Unsupported database type')
        user_infos.append(UserInfo(**user))

    return user_infos


def add_role_for_user(user_name: str, role_name: str, database=None) -> bool:
    """添加用户角色"""
    if database is None:
        database = db()
    with database.atomic() as txn:
        try:
            SysUserRole.create(user_name=user_name, role_name=role_name)
        except IntegrityError:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}给用户{user_name}添加角色{role_name}时，出现异常', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def del_role_for_user(user_name: str, role_name: str, database=None) -> bool:
    """删除用户角色"""
    if database is None:
        database = db()
    with database.atomic() as txn:
        try:
            SysUserRole.delete().where((SysUserRole.user_name == user_name) & (SysUserRole.role_name == role_name)).execute()
        except Exception as e:
            logger.warning(f'用户{user_name}删除角色{role_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user(user_name, user_full_name, password, user_status: bool, user_sex, user_roles, user_email, phone_number, user_remark):
    """更新用户信息"""

    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user: SysUser = SysUser.get(SysUser.user_name == user_name)
            user.user_full_name = user_full_name
            if password:
                user.password_sha256 = hashlib.sha256(password.encode('utf-8')).hexdigest()
            user.user_status = user_status
            user.user_sex = user_sex
            user.user_email = user_email
            user.phone_number = phone_number
            user.update_by = user_name_op
            user.update_datetime = datetime.now()
            user.user_remark = user_remark
            user.save()

            SysUserRole.delete().where(SysUserRole.user_name == user_name).execute()
            if user_roles:
                SysUserRole.insert_many([{'user_name': user_name, 'role_name': role} for role in user_roles]).execute()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户{user_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user_full_name(user_name: str, user_full_name: str) -> bool:
    """更新用户全名"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user: SysUser = SysUser.get(SysUser.user_name == user_name)
            user.user_full_name = user_full_name
            user.update_by = user_name_op
            user.update_datetime = datetime.now()
            user.save()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户全名为{user_full_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user_sex(user_name: str, user_sex: str) -> bool:
    """更新用户性别"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user: SysUser = SysUser.get(SysUser.user_name == user_name)
            user.user_sex = user_sex
            user.update_by = user_name_op
            user.update_datetime = datetime.now()
            user.save()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户性别为{user_sex}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user_email(user_name: str, user_email: str) -> bool:
    """更新用户邮箱"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user: SysUser = SysUser.get(SysUser.user_name == user_name)
            user.user_email = user_email
            user.update_by = user_name_op
            user.update_datetime = datetime.now()
            user.save()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户邮箱为{user_email}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_phone_number(user_name: str, phone_number: str) -> bool:
    """更新用户电话"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user: SysUser = SysUser.get(SysUser.user_name == user_name)
            user.phone_number = phone_number
            user.update_by = user_name_op
            user.update_datetime = datetime.now()
            user.save()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户电话为{phone_number}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user_remark(user_name: str, user_remark: str) -> bool:
    """更新用户描述"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user: SysUser = SysUser.get(SysUser.user_name == user_name)
            user.user_remark = user_remark
            user.update_by = user_name_op
            user.update_datetime = datetime.now()
            user.save()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户描述为{user_remark}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user_password(user_name: str, new_password: str, old_password: Optional[str] = None) -> bool:
    """更新用户密码"""
    if old_password and not user_password_verify(user_name, hashlib.sha256(old_password.encode('utf-8')).hexdigest()):
        return False
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user: SysUser = SysUser.get(SysUser.user_name == user_name)
            user.password_sha256 = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
            user.update_by = user_name_op
            user.update_datetime = datetime.now()
            user.save()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新密码')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户{user_name}密码时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def gen_otp_qrcode(user_name: str, password: str) -> Optional[str]:
    """生成 OTP 二维码"""
    if not user_password_verify(user_name, hashlib.sha256(password.encode('utf-8')).hexdigest()):
        return False
    import uuid

    otp_secret = str(uuid.uuid4()).replace('-', '')[:16]
    database = db()
    with database.atomic():
        try:
            user: SysUser = SysUser.get(SysUser.user_name == user_name)
            user.otp_secret = otp_secret
            user.save()
        except DoesNotExist:
            return False

    return otp_secret


def get_otp_secret(user_name: str) -> Optional[str]:
    """获取用户的 OTP 密钥"""
    database = db()
    with database.atomic():
        try:
            user: SysUser = SysUser.get((SysUser.user_name == user_name) & (SysUser.user_status == Status.ENABLE))
            return user.otp_secret
        except DoesNotExist:
            return None


def create_user(
    user_name: str,
    user_full_name: str,
    password: str,
    user_status: bool,
    user_sex: str,
    user_roles: List[str],
    user_email: str,
    phone_number: str,
    user_remark: str,
) -> bool:
    """新建用户"""

    if not user_name or not user_full_name:
        return False
    password = password.strip()
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            SysUser.create(
                user_name=user_name,
                user_full_name=user_full_name,
                password_sha256=hashlib.sha256(password.encode('utf-8')).hexdigest(),
                user_status=user_status,
                user_sex=user_sex,
                user_email=user_email,
                phone_number=phone_number,
                create_by=user_name_op,
                create_datetime=datetime.now(),
                update_by=user_name_op,
                update_datetime=datetime.now(),
                user_remark=user_remark,
                otp_secret='',
            )
            if user_roles:
                SysUserRole.insert_many([{'user_name': user_name, 'role_name': role} for role in user_roles]).execute()
        except IntegrityError as e:
            logger.warning(f'用户{user_name_op}添加用户{user_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def delete_user(user_name: str) -> bool:
    """删除用户"""
    database = db()
    with database.atomic() as txn:
        try:
            # 删除用户角色表中的记录
            SysUserRole.delete().where(SysUserRole.user_name == user_name).execute()
            # 删除团队的用户记录
            SysGroupUser.delete().where(SysGroupUser.user_name == user_name).execute()
            # 删除用户表中的记录
            SysUser.delete().where(SysUser.user_name == user_name).execute()
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}删除用户{user_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def get_roles_from_user_name(user_name: str, exclude_disabled=True) -> List[str]:
    """根据用户查询角色"""
    database = db()

    if isinstance(database, MySQLDatabase):
        roles_agg = fn.JSON_ARRAYAGG(SysRole.role_name).alias('role_names')
    elif isinstance(database, SqliteDatabase):
        roles_agg = fn.GROUP_CONCAT(SysRole.role_name, '○').alias('role_names')
    else:
        raise NotImplementedError('Unsupported database type')

    query = (
        SysUser.select(roles_agg)
        .join(SysUserRole, on=(SysUser.user_name == SysUserRole.user_name))
        .join(SysRole, on=(SysUserRole.role_name == SysRole.role_name))
        .where(SysUser.user_name == user_name)
    )

    if exclude_disabled:
        query = query.where((SysUser.user_status == Status.ENABLE) & (SysRole.role_status == Status.ENABLE))

    result = query.dicts().get()
    if isinstance(database, MySQLDatabase):
        role_names = json.loads(result['role_names']) if result['role_names'] else []
    elif isinstance(database, SqliteDatabase):
        role_names = result['role_names'].split('○') if result['role_names'] else []
    else:
        raise NotImplementedError('Unsupported database type')

    return role_names


def get_user_access_meta(user_name: str, exclude_disabled=True) -> Set[str]:
    """根据用户名查询权限元"""
    database = db()  # 假设你有一个函数 db() 返回当前的数据库连接

    if isinstance(database, MySQLDatabase):
        access_meta_agg = fn.JSON_ARRAYAGG(SysRoleAccessMeta.access_meta).alias('access_metas')
    elif isinstance(database, SqliteDatabase):
        access_meta_agg = fn.GROUP_CONCAT(SysRoleAccessMeta.access_meta, '○').alias('access_metas')
    else:
        raise NotImplementedError('Unsupported database type')

    query = (
        SysUser.select(access_meta_agg)
        .join(SysUserRole, on=(SysUser.user_name == SysUserRole.user_name))
        .join(SysRole, on=(SysUserRole.role_name == SysRole.role_name))
        .join(SysRoleAccessMeta, on=(SysRole.role_name == SysRoleAccessMeta.role_name))
        .where(SysUser.user_name == user_name)
    )

    if exclude_disabled:
        query = query.where((SysUser.user_status == Status.ENABLE) & (SysRole.role_status == Status.ENABLE))

    result = query.dicts().get()
    if isinstance(database, MySQLDatabase):
        access_metas = json.loads(result['access_metas']) if result['access_metas'] else []
    elif isinstance(database, SqliteDatabase):
        access_metas = result['access_metas'].split('○') if result['access_metas'] else []
    else:
        raise NotImplementedError('Unsupported database type')

    return set(access_metas)


@dataclass
class RoleInfo:
    role_name: str
    access_metas: List[str]
    role_status: bool
    update_datetime: datetime
    update_by: str
    create_datetime: datetime
    create_by: str
    role_remark: str


def get_role_info(role_names: Optional[List[str]] = None, exclude_role_admin=False, exclude_disabled=True) -> List[RoleInfo]:
    """获取角色信息"""
    database = db()

    if isinstance(database, MySQLDatabase):
        access_meta_agg = fn.JSON_ARRAYAGG(SysRoleAccessMeta.access_meta).alias('access_metas')
    elif isinstance(database, SqliteDatabase):
        access_meta_agg = fn.GROUP_CONCAT(SysRoleAccessMeta.access_meta, '○').alias('access_metas')
    else:
        raise NotImplementedError('Unsupported database type')

    query = (
        SysRole.select(
            SysRole.role_name, SysRole.role_status, SysRole.update_datetime, SysRole.update_by, SysRole.create_datetime, SysRole.create_by, SysRole.role_remark, access_meta_agg
        )
        .join(SysRoleAccessMeta, JOIN.LEFT_OUTER, on=(SysRole.role_name == SysRoleAccessMeta.role_name))
        .group_by(SysRole.role_name, SysRole.role_status, SysRole.update_datetime, SysRole.update_by, SysRole.create_datetime, SysRole.create_by, SysRole.role_remark)
    )

    if role_names is not None:
        query = query.where(SysRole.role_name.in_(role_names))
    if exclude_role_admin:
        query = query.where(SysRole.role_name != 'admin')
    if exclude_disabled:
        query = query.where(SysRole.role_status == Status.ENABLE)

    role_infos = []
    for role in query.dicts():
        if isinstance(database, MySQLDatabase):
            role['access_metas'] = [i for i in json.loads(role['access_metas']) if i] if role['access_metas'] else []
        elif isinstance(database, SqliteDatabase):
            role['access_metas'] = role['access_metas'].split('○') if role['access_metas'] else []
        else:
            raise NotImplementedError('Unsupported database type')
        role_infos.append(RoleInfo(**role))

    return role_infos


def delete_role(role_name: str) -> bool:
    """删除角色"""
    database = db()
    with database.atomic() as txn:
        try:
            # 删除角色权限表
            SysRoleAccessMeta.delete().where(SysRoleAccessMeta.role_name == role_name).execute()
            # 删除用户角色表
            SysUserRole.delete().where(SysUserRole.role_name == role_name).execute()
            # 删除团队角色表
            SysGroupRole.delete().where(SysGroupRole.role_name == role_name).execute()
            # 删除角色表
            SysRole.delete().where(SysRole.role_name == role_name).execute()
        except IntegrityError as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}删除角色{role_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def create_role(role_name: str, role_status: bool, role_remark: str, access_metas: List[str]) -> bool:
    """新建角色"""
    if not role_name:
        return False
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            SysRole.create(
                role_name=role_name,
                role_status=role_status,
                update_datetime=datetime.now(),
                update_by=user_name_op,
                create_datetime=datetime.now(),
                create_by=user_name_op,
                role_remark=role_remark,
            )
            if access_metas:
                SysRoleAccessMeta.insert_many([{'role_name': role_name, 'access_meta': access_meta} for access_meta in access_metas]).execute()
        except IntegrityError as e:
            logger.warning(f'用户{user_name_op}创建角色{role_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def exists_role_name(role_name: str) -> bool:
    """是否存在角色名称"""
    try:
        SysRole.get(SysRole.role_name == role_name)
        return True
    except DoesNotExist:
        return False


def update_role(role_name: str, role_status: bool, role_remark: str, access_metas: List[str]) -> bool:
    """更新角色"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            # 更新角色信息
            SysRole.update(
                role_status=role_status,
                update_datetime=datetime.now(),
                update_by=user_name_op,
                role_remark=role_remark,
            ).where(SysRole.role_name == role_name).execute()

            # 删除旧的角色权限
            SysRoleAccessMeta.delete().where(SysRoleAccessMeta.role_name == role_name).execute()

            # 插入新的角色权限
            if access_metas:
                SysRoleAccessMeta.insert_many([{'role_name': role_name, 'access_meta': access_meta} for access_meta in access_metas]).execute()
        except IntegrityError as e:
            logger.warning(f'用户{user_name_op}更新角色{role_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


@dataclass
class GroupInfo:
    group_name: str
    group_roles: List[str]
    group_status: bool
    group_users: List[str]
    group_admin_users: List[str]
    update_datetime: datetime
    update_by: str
    create_datetime: datetime
    create_by: str
    group_remark: str


def get_group_info(group_names: Optional[List[str]] = None, exclude_disabled=True) -> List[GroupInfo]:
    """获取团队信息"""
    database = db()

    if isinstance(database, MySQLDatabase):
        roles_agg = fn.JSON_ARRAYAGG(SysGroupRole.role_name).alias('group_roles')
        users_agg = fn.JSON_ARRAYAGG(fn.IF(SysGroupUser.is_admin == Status.ENABLE, fn.CONCAT('is_admin:', SysGroupUser.user_name), SysGroupUser.user_name)).alias('user_name_plus')
    elif isinstance(database, SqliteDatabase):
        roles_agg = fn.GROUP_CONCAT(SysGroupRole.role_name, '○').alias('group_roles')
        users_agg = fn.GROUP_CONCAT(Case(SysGroupUser.is_admin, [(Status.ENABLE, fn.CONCAT('is_admin:', SysGroupUser.user_name))], SysGroupUser.user_name), '○').alias(
            'user_name_plus'
        )
    else:
        raise NotImplementedError('Unsupported database type')
    query_users = (
        SysGroup.select(
            SysGroup.group_name,
            users_agg,
        )
        .join(SysGroupUser, JOIN.LEFT_OUTER, on=(SysGroup.group_name == SysGroupUser.group_name))
        .group_by(SysGroup.group_name)
    )
    query_role = (
        SysGroup.select(
            SysGroup.group_name,
            roles_agg,
        )
        .join(SysGroupRole, JOIN.LEFT_OUTER, on=(SysGroup.group_name == SysGroupRole.group_name))
        .group_by(SysGroup.group_name)
    )
    query = (
        SysGroup.select(
            SysGroup.group_name,
            SysGroup.group_status,
            SysGroup.update_datetime,
            SysGroup.update_by,
            SysGroup.create_datetime,
            SysGroup.create_by,
            SysGroup.group_remark,
            query_role.c.group_roles,
            query_users.c.user_name_plus,
        )
        .join(query_role, on=(SysGroup.group_name == query_role.c.group_name))
        .join(query_users, on=(SysGroup.group_name == query_users.c.group_name))
        .group_by(SysGroup.group_name, SysGroup.group_status, SysGroup.update_datetime, SysGroup.update_by, SysGroup.create_datetime, SysGroup.create_by, SysGroup.group_remark)
    )

    if group_names is not None:
        query = query.where(SysGroup.group_name.in_(group_names))
    if exclude_disabled:
        query = query.where(SysGroup.group_status == Status.ENABLE)

    group_infos = []
    for group in query.dicts():
        if isinstance(database, MySQLDatabase):
            group['group_roles'] = [i for i in set(json.loads(group['group_roles'])) if i] if group['group_roles'] else []
            group['user_name_plus'] = [i for i in set(json.loads(group['user_name_plus'])) if i] if group['user_name_plus'] else []
        elif isinstance(database, SqliteDatabase):
            group['group_roles'] = group['group_roles'].split('○') if group['group_roles'] else []
            group['user_name_plus'] = group['user_name_plus'].split('○') if group['user_name_plus'] else []
        else:
            raise NotImplementedError('Unsupported database type')

        group['group_users'] = [i for i in group['user_name_plus'] if not str(i).startswith('is_admin:')]
        group['group_admin_users'] = [str(i).replace('is_admin:', '') for i in group['user_name_plus'] if str(i).startswith('is_admin:')]
        group.pop('user_name_plus')
        group_infos.append(GroupInfo(**group))

    return group_infos


def is_group_admin(user_name: str) -> bool:
    """判断是不是团队管理员，排除禁用的团队"""
    query = (
        SysGroup.select(fn.COUNT(1))
        .join(SysGroupUser, on=(SysGroup.group_name == SysGroupUser.group_name))
        .where((SysGroupUser.user_name == user_name) & (SysGroup.group_status == Status.ENABLE) & (SysGroupUser.is_admin == Status.ENABLE))
    )

    result = query.scalar()
    return bool(result)


def get_admin_groups_for_user(user_name: str) -> List[str]:
    """获取用户管理的团队名称"""
    query = (
        SysGroupUser.select(SysGroupUser.group_name)
        .join(SysGroup, on=(SysGroup.group_name == SysGroupUser.group_name))
        .where((SysGroupUser.user_name == user_name) & (SysGroupUser.is_admin == Status.ENABLE) & (SysGroup.group_status == Status.ENABLE))
    )
    return [row['group_name'] for row in query.dicts()]


def get_user_and_role_for_group_name(group_name: str):
    """根据团队名称获取成员和对应的角色"""
    database = db()
    if isinstance(database, MySQLDatabase):
        users_agg = fn.JSON_ARRAYAGG(SysGroupUser.user_name).alias('users_agg')
        roles_agg = fn.JSON_ARRAYAGG(SysGroupRole.role_name).alias('roles_agg')
    elif isinstance(database, SqliteDatabase):
        users_agg = fn.GROUP_CONCAT(SysGroupUser.user_name, '○').alias('users_agg')
        roles_agg = fn.GROUP_CONCAT(SysGroupRole.role_name, '○').alias('roles_agg')
    else:
        raise NotImplementedError('Unsupported database type')
    SysGroupUser_query = (
        SysGroupUser.select(SysGroupUser.group_name, users_agg).where(SysGroupUser.group_name == group_name).group_by(SysGroupUser.group_name).alias('SysGroupUser_agg')
    )
    SysGroupRole_query = (
        SysGroupRole.select(SysGroupRole.group_name, roles_agg)
        .join(SysRole, on=(SysGroupRole.role_name == SysRole.role_name))
        .where((SysGroupRole.group_name == group_name) & (SysRole.role_status == Status.ENABLE))
        .group_by(SysGroupRole.group_name)
        .alias('SysGroupRole_agg')
    )
    query = (
        SysGroup.select(SysGroup.group_remark, SysGroupUser_query.c.users_agg, SysGroupRole_query.c.roles_agg)
        .join(SysGroupUser_query, on=(SysGroup.group_name == SysGroupUser_query.c.group_name))
        .join(SysGroupRole_query, on=(SysGroup.group_name == SysGroupRole_query.c.group_name))
        .where((SysGroupUser_query.c.group_name == group_name) & (SysGroup.group_status == Status.ENABLE))
    )
    users = []
    roles = []
    group_remark = ''
    for row in query.dicts():
        if isinstance(database, MySQLDatabase):
            users = json.loads(row['users_agg']) if row['users_agg'] else []
            roles = json.loads(row['roles_agg']) if row['roles_agg'] else []
        elif isinstance(database, SqliteDatabase):
            users = row['users_agg'].split('○') if row['users_agg'] else []
            roles = row['roles_agg'].split('○') if row['roles_agg'] else []
        else:
            raise NotImplementedError('Unsupported database type')
        group_remark = row['group_remark']
    return group_remark, users, roles


def get_dict_group_name_users_roles(user_name) -> Dict[str, Union[str, Set]]:
    """根据用户名获取可管理的团队、人员和可管理的角色，排除禁用的管理员用户"""
    all_ = []
    group_names = get_admin_groups_for_user(user_name=user_name)

    for group_name in group_names:
        group_remark, user_names, group_roles = get_user_and_role_for_group_name(group_name=group_name)
        user_infos = get_user_info(user_names=user_names)
        dict_user_info = {i.user_name: i for i in user_infos}
        for user_name_per, user_info in dict_user_info.items():
            all_.append(
                {
                    'group_remark': group_remark,
                    'group_name': group_name,
                    'user_name': user_name_per,
                    'group_roles': group_roles,
                    'user_roles': list(set(user_info.user_roles) & set(group_roles)),
                    'user_full_name': user_info.user_full_name,
                    'user_status': user_info.user_status,
                }
            )
    return all_


def update_user_roles_from_group(user_name, group_name, roles_in_range):
    """在团队授权页，更新用户权限"""
    is_ok = True
    user_roles = set(get_roles_from_user_name(user_name, exclude_disabled=True))
    roles_in_range = set(roles_in_range)
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        # 新增的权限
        for i in set(roles_in_range) - user_roles:
            is_ok = add_role_for_user(user_name, i, database)
        # 需要删除的权限
        for i in user_roles & (set(get_group_info([group_name], exclude_disabled=True)[0].group_roles) - roles_in_range):
            is_ok = del_role_for_user(user_name, i, database)
        if is_ok:
            txn.commit()
            return True
        else:
            logger.warning(f'用户{user_name_op}修改团队成员{user_name}权限时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False



def exists_group_name(group_name: str) -> bool:
    """是否已经存在这个团队名"""
    try:
        SysGroup.get(SysGroup.group_name == group_name)
        return True
    except DoesNotExist:
        return False


def create_group(group_name: str, group_status: bool, group_remark: str, group_roles: List[str], group_admin_users: List[str], group_users: List[str]) -> bool:
    """添加团队"""
    if exists_group_name(group_name):
        return False
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            # 插入团队表
            SysGroup.create(
                group_name=group_name,
                group_status=group_status,
                update_datetime=datetime.now(),
                update_by=user_name_op,
                create_datetime=datetime.now(),
                create_by=user_name_op,
                group_remark=group_remark,
            )
            # 插入团队角色表
            if group_roles:
                SysGroupRole.insert_many([{'group_name': group_name, 'role_name': role} for role in group_roles]).execute()
            # 插入团队用户表
            user_names = set(group_admin_users + group_users)
            if user_names:
                SysGroupUser.insert_many([{'group_name': group_name, 'user_name': user, 'is_admin': user in group_admin_users} for user in user_names]).execute()
        except IntegrityError as e:
            logger.warning(f'用户{user_name_op}添加团队{group_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def delete_group(group_name: str) -> bool:
    """删除团队"""
    database = db()
    with database.atomic() as txn:
        try:
            # 删除团队角色表中的记录
            SysGroupRole.delete().where(SysGroupRole.group_name == group_name).execute()
            # 删除团队用户表中的记录
            SysGroupUser.delete().where(SysGroupUser.group_name == group_name).execute()
            # 删除团队表中的记录
            SysGroup.delete().where(SysGroup.group_name == group_name).execute()
        except IntegrityError as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}删除团队{group_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_group(group_name: str, group_status: bool, group_remark: str, group_roles: List[str], group_admin_users: List[str], group_users: List[str]) -> bool:
    """更新团队"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()  # 假设你有一个函数 db() 返回当前的数据库连接
    with database.atomic() as txn:
        try:
            # 更新团队信息
            SysGroup.update(group_status=group_status, update_datetime=datetime.now(), update_by=user_name_op, group_remark=group_remark).where(
                SysGroup.group_name == group_name
            ).execute()

            # 删除旧的团队角色
            SysGroupRole.delete().where(SysGroupRole.group_name == group_name).execute()

            # 插入新的团队角色
            if group_roles:
                SysGroupRole.insert_many([{'group_name': group_name, 'role_name': role} for role in group_roles]).execute()

            # 删除旧的团队用户
            SysGroupUser.delete().where(SysGroupUser.group_name == group_name).execute()

            # 插入新的团队用户
            user_names = set(group_admin_users + group_users)
            if user_names:
                SysGroupUser.insert_many([{'group_name': group_name, 'user_name': user, 'is_admin': user in group_admin_users} for user in user_names]).execute()
        except IntegrityError as e:
            logger.warning(f'用户{user_name_op}更新团队{group_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True
