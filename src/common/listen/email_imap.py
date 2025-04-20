import imaplib
import email
from typing import List
from email.header import decode_header
from datetime import datetime
import re
from common.utilities.util_logger import Log
import base64

logger = Log.get_logger(__name__)

def encode_chinese_for_imap(text: str) -> str:
    """
    将中文文本编码为IMAP搜索可识别的格式
    
    参数:
        text: 要编码的中文文本
    
    返回:
        编码后的字符串
    """
    # 对于中文主题，通常需要转换为UTF-8编码的base64字符串
    return f"{base64.b64encode(text.encode('utf-8')).decode()}"

def get_email_context_from_subject_during(
    imap_server: str,
    port: int,
    emal_account: str,
    password: str,
    subjects: List[str],
    since_time: datetime,
    before_time: datetime,
):
    context = ''
    mail = imaplib.IMAP4_SSL(imap_server, port=port)
    try:
        mail.login(emal_account, password)
        mail.select('inbox')  # 选择邮箱文件夹（通常是 INBOX）
        since_time_str = f'{since_time:%d-%b-%Y}'
        before_time_str = f'{before_time:%d-%b-%Y}'
        subjects_str = ' OR '.join([subject for subject in subjects])
        status, messages = mail.search(None, f'SUBJECT "{subjects_str}" SINCE {since_time_str} BEFORE {before_time_str}')
        messages = messages[0].split()
        emails = []
        for mail_id in messages:
            status, msg_data = mail.fetch(mail_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])  # 解析邮件内容
                    subject, encoding = decode_header(msg['Subject'])[0]  # 获取邮件主题
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or 'utf-8')
                    from_info = ''
                    for from_, encoding in decode_header(msg.get('From')):  # 获取发件人
                        if isinstance(from_, bytes):
                            from_info += from_.decode(encoding or 'utf-8')
                    date_str = msg.get('Date', '')[:25]  # 提取邮件发送时间
                    try:
                        email_datetime = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S')
                    except ValueError as e:
                        logger.error(f'无法解析邮件的发送时间的日期字符串: {date_str} err: {e}')
                        continue
                    if not (since_time <= email_datetime < before_time):  # 过滤精确时间
                        continue
                    if msg.is_multipart():  # 如果邮件是多部分的
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get('Content-Disposition'))
                            if content_type == 'text/plain' and 'attachment' not in content_disposition:
                                body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                                context += body
                    else:
                        body = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8')
                        context += body
            emails.append(
                {
                    'subject': subject,
                    'datetime': email_datetime,
                    'from': from_info,
                    'context': context,
                }
            )
        return emails
    except Exception as e:
        raise e
    finally:
        mail.logout()  # 关闭连接


# a = get_email_context_from_subject(
#     imap_server=IMAP_SERVER,
#     port=993,
#     emal_account=EMAIL_ACCOUNT,
#     password=PASSWORD,
#     subject='VDU',
#     since_time=datetime.now() - timedelta(days=5),
#     before_time=datetime.now(),
# )
# from pprint import pprint

# pprint(a)
