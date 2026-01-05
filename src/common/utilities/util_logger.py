from loguru import logger
from config.dashgo_conf import LogConf
import asyncio
import functools
import inspect
import time
import traceback


logger.remove()

logger.add(
    sink=LogConf.LOG_FILE_PATH,
    encoding="utf-8",
    level=LogConf.LOG_LEVEL,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "  # 时间（精确到毫秒）
        "<level>{level: <8}</level> | "  # 日志级别（对齐宽度）
        # "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "  # 模块名:函数名:行号
        # "PID:{process.id} | TID:{thread.id} | "  # 进程ID和线程ID
        "<level>{message}</level>"  # 日志消息
    ),
    colorize=False,  # 关闭颜色
    backtrace=True,  # 允许记录异常堆栈
    diagnose=False,  # 显示变量值（调试用）
    enqueue=True,
)


class Timer(object):
    def __init__(self, key: str):
        self.key = key

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"{self.key} start...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"{self.key} error={traceback.format_exc()}")
            return False
        else:
            logger.info(
                f"{self.key} cost=[{int((time.time() - self.start_time) * 1000)} ms]"
            )
            return True


class AsyncTimer(object):
    def __init__(self, key: str):
        self.key = key

    async def __aenter__(self):
        self.start_time = time.time()
        logger.info(f"{self.key} start...")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"{self.key} error={traceback.format_exc()}")
        else:
            logger.info(
                f"{self.key} cost=[{int((time.time() - self.start_time) * 1000)} ms]"
            )


class TimeMonitor:
    def __init__(self, key=""):
        self.key = key

    def __call__(self, func):
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                async with AsyncTimer(f"{self.key} {func.__name__}"):
                    result = await func(*args, **kwargs)
                return result

            return wrapper
        elif inspect.isasyncgenfunction(func):

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                async with AsyncTimer(f"{self.key} {func.__name__}"):
                    async for element in func(*args, **kwargs):
                        yield element

            return wrapper
        else:

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with Timer(f"{self.key} {func.__name__}"):
                    result = func(*args, **kwargs)
                return result

            return wrapper
