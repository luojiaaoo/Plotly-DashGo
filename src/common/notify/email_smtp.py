import smtplib
from smtplib import SMTPAuthenticationError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from email.header import Header


def send_mail(host: str, port: str, user: str, password: str, receivers: List[str], title: str, content: str):
    try:
        # 1. 连接邮箱服务器
        con = smtplib.SMTP_SSL(host, port)
        # 2. 登录邮箱
        con.login(user, password)
    except Exception as e:
        return False, str(e)
    # 3. 准备数据
    # 创建邮件对象
    msg = MIMEMultipart()
    # 设置邮件主题
    msg['Subject'] = Header(title, 'utf-8').encode()
    # 设置邮件发送者
    msg['From'] = f'{user} <{user}>'
    # 设置邮件接受者
    msg['To'] = ', '.join(receivers)
    # 添加⽂文字内容
    msg.attach(MIMEText(content[:1900], 'plain', 'utf-8'))
    # 4.发送邮件
    try:
        con.sendmail(user, receivers, msg.as_string())
        return True, 'ok'
    except Exception as e:
        return False, str(e)
    finally:
        con.quit()
