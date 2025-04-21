from common.utilities.util_logger import Log
from datetime import datetime
import poplib
from email import parser
from email.header import decode_header


logger = Log.get_logger(__name__)


# 解码函数
def decode_mime(header):
    parts = decode_header(header)
    decoded_parts = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(charset if charset else 'utf-8'))
        else:
            decoded_parts.append(part)
    return ''.join(decoded_parts)


def get_email_context_from_subject_during(
    pop3_server: str,
    port: int,
    emal_account: str,
    password: str,
    subjects: str,
    since_time: datetime,
    before_time: datetime,
):
    pop_conn = poplib.POP3_SSL(pop3_server, int(port))
    try:
        rt = []
        # 1. 连接到服务器
        pop_conn.user(emal_account)
        pop_conn.pass_(password)

        # 2. 获取统计信息
        num_messages, _ = pop_conn.stat()
        if num_messages == 0:
            pop_conn.quit()
            return rt
        # 获取邮件列表
        _, msg_list, _ = pop_conn.list()
        for msg_num in range(1, len(msg_list) + 1)[::-1]:
            # 获取邮件
            response, msg_lines, _ = pop_conn.retr(msg_num)
            msg_content = b'\n'.join(msg_lines)

            msg_parser = parser.BytesParser()
            email_msg = msg_parser.parsebytes(msg_content)
            try:
                from_ = decode_mime(email_msg['From'])
                subject_ = decode_mime(email_msg['Subject'])
                datetime_ = datetime.strptime(decode_mime(email_msg['Date'])[:31], '%a, %d %b %Y %H:%M:%S %z')
                context = ''
                for part in email_msg.walk():
                    if part.get_content_type() == 'text/plain':
                        context = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
            except Exception as e:
                logger.error(f'解析邮件失败: {e}')
                continue
            else:
                if datetime_ < since_time:
                    break
                elif since_time <= datetime_ < before_time and any([subject in subject_ for subject in subjects]):
                    rt.append(
                        {
                            'from': from_,
                            'subject': subject_,
                            'datetime': datetime_,
                            'context': context,
                        }
                    )
        return rt
    except Exception as e:
        raise e
    finally:
        pop_conn.quit()
