import logging
import os

if os.name == 'nt':
    from concurrent_log_handler import ConcurrentRotatingFileHandler
else:
    from cloghandler import ConcurrentRotatingFileHandler
from config.dashgo_conf import LogConf
# logging.error("An error occurred: %s", e, exc_info=True)


class Log:
    # 创建一个ConcurrentRotatingFileHandler对象
    handler_file = ConcurrentRotatingFileHandler(
        filename=LogConf.LOG_FILE_PATH,
        mode='a',
        maxBytes=1024 * 1024 * LogConf.MAX_MB_PER_LOG_FILE,
        backupCount=LogConf.MAX_COUNT_LOG_FILE,
        encoding='utf-8',
    )
    handler_console = logging.StreamHandler()

    # 设置日志级别
    handler_file.setLevel(eval(f'logging.{LogConf.LOG_LEVEL}'))
    handler_console.setLevel(eval(f'logging.{LogConf.LOG_LEVEL}'))
    # 创建一个格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler_file.setFormatter(formatter)
    handler_console.setFormatter(formatter)

    @classmethod
    def get_logger(cls, logger_name: str) -> logging.Logger:
        logger = logging.getLogger(logger_name)
        logger.setLevel(eval(f'logging.{LogConf.LOG_LEVEL}'))
        if LogConf.HANDLER_LOG_FILE:
            logger.addHandler(cls.handler_file)
        if LogConf.HANDLER_CONSOLE:
            logger.addHandler(cls.handler_console)
        return logger
