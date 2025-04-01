import subprocess


def run_script(type, script_text, timeout=20, ip=None, password=None):
    print(11111111)
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
        try:
            result = subprocess.run(
                script_text,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return None, 'Command timed out'
        except Exception as e:
            return None, str(e)
    elif type == 'ssh':
        import paramiko

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=ip, username='root', password=password)
            stdin, stdout, stderr = ssh.exec_command(script_text, get_pty=True, timeout=timeout)
            output = stdout.read().decode()
            error = stderr.read().decode()
            return output, error
        except Exception as e:
            return None, str(e)
        finally:
            ssh.close()
