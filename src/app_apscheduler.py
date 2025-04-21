import rpyc
from rpyc.utils.server import ThreadedServer
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import glob
import socket
import subprocess
from database.sql_db.dao.dao_apscheduler import (
    insert_apscheduler_result,
    insert_apscheduler_running,
    insert_apscheduler_extract_value,
    delete_apscheduler_running,
    select_apscheduler_running_log,
    truncate_apscheduler_running,
    delete_expire_data,
)
from common.utilities import util_ssh
from config.dashgo_conf import SqlDbConf, ListenTaskConf
from datetime import datetime, timedelta
import time
from config.dashgo_conf import ApSchedulerConf
from common.listen import active_listen
from queue import Queue
from itertools import count
import threading
import json
import re
import platform
import os
import tempfile
from multiprocessing import Manager,freeze_support
# https://github.com/agronholm/apscheduler/blob/3.x/examples/rpc/server.py


SUFFIX = {'Bat': '.bat', 'Shell': '.sh', 'Python': '.py'}
RUN_CMD = {'Bat': ['cmd', '/c'], 'Shell': ['sh'], 'Python': ['python']}


def run_script(
    type,
    script_text,
    script_type,
    job_id,
    notify_channels,
    extract_names=None,
    timeout=20,
    host=None,
    port=22,
    username=None,
    password=None,
    update_by=None,
    update_datetime=None,
    create_by=None,
    create_datetime=None,
    env_vars=None,
):
    """
    根据类型执行脚本，支持本地和远程执行。

    参数:
    type (str): run-type执行类型，'local' 表示本地执行，'ssh' 表示远程执行。
    script_text (str): 要运行的脚本内容或命令。
    host (str): 远程服务器的 host 地址（仅在 'ssh' 类型时需要）。
    password (str): SSH 登录密码（仅在 'ssh' 类型时需要）。
    timeout (int): 命令执行的超时时间，单位为秒。
    """
    start_datetime = datetime.now()
    extract_names = json.loads(extract_names)
    notify_channels = json.loads(notify_channels)
    output_full = ''

    def pop_from_stdout(stdout, event: threading.Event, queue_stdout: Queue, encoding='utf8'):
        while not event.is_set():
            try:  # ugly fix: 避免ssh命令超时后，这里疯狂报错
                line = stdout.readline()
                if isinstance(line, bytes):
                    queue_stdout.put(line.decode(encoding, errors='ignore'))
                else:
                    queue_stdout.put(line)
            except:
                ...

    def pop_from_stderr(stderr, event: threading.Event, queue_stderr: Queue, encoding='utf8'):
        while not event.is_set():
            try:  # ugly fix: 避免ssh命令超时后，这里疯狂报错
                line = stderr.readline()
                if isinstance(line, bytes):
                    queue_stderr.put(line.decode(encoding, errors='ignore'))
                else:
                    queue_stderr.put(line)
            except:
                ...

    suffix = SUFFIX[script_type]
    run_cmd = RUN_CMD[script_type]
    if type == 'local':
        # 如果本地是中文版windows的话，需要gbk解码
        encoding = 'gbk' if suffix == '.bat' else 'utf-8'
        # 创建文件
        with tempfile.NamedTemporaryFile(
            delete=False,
            mode='w',
            dir=tempfile.gettempdir(),
            prefix='dashgo_',
            suffix=suffix,
            encoding=encoding,
        ) as f:
            f.write(script_text)
            f.flush()
            script_filepath = f.name
        process = subprocess.Popen(
            [*run_cmd, script_filepath],
            shell=True,
            env={**os.environ.copy(), **env_vars} if env_vars else os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=False,
        )
        queue_stdout = Queue()
        queue_stderr = Queue()
        event = threading.Event()
        thread_stdout = threading.Thread(target=pop_from_stdout, args=(process.stdout, event, queue_stdout, encoding))
        thread_stderr = threading.Thread(target=pop_from_stderr, args=(process.stderr, event, queue_stderr, encoding))
        thread_stdout.daemon = True
        thread_stderr.daemon = True
        thread_stdout.start()
        thread_stderr.start()
        order = 0
        is_timeout = False
        for i in count():
            if i % 2 == 0:  # 1秒读一次数据
                output_list = []
                output_list.extend(queue_stdout.get() for _ in range(queue_stdout.qsize()))
                output_list.extend(queue_stderr.get() for _ in range(queue_stderr.qsize()))
                if output := ''.join(output_list):
                    insert_apscheduler_running(
                        job_id=job_id,
                        log=output,
                        order=order,
                        start_datetime=start_datetime,
                    )
                    output_full += output
                    if extract_names and (search_sops_var := re.search(r'<SOPS_VAR>.+</SOPS_VAR>', output_full)):
                        # 发现了<SOPS_VAR>标签，进行提取
                        insert_apscheduler_extract_value(
                            job_id=job_id,
                            log=output,
                            start_datetime=start_datetime,
                            extract_names=extract_names,
                            notify_channels=notify_channels,
                        )
                        output_full = output_full[search_sops_var.end() :]  # 清除已经提取的内容
                    order += 1
            if process.poll() is not None and output == '':
                break
            if datetime.now() - start_datetime > timedelta(seconds=timeout):  # 每1秒检查一次是否超时
                process.kill()
                is_timeout = True
                break
            time.sleep(0.5)
        time.sleep(0.5)  # 多等待0.5秒，保证多线程的日志读取完成
        event.set()
        output_list = []
        output_list.extend(queue_stdout.get() for _ in range(queue_stdout.qsize()))
        output_list.extend(queue_stderr.get() for _ in range(queue_stderr.qsize()))
        if output := ''.join(output_list):
            insert_apscheduler_running(
                job_id=job_id,
                log=output,
                order=order,
                start_datetime=start_datetime,
            )
            output_full += output
            if extract_names and (search_sops_var := re.search(r'<SOPS_VAR>.+</SOPS_VAR>', output_full)):
                # 发现了<SOPS_VAR>标签，进行提取
                insert_apscheduler_extract_value(
                    job_id=job_id,
                    log=output,
                    start_datetime=start_datetime,
                    extract_names=extract_names,
                    notify_channels=notify_channels,
                )
        if is_timeout:
            log = select_apscheduler_running_log(job_id=job_id, start_datetime=start_datetime)
            insert_apscheduler_result(
                job_id,
                status='timeout',
                log=log,
                start_datetime=start_datetime,
            )
            err_name = f'[ERROR] {job_id} Local Script Execute Timeout'
            err_log = f'<SOPS_VAR>{err_name}: {log}</SOPS_VAR>'
            insert_apscheduler_extract_value(
                job_id=job_id,
                log=err_log,
                start_datetime=start_datetime,
                extract_names=[{'type': 'notify', 'name': err_name}],
                notify_channels=notify_channels,
            )
        else:
            return_code = process.wait()
            log = select_apscheduler_running_log(job_id=job_id, start_datetime=start_datetime)
            insert_apscheduler_result(
                job_id,
                status='success' if return_code == 0 else 'error',
                log=log,
                start_datetime=start_datetime,
            )
            if return_code != 0:
                err_name = f'[ERROR] {job_id} Local Script Execute Failed'
                err_log = f'<SOPS_VAR>{err_name}: {log}</SOPS_VAR>'
                insert_apscheduler_extract_value(
                    job_id=job_id,
                    log=err_log,
                    start_datetime=start_datetime,
                    extract_names=[{'type': 'notify', 'name': err_name}],
                    notify_channels=notify_channels,
                )
        delete_apscheduler_running(job_id=job_id, start_datetime=start_datetime)
        # 删除旧的脚本文件
        script_filepath_old = glob.glob(os.path.join(tempfile.gettempdir(), 'dashgo_*'))
        try:
            script_filepath_old.sort(key=os.path.getmtime, reverse=True)
            for i in script_filepath_old[30:]:  # 最多只保留30个脚本文件
                os.remove(i)
        except Exception as e:
            pass
    elif type == 'ssh':
        # ssh默认都认为是linux系统
        with tempfile.NamedTemporaryFile(
            delete=False,
            mode='w',
            dir=tempfile.gettempdir(),
            prefix=f'dashgo_{datetime.now().timestamp()}',
            suffix=suffix,
            encoding='utf-8',
        ) as f:
            f.write('\n'.join(['export ' + key + '="' + value + '"' for key, value in env_vars.items()]) + '\n')  # 设置环境变量
            f.write(script_text)
            f.flush()
            script_filepath = f.name
        try:
            ssh = util_ssh.connect_ssh(hostname=host, port=port, username=username, password=password)
            util_ssh.ftp_ssh(ssh, script_filepath, '/tmp')  # 上传脚本到远程/tmp目录
            os.remove(script_filepath)  # 清理本地临时文件
            try:
                stdin, stdout, stderr = ssh.exec_command(f'{" ".join(run_cmd)} /tmp/{os.path.basename(script_filepath)}', get_pty=True, timeout=timeout)
                queue_stdout = Queue()
                queue_stderr = Queue()
                event = threading.Event()
                thread_stdout = threading.Thread(target=pop_from_stdout, args=(stdout, event, queue_stdout))
                thread_stderr = threading.Thread(target=pop_from_stderr, args=(stderr, event, queue_stderr))
                thread_stdout.daemon = True
                thread_stderr.daemon = True
                thread_stdout.start()
                thread_stderr.start()
                order = 0
                for i in count():
                    if i % 2 == 0:  # 等待1秒钟读取一次日志
                        output_list = []
                        output_list.extend(queue_stdout.get() for _ in range(queue_stdout.qsize()))
                        output_list.extend(queue_stderr.get() for _ in range(queue_stderr.qsize()))
                        if output := ''.join(output_list):
                            insert_apscheduler_running(
                                job_id=job_id,
                                log=output,
                                order=order,
                                start_datetime=start_datetime,
                            )
                            output_full += output
                            if extract_names and (search_sops_var := re.search(r'<SOPS_VAR>.+</SOPS_VAR>', output_full)):
                                # 发现了<SOPS_VAR>标签，进行提取
                                insert_apscheduler_extract_value(
                                    job_id=job_id,
                                    log=output,
                                    start_datetime=start_datetime,
                                    extract_names=extract_names,
                                    notify_channels=notify_channels,
                                )
                                output_full = output_full[search_sops_var.end() :]  # 清除已经提取的内容
                            order += 1
                    if stdout.channel.exit_status_ready() and output == '':
                        break
                    time.sleep(0.5)
                time.sleep(0.5)  # 多等待0.5秒，保证多线程的日志读取完成
                event.set()
                output_list = []
                output_list.extend(queue_stdout.get() for _ in range(queue_stdout.qsize()))
                output_list.extend(queue_stderr.get() for _ in range(queue_stderr.qsize()))
                if output := ''.join(output_list):
                    insert_apscheduler_running(
                        job_id=job_id,
                        log=output,
                        order=order,
                        start_datetime=start_datetime,
                    )
                    output_full += output
                    if extract_names and (search_sops_var := re.search(r'<SOPS_VAR>.+</SOPS_VAR>', output_full)):
                        # 发现了<SOPS_VAR>标签，进行提取
                        insert_apscheduler_extract_value(
                            job_id=job_id,
                            log=output,
                            start_datetime=start_datetime,
                            extract_names=extract_names,
                            notify_channels=notify_channels,
                        )
                stdout.readline()  # 尝试读一下，如果是超时的异常，则会抛出socket.timeout
            except socket.timeout:
                # 超时
                log = select_apscheduler_running_log(job_id=job_id, start_datetime=start_datetime)
                insert_apscheduler_result(
                    job_id,
                    status='timeout',
                    log=log,
                    start_datetime=start_datetime,
                )
                err_name = f'[ERROR] {job_id} Ssh Script Execute Timeout'
                err_log = f'<SOPS_VAR>{err_name}: {log}</SOPS_VAR>'
                insert_apscheduler_extract_value(
                    job_id=job_id,
                    log=err_log,
                    start_datetime=start_datetime,
                    extract_names=[{'type': 'notify', 'name': err_name}],
                    notify_channels=notify_channels,
                )
                return
            return_code = stdout.channel.recv_exit_status()
            # 执行成功 or 失败
            log = select_apscheduler_running_log(job_id=job_id, start_datetime=start_datetime)
            insert_apscheduler_result(
                job_id,
                status='success' if return_code == 0 else 'error',
                log=log,
                start_datetime=start_datetime,
            )
            if return_code != 0:
                err_name = f'[ERROR] {job_id} Ssh Script Execute Fail'
                err_log = f'<SOPS_VAR>{err_name}: {log}</SOPS_VAR>'
                insert_apscheduler_extract_value(
                    job_id=job_id,
                    log=err_log,
                    start_datetime=start_datetime,
                    extract_names=[{'type': 'notify', 'name': err_name}],
                    notify_channels=notify_channels,
                )
        except TimeoutError:
            err_name = f'[ERROR] SSH connect error from {job_id}'
            err_log = f'<SOPS_VAR>{err_name}: Cannot connect to the host {host}</SOPS_VAR>'
            insert_apscheduler_result(
                job_id,
                status='error',
                log=err_log,
                start_datetime=start_datetime,
            )
            insert_apscheduler_extract_value(
                job_id=job_id,
                log=err_log,
                start_datetime=start_datetime,
                extract_names=[{'type': 'notify', 'name': err_name}],
                notify_channels=notify_channels,
            )
        except Exception as e:
            raise e
        else:
            delete_apscheduler_running(job_id=job_id, start_datetime=start_datetime)
            ssh.exec_command("ls /tmp/dashgo_*|sort -r|sed '1,30d'|xargs -n 30 rm -f", get_pty=True, timeout=20)  # 清理历史脚本，最多保留30个
        finally:
            ssh.close()


