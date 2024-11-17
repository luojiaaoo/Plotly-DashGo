from config.dash_melon_conf import SqlDbConf
from playhouse.pool import PooledMySQLDatabase


db = PooledMySQLDatabase(
    database=SqlDbConf.DATABASE,
    max_connections=SqlDbConf.POOL_SIZE,
    user=SqlDbConf.USER,
    password=SqlDbConf.PASSWORD,
    host=SqlDbConf.HOST,
    port=SqlDbConf.PORT,
    stale_timeout=300,
)
