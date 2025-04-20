import paramiko
import os


def connect_ssh(hostname, port, username, password):
    port = int(port)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, port=port, username=username, password=password)
    return ssh


def ftp_ssh(ssh, file_path, destination_folder):
    destination_folder = destination_folder.rstrip('/')
    sftp = ssh.open_sftp()
    sftp.put(file_path, f'{destination_folder}/{os.path.basename(file_path)}')  # 传输到/tmp目录
    sftp.close()