CLEAR_JOB_ID = 'sys_delete_expire_data_for_cron'
LISTEN_JOB_ID = 'sys_listen_interval_job'


class SchedulerService(rpyc.Service):
    def exposed_add_job(self, func, *args, **kwargs):
        kwargs = dict(kwargs)
        kwargs['kwargs'] = list(kwargs['kwargs'])
        kwargs['kwargs'].append(('job_id', kwargs['id']))  # 给函数传递job_id参数
        is_pause = False
        if kwargs.get('is_pause', None):
            is_pause = True
        if kwargs.get('is_pause', ...) != ...:
            kwargs.pop('is_pause')
        job = scheduler.add_job(func, *args, **kwargs)
        if is_pause:
            job.pause()
        return job

    def exposed_modify_job(self, job_id, jobstore=None, **changes):
        return scheduler.modify_job(job_id, jobstore, **changes)

    def exposed_reschedule_job(self, job_id, jobstore=None, trigger=None, **trigger_args):
        return scheduler.reschedule_job(job_id, jobstore, trigger, **trigger_args)

    def exposed_pause_job(self, job_id, jobstore=None):
        return scheduler.pause_job(job_id, jobstore)

    def exposed_resume_job(self, job_id, jobstore=None):
        return scheduler.resume_job(job_id, jobstore)

    def exposed_remove_job(self, job_id, jobstore=None):
        scheduler.remove_job(job_id, jobstore)

    def exposed_get_job(self, job_id):
        job = scheduler.get_job(job_id)
        if job:
            return json.dumps(self.get_job_dict(job))
        else:
            return None

    def exposed_get_platform(self):
        return platform.system()

    def exposed_get_jobs(self, jobstore=None):
        jobs = scheduler.get_jobs(jobstore)
        result = []
        for job in jobs:
            if job.id in (CLEAR_JOB_ID, LISTEN_JOB_ID):
                continue
            result.append(self.get_job_dict(job))
        return json.dumps(result, ensure_ascii=False)

    @staticmethod
    def get_job_dict(job):
        if isinstance(job.trigger, IntervalTrigger):
            plan = {
                'seconds': job.trigger.interval_length,
            }
            trigger = 'interval'
        elif isinstance(job.trigger, CronTrigger):
            plan = {
                # 'second': job.trigger.fields[CronTrigger.FIELD_NAMES.index('second')].__str__(),
                'minute': job.trigger.fields[CronTrigger.FIELD_NAMES.index('minute')].__str__(),
                'hour': job.trigger.fields[CronTrigger.FIELD_NAMES.index('hour')].__str__(),
                'day': job.trigger.fields[CronTrigger.FIELD_NAMES.index('day')].__str__(),
                'month': job.trigger.fields[CronTrigger.FIELD_NAMES.index('month')].__str__(),
                'day_of_week': job.trigger.fields[CronTrigger.FIELD_NAMES.index('day_of_week')].__str__(),
            }
            trigger = 'cron'
        else:
            raise Exception('不支持的触发器类型')
        return {
            'id': job.id,
            'status': job.next_run_time is not None,
            'next_run_time': f'{job.next_run_time:%Y-%m-%dT%H:%M:%S}' if job.next_run_time else '-',
            'kwargs': job.kwargs,
            'trigger': trigger,
            'plan': plan,
        }


