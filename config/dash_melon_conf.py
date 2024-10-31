from configparser import ConfigParser
from pathlib import Path
from typing import List


class PathProj:
    ROOT_PATH = Path(__file__).parent.parent
    CONF_FILE_PATH = ROOT_PATH / 'config' / 'dash_melon.ini'
    AVATAR_DIR_PATH = ROOT_PATH / 'user_data' / 'avatars'


conf = ConfigParser()
conf.read(PathProj.CONF_FILE_PATH)


class BaseMetaConf(type):
    def __new__(cls, name, bases, dct):
        sub_conf = conf[name]
        for stat_var_name, type_ in dct['__annotations__'].items():
            if sub_conf.get(stat_var_name) is not None:
                if type_ is List:
                    dct[stat_var_name] = sub_conf.get(stat_var_name).split()
                elif type_ is bool:
                    dct[stat_var_name] = eval(sub_conf.get(stat_var_name))
                else:
                    dct[stat_var_name] = type_(sub_conf.get(stat_var_name))
        return super().__new__(cls, name, bases, dct)


class LogConf(metaclass=BaseMetaConf):
    LOG_LEVEL: str = 'WARNING'
    HANDLER_CONSOLE: bool = True
    HANDLER_LOG_FILE: bool = False
    LOG_FILE_PATH: str
    MAX_MB_PER_LOG_FILE: int = 50
    MAX_COUNT_LOG_FILE: int = 3


class BabelConf(metaclass=BaseMetaConf):
    BABEL_DEFAULT_LOCALE: str = 'zh'
    BABEL_DEFAULT_TIMEZONE: str = 'Asia/Shanghai'
    BABEL_TRANSLATION_DIRECTORIES: str = '**/translations'
    LANGUAGES: List = ['zh', 'en']


class CommonConf(metaclass=BaseMetaConf):
    ENCRYPT_KEY: str
    DASH_SERVE_LOCALLY: bool


class LoginConf(metaclass=BaseMetaConf):
    VERIFY_CODE_SHOW_LOGIN_FAIL_COUNT: int = 5
    VERIFY_CODE_CHAR_NUM: int = 4
    JWT_EXPIRED_FORCE_LOGOUT: bool = False


class FlaskConf(metaclass=BaseMetaConf):
    COMPRESS_ALGORITHM: str = 'br'
    COMPRESS_BR_LEVEL: int = 9
    COOKIE_SESSION_SECRET_KEY: str


class ShowConf(metaclass=BaseMetaConf):
    WEB_TITLE: str
    APP_NAME: str


class JwtConf(metaclass=BaseMetaConf):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRE_MINUTES: int = 1440


class SqlDbConf(metaclass=BaseMetaConf):
    HOST: str
    PORT: int
    USER: str
    PASSWORD: str
    DATABASE: str
    CHARSET: str
    POOL_SIZE: int
