import rpyc
from rpyc.utils.server import ThreadedServer
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.interval import IntervalTrigger
import subprocess
from database.sql_db.dao.dao_apscheduler import insert_apscheduler_result, insert_apscheduler_running, delete_apscheduler_running, select_apscheduler_running_log
from config.dashgo_conf import SqlDbConf
import paramiko
from datetime import datetime, timedelta
import time
import itertools
from queue import Queue
import threading
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
# https://github.com/agronholm/apscheduler/blob/3.x/examples/rpc/server.py


def run_script(type, script_text, job_id, update_by, update_datetime, create_by, create_datetime, timeout=20, ip=None, username=None, password=None, extract_names=None):
    """
    根据类型执行脚本，支持本地和远程执行。

    参数:
    type (str): 执行类型，'local' 表示本地执行，'ssh' 表示远程执行。
    script_text (str): 要运行的脚本内容或命令。
    ip (str): 远程服务器的 IP 地址（仅在 'ssh' 类型时需要）。
    password (str): SSH 登录密码（仅在 'ssh' 类型时需要）。
    timeout (int): 命令执行的超时时间，单位为秒。
    """
    start_datetime = datetime.now()

    def pop_from_stdout(stdout, event: threading.Event, queue_stdout: Queue):
        while not event.is_set():
            queue_stdout.put(stdout.readline().decode('utf-8', errors='ignore'))

    def pop_from_stderr(stderr, event: threading.Event, queue_stderr: Queue):
        while not event.is_set():
            queue_stderr.put(stderr.readline().decode('utf-8', errors='ignore'))

    if type == 'local':
        process = subprocess.Popen(
            script_text,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=False,
        )
        queue_stdout = Queue()
        queue_stderr = Queue()
        event = threading.Event()
        thread_stdout = threading.Thread(target=pop_from_stdout, args=(process.stdout, event, queue_stdout))
        thread_stderr = threading.Thread(target=pop_from_stderr, args=(process.stderr, event, queue_stderr))
        thread_stdout.daemon = True
        thread_stderr.daemon = True
        thread_stdout.start()
        thread_stderr.start()
        order = 0
        while True:
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
                order += 1
            if process.poll() is not None and output == '':
                break
            if datetime.now() - start_datetime > timedelta(seconds=timeout):
                process.kill()
                break
            time.sleep(2)  # 等待2秒钟读取一次日志
        time.sleep(1)
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
        return_code = process.wait()
        log = select_apscheduler_running_log(job_id=job_id, start_datetime=start_datetime)
        insert_apscheduler_result(
            job_id,
            status='success' if return_code == 0 else 'error',
            log=log,
            start_datetime=start_datetime,
            extract_names=extract_names,
        )
        delete_apscheduler_running(job_id=job_id, start_datetime=start_datetime)

    elif type == 'ssh':
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=ip, username=username, password=password)
            stdin, stdout, stderr = ssh.exec_command(script_text, get_pty=True, timeout=timeout)
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
            while True:
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
                    order += 1
                if stdout.channel.exit_status_ready() and output == '':
                    break
                time.sleep(2)  # 等待2秒钟读取一次日志
            time.sleep(1)
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
            return_code = stdout.channel.recv_exit_status()
            log = select_apscheduler_running_log(job_id=job_id, start_datetime=start_datetime)
            insert_apscheduler_result(
                job_id,
                status='success' if return_code == 0 else 'error',
                log=log,
                start_datetime=start_datetime,
                extract_names=extract_names,
            )
        except Exception as e:
            raise e
        finally:
            delete_apscheduler_running(job_id=job_id, start_datetime=start_datetime)
            ssh.close()


class SchedulerService(rpyc.Service):
    def exposed_add_job(self, func, *args, **kwargs):
        kwargs['kwargs'] = list(kwargs['kwargs'])
        kwargs['kwargs'].append(('job_id', kwargs['id']))  # 给函数传递job_id参数
        return scheduler.add_job(func, *args, **kwargs)

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
        return scheduler.get_job(job_id)

    def exposed_get_jobs(self, jobstore=None):
        import json

        jobs = scheduler.get_jobs(jobstore)
        result = []
        for job in jobs:
            if isinstance(job.trigger, IntervalTrigger):
                plan = {
                    'seconds': job.trigger.interval_length,
                }
                trigger = 'interval'
            else:
                plan = (
                    {
                        'second': job.trigger.second,
                        'minute': job.trigger.minute,
                        'hour': job.trigger.hour,
                        'day': job.trigger.day,
                        'month': job.trigger.month,
                        'day_of_week': job.trigger.day_of_week,
                    },
                )
                trigger = 'cron'
            result.append(
                {
                    'id': job.id,
                    'status': job.next_run_time is not None,
                    'next_run_time': f'{job.next_run_time:%Y-%m-%dT%H:%M:%S}' if job.next_run_time else '',
                    'kwargs': job.kwargs,
                    'trigger': trigger,
                    'plan': plan,
                }
            )
        return json.dumps(result, ensure_ascii=False)


if __name__ == '__main__':
    if SqlDbConf.RDB_TYPE == 'sqlite':
        jobstores = {'default': SQLAlchemyJobStore(url=f'sqlite:///{SqlDbConf.SQLITE_DB_PATH}')}
    elif SqlDbConf.RDB_TYPE == 'mysql':
        jobstores = {'default': SQLAlchemyJobStore(url=f'mysql+pymysql://{SqlDbConf.USER}:{SqlDbConf.PASSWORD}@{SqlDbConf.HOST}:{SqlDbConf.PORT}/{SqlDbConf.DATABASE}')}

    executors = {
        'default': ThreadPoolExecutor(20),
    }
    job_defaults = {'coalesce': True, 'max_instances': 10}
    scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
    scheduler.start()
    protocol_config = {'allow_public_attrs': True}
    server = ThreadedServer(SchedulerService, port=8091, protocol_config=protocol_config)

    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        server.close()
        scheduler.shutdown()
