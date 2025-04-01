def ssh_run_script(ip, password, script_text, timeout):
    """
    使用 SSH 连接到远程服务器并运行脚本。

    参数:
    ip (str): 远程服务器的 IP 地址。
    password (str): SSH 登录密码。
    script_text (str): 要运行的脚本内容。
    """
    import paramiko
    print(111111111)

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
