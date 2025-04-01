import rpyc


def add_ssh_interval_job(ip, password, script_text, interval, timeout, job_id, max_instances=10):
    try:
        conn = rpyc.connect('localhost', 8091)
        job = conn.root.add_job(
            'server:ssh_run_script',
            'interval',
            args=[ip, password, script_text, timeout],
            seconds=interval,
            job_id=job_id,
            max_instances=max_instances,
        )
        return job.id
    except Exception as e:
        raise e
    finally:
        conn.close()