def delete_expire_data_for_cron(day):
    delete_expire_data(day)


def add_clear_job(scheduler):
    # 添加清理作业
    try:
        scheduler.remove_job(CLEAR_JOB_ID)
        print('清理作业删除成功')
    except:
        pass
    scheduler.add_job(
        'app_apscheduler:delete_expire_data_for_cron',
        'cron',
        kwargs=[
            ('day', ApSchedulerConf.DATA_EXPIRE_DAY),
        ],
        year='*',
        week='*',
        second=0,
        minute=0,
        hour=1,
        day='*',
        month='*',
        day_of_week='*',
        id=CLEAR_JOB_ID,
    )
    print(f'清理作业添加成功，保留天数为{ApSchedulerConf.DATA_EXPIRE_DAY}')


def listen_interval(shared_datetime):
    active_listen(shared_datetime=shared_datetime)


def add_listen_job(scheduler):
    # 添加监听作业
    try:
        scheduler.remove_job(LISTEN_JOB_ID)
        print('主动监听作业删除成功')
    except:
        pass
    interval = ListenTaskConf.PERIOD_MINTUES * 60
    scheduler.add_job(
        'app_apscheduler:listen_interval',
        'interval',
        kwargs=[
            ('shared_datetime', shared_datetime),
        ],
        seconds=interval,
        id=LISTEN_JOB_ID,
    )
    print(f'主动监听作业添加成功，扫描周期为{interval}秒')


