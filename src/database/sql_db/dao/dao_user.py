from database.sql_db.conn import db
from typing import Dict, List, Set, Union, Optional, Iterator
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib
from peewee import DoesNotExist, fn, MySQLDatabase, SqliteDatabase, IntegrityError, JOIN, Case
from loguru import logger
from common.utilities.util_menu_access import get_menu_access
from ..entity.table_user import SysUser, SysRoleAccessMeta, SysUserRole, SysRole



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
