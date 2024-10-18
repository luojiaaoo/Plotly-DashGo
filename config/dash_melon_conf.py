from configparser import ConfigParser
from pathlib import Path


class PathProj:
    ROOT_PATH = Path(__file__).parent.parent

conf = ConfigParser()
conf.read(PathProj.ROOT_PATH/'config'/'dash_melon.ini')

class FlaskConf:
    COMPRESS_ALGORITHM = conf.get('flask', 'COMPRESS_ALGORITHM')
    COMPRESS_BR_LEVEL = conf.getint('flask', 'COMPRESS_BR_LEVEL')
    COOKIE_SESSION_SECRET_KEY = conf.get('flask', 'COOKIE_SESSION_SECRET_KEY')

class ShowConf:
    WEB_TITLE:str = conf.get('show', 'WEB_TITLE')
    SYSTEM_NAME:str = conf.get('show', 'SYSTEM_NAME')

class JwtConf:
    JWT_SECRET_KEY = conf.get('jwt', 'JWT_SECRET_KEY')
    JWT_ALGORITHM = conf.get('jwt', 'JWT_ALGORITHM')
    JWT_EXPIRE_MINUTES = conf.get('jwt', 'JWT_EXPIRE_MINUTES')