if __name__ == '__main__':
    if platform.system() == 'Windows':
        freeze_support()
    manager = Manager()
    shared_datetime = manager.dict({'last_datetime': datetime.now() - timedelta(minutes=ListenTaskConf.PERIOD_MINTUES)})
    if SqlDbConf.RDB_TYPE == 'sqlite':
        jobstores = {'default': SQLAlchemyJobStore(url=f'sqlite:///{SqlDbConf.SQLITE_DB_PATH}?timeout=20')}
    elif SqlDbConf.RDB_TYPE == 'mysql':
        jobstores = {'default': SQLAlchemyJobStore(url=f'mysql+pymysql://{SqlDbConf.USER}:{SqlDbConf.PASSWORD}@{SqlDbConf.HOST}:{SqlDbConf.PORT}/{SqlDbConf.DATABASE}')}
    truncate_apscheduler_running()
    executors = {
        'default': ThreadPoolExecutor(64),
    }
    job_defaults = {'coalesce': True, 'max_instances': 8}
    scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
    scheduler.start()
    protocol_config = {'allow_public_attrs': True}
    server = ThreadedServer(SchedulerService, hostname=ApSchedulerConf.HOST, port=ApSchedulerConf.PORT, protocol_config=protocol_config)
    add_clear_job(scheduler)
    add_listen_job(scheduler)
    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        server.close()
        scheduler.shutdown()
