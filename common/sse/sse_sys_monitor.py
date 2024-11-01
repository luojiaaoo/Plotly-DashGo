import time
import shlex
from subprocess import Popen, PIPE
import psutil
import random
import socket
import platform
import os
import json

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

def get_sys_info():
            # 获取CPU总核心数
        cpu_num = psutil.cpu_count(logical=True)
        cpu_usage_percent = psutil.cpu_times_percent()
        cpu_used = cpu_usage_percent.user
        cpu_sys = cpu_usage_percent.system
        cpu_free = cpu_usage_percent.idle

        # 内存信息
        memory_info = psutil.virtual_memory()
        memory_total = bytes2human(memory_info.total)
        memory_used = bytes2human(memory_info.used)
        memory_free = bytes2human(memory_info.free)
        memory_usage = memory_info.percent

        # 主机信息
        # 获取主机名
        hostname = socket.gethostname()
        # 获取IP
        computer_ip = socket.gethostbyname(hostname)
        os_name = platform.platform()
        computer_name = platform.node()
        os_arch = platform.machine()
        user_dir = os.path.abspath(os.getcwd())

        # python解释器信息
        current_pid = os.getpid()
        current_process = psutil.Process(current_pid)
        python_name = current_process.name()
        python_version = platform.python_version()
        python_home = current_process.exe()
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
        return f'''
CPU:
核心数：{cpu_num}
用户使用率：{cpu_used}
系统使用率：{cpu_sys}
当前空闲率：{cpu_free}
'''

def get_sys_info_sse():
    while True:
        time.sleep(1)
        yield "data: %s\n\n" % json.dumps(
            {
                "content": get_sys_info().replace("\n", "<line-break>"),
                "timestamp": time.time(),
            }
        )
