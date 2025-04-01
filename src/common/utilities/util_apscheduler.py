import rpyc


def add_ssh_interval_job(ip, password, script_text, interval, timeout, job_id):
    try:
        conn = rpyc.connect('localhost', 8091)
        job = conn.root.add_job(
            'server:ssh_run_script',
            'interval',
            args=[ip, password, script_text, timeout],
            seconds=interval,
            job_id=job_id,
        )
        return job.id
    except Exception as e:
        raise e
    finally:
        conn.close()


def add_ssh_cron_job(ip, password, script_text, cron_text, timeout, job_id, year=None, week=None):
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
            'server:ssh_run_script',
            'cron',
            args=[ip, password, script_text, timeout],
            year=year,
            week=week,
            second=second,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            job_id=job_id,
        )
        return job.id
    except Exception as e:
        raise e
    finally:
        conn.close()
