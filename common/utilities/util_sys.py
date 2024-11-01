import time
import shlex
import psutil
import socket
import platform
import os
import cpuinfo
from flask_babel import gettext as _  # noqa
from cacheout import Cache

cache = Cache()


def bytes2human(n, format_str='%(value).1f%(symbol)s'):
    """Used by various scripts. See:
    http://goo.gl/zeJZl

    >>> bytes2human(10000)
    '9.8K'
    >>> bytes2human(100001221)
    '95.4M'
    """
    symbols = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i + 1) * 10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format_str % locals()
    return format_str % dict(symbol=symbols[0], value=n)


cpu_info = cpuinfo.get_cpu_info()
cpu_num = psutil.cpu_count(logical=True)


@cache.memoize(ttl=5, typed=True)
def get_sys_info():
    global cpu_num, cpu_info
    # 获取CPU
    cpu_name: str = cpu_info['brand_raw']
    cpu_num = cpu_num
    cpu_usage_percent = psutil.cpu_times_percent()
    cpu_user_usage_percent: float = cpu_usage_percent.user
    cpu_sys_usage_percent: float = cpu_usage_percent.system
    cpu_all_usage_percent: float = cpu_user_usage_percent + cpu_sys_usage_percent
    cpu_free_percent: float = cpu_usage_percent.idle

    # 内存信息
    memory_info: str = psutil.virtual_memory()
    memory_total: str = bytes2human(memory_info.total)
    memory_used: str = bytes2human(memory_info.used)
    memory_free: str = bytes2human(memory_info.free)
    memory_usage_percent: float = memory_info.percent

    # 主机信息
    hostname: str = socket.gethostname()
    os_name: str = platform.platform()
    computer_name: str = platform.node()
    os_arch: str = platform.machine()

    # python解释器信息
    current_process = psutil.Process(os.getpid())
    python_name: str = current_process.name()
    python_version: str = platform.python_version()
    python_home: str = current_process.exe()
    start_time_stamp = current_process.create_time()
    start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time_stamp))
    current_time_stamp = time.time()
    difference = current_time_stamp - start_time_stamp
    # 将时间差转换为天、小时和分钟数
    days = int(difference // (24 * 60 * 60))  # 每天的秒数
    hours = int((difference % (24 * 60 * 60)) // (60 * 60))  # 每小时的秒数
    minutes = int((difference % (60 * 60)) // 60)  # 每分钟的秒数
    run_time = f'{days}天{hours}小时{minutes}分钟'
    # 获取该进程的内存信息
    current_process_memory_info = psutil.Process(os.getpid()).memory_info()

    # 磁盘信息
    io = psutil.disk_partitions()
    sys_files = []
    for i in io:
        o = psutil.disk_usage(i.device)
        disk_data = dict(
            dir_name=i.device,
            sys_type_name=i.fstype,
            type_name='本地固定磁盘（' + i.mountpoint.replace('\\', '') + '）',
            total=bytes2human(o.total),
            used=bytes2human(o.used),
            free=bytes2human(o.free),
            usage=f'{psutil.disk_usage(i.device).percent}%',
        )
        sys_files.append(disk_data)
    return dict(
        # 系统信息
        hostname=hostname,
        os_name=os_name,
        computer_name=computer_name,
        os_arch=os_arch,
        # cpu
        cpu_name=cpu_name,
        cpu_num=cpu_num,
        cpu_free_percent=cpu_free_percent,
        cpu_user_usage_percent=cpu_user_usage_percent,
        cpu_sys_usage_percent=cpu_sys_usage_percent,
        cpu_all_usage_percent=cpu_all_usage_percent,
        #  内存
        memory_total=memory_total,
        memory_used=memory_used,
        memory_free=memory_free,
        memory_usage_percent=memory_usage_percent,
    )