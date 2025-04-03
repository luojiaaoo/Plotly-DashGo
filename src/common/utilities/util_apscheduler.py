import rpyc


def add_ssh_interval_job(ip, username, password, script_text, interval, timeout, job_id, extract_names):
    try:
        conn = rpyc.connect('localhost', 8091)
        job = conn.root.add_job(
            'app_apscheduler:run_script',
            'interval',
            kwargs=dict(
                type='ssh',
                script_text=script_text,
                timeout=timeout,
                ip=ip,
                username=username,
                password=password,
                extract_names=extract_names,
            ),
            seconds=interval,
            id=job_id,
        )
        return job.id
    except Exception as e:
        raise e
    finally:
        conn.close()


def add_ssh_cron_job(ip, username, password, script_text, cron_text, timeout, job_id, extract_names, year=None, week=None):
    """https://apscheduler.readthedocs.io/en/master/api.html#apscheduler.triggers.cron.CronTrigger"""
    try:
        conn = rpyc.connect('localhost', 8091)
        if len(cron_text) == 5:
            minute, hour, day, month, day_of_week = cron_text
            second = None
        elif len(cron_text) == 6:
            second, minute, hour, day, month, day_of_week = cron_text
        else:
            raise Exception('cron_text error')
        job = conn.root.add_job(
            'app_apscheduler:run_script',
            'cron',
            kwargs=dict(
                type='ssh',
                script_text=script_text,
                timeout=timeout,
                ip=ip,
                username=username,
                password=password,
                extract_names=extract_names,
            ),
            year=year,
            week=week,
            second=second,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=job_id,
        )
        return job.id
    except Exception as e:
        raise e
    finally:
        conn.close()


def add_local_interval_job(script_text, interval, timeout, job_id, extract_names):
    try:
        conn = rpyc.connect('localhost', 8091)
        job = conn.root.add_job(
            'app_apscheduler:run_script',
            'interval',
            kwargs=dict(
                type='local',
                script_text=script_text,
                timeout=timeout,
                extract_names=extract_names,
            ),
            seconds=interval,
            id=job_id,
        )
        return job.id
    except Exception as e:
        raise e
    finally:
        conn.close()
