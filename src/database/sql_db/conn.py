from config.dashgo_conf import SqlDbConf
from playhouse.pool import PooledMySQLDatabase
from server import server
from playhouse.shortcuts import ReconnectMixin
from .entity.table_user import SysUser, SysRoleAccessMeta, SysUserRole, SysGroupUser, SysRole, SysGroupRole, SysGroup


# 断线重连+连接池
class ReconnectPooledMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):
    _instance = None

    @classmethod
    def get_db_instance(cls):
        if not cls._instance:
            cls._instance = cls(
                database=SqlDbConf.DATABASE,
                max_connections=SqlDbConf.POOL_SIZE,
                user=SqlDbConf.USER,
                password=SqlDbConf.PASSWORD,
                host=SqlDbConf.HOST,
                port=SqlDbConf.PORT,
                stale_timeout=300,
            )
        return cls._instance


def db():
    return ReconnectPooledMySQLDatabase.get_db_instance()


# 判断是否存在SysUser表，如不存在则初始化库
def initialize_database():
    db_instance = db()
    if not db_instance.table_exists('sys_user'):
        db_instance.create_tables(
            [
                SysUser,
                SysRoleAccessMeta,
                SysUserRole,
                SysGroupUser,
                SysRole,
                SysGroupRole,
                SysGroup,
            ]
        )


initialize_database()


# 自动管理数据库上下文
@server.before_request
def _db_connect():
    db().connect(reuse_if_open=True)


@server.teardown_request
def _db_close(exc):
    _db = db()
    if not _db.is_closed():
        _db.close()
