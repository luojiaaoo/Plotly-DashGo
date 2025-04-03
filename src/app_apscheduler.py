import rpyc
from rpyc.utils.server import ThreadedServer
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import subprocess
from database.sql_db.dao.dao_apscheduler import insert_apscheduler_result
from config.dashgo_conf import SqlDbConf
import paramiko
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
# https://github.com/agronholm/apscheduler/blob/3.x/examples/rpc/server.py


def run_script(type, script_text, timeout=20, ip=None,username=None, password=None, extract_names=None):
    """
    根据类型执行脚本，支持本地和远程执行。

    参数:
    type (str): 执行类型，'local' 表示本地执行，'ssh' 表示远程执行。
    script_text (str): 要运行的脚本内容或命令。
    ip (str): 远程服务器的 IP 地址（仅在 'ssh' 类型时需要）。
    password (str): SSH 登录密码（仅在 'ssh' 类型时需要）。
    timeout (int): 命令执行的超时时间，单位为秒。
    """
    if type == 'local':
        result = subprocess.run(
            script_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 将标准错误重定向到标准输出
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(result.stdout)
    elif type == 'ssh':
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=ip, username=username, password=password)
            stdin, stdout, stderr = ssh.exec_command(script_text, get_pty=True, timeout=timeout)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            returncode = stdout.channel.recv_exit_status()
            if returncode == 0:
                return f'{output}\n\n### Warning:\n{error}' if error else output
            else:
                raise Exception(f'{output}\n\n### Warning:\n{error}' if error else output)
        except Exception as e:
            raise e
        finally:
            ssh.close()


class SchedulerService(rpyc.Service):
    def exposed_add_job(self, func, *args, **kwargs):
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
        return scheduler.get_jobs(jobstore)

def job_listener(event):
    from apscheduler.events import JobEvent
    if not isinstance(event, JobEvent):
        return
    job_id = event.job_id
    job = scheduler.get_job(event.job_id)
    if event.code == EVENT_JOB_EXECUTED:
        log = event.retval
        status = 'success'
    elif event.code == EVENT_JOB_ERROR:
        log = str(event.exception)
        status = 'error'
    insert_apscheduler_result(job_id, status=status, log=log, extract_names=job.kwargs)

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
    scheduler.add_listener(job_listener)
    scheduler.start()
    protocol_config = {'allow_public_attrs': True}
    server = ThreadedServer(SchedulerService, port=8091, protocol_config=protocol_config)

    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()
