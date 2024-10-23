from configparser import ConfigParser
from pathlib import Path


class PathProj:
    ROOT_PATH = Path(__file__).parent.parent

conf = ConfigParser()
conf.read(PathProj.ROOT_PATH/'config'/'dash_melon.ini')

class EncryptConf:
    CUSTOM_KEY = conf.get('encrypt', 'CUSTOM_KEY')

class LoginConf:
    VERIFY_CODE_SHOW_LOGIN_FAIL_COUNT = conf.getint('login', 'VERIFY_CODE_SHOW_LOGIN_FAIL_COUNT')
    VERIFY_CODE_CHAR_NUM = conf.getint('login', 'VERIFY_CODE_CHAR_NUM')

class FlaskConf:
    COMPRESS_ALGORITHM = conf.get('flask', 'COMPRESS_ALGORITHM')
    COMPRESS_BR_LEVEL = conf.getint('flask', 'COMPRESS_BR_LEVEL')
    COOKIE_SESSION_SECRET_KEY = conf.get('flask', 'COOKIE_SESSION_SECRET_KEY')

class ShowConf:
    WEB_TITLE:str = conf.get('show', 'WEB_TITLE')
    APP_NAME:str = conf.get('show', 'APP_NAME')

class JwtConf:
    JWT_SECRET_KEY = conf.get('jwt', 'JWT_SECRET_KEY')
    JWT_ALGORITHM = conf.get('jwt', 'JWT_ALGORITHM')
    JWT_EXPIRE_MINUTES = conf.getint('jwt', 'JWT_EXPIRE_MINUTES')

class SqlDbConf:
    HOST = conf.get('sql_db', 'HOST')
    PORT = conf.getint('sql_db', 'PORT')
    USER = conf.get('sql_db', 'USER')
    PASSWORD = conf.get('sql_db', 'PASSWORD')
    DATABASE = conf.get('sql_db', 'DATABASE')
    CHARSET = conf.get('sql_db', 'CHARSET')
    POOL_SIZE = conf.getint('sql_db', 'POOL_SIZE')