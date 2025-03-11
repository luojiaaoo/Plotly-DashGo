from peewee import JOIN
from ..entity.table_announcement import SysAnnouncement
from ..entity.table_user import SysUser


def get_announcement() -> bool:
    """获取公告内容"""
    query = (
        SysAnnouncement.select(SysAnnouncement.datetime, SysAnnouncement.announcement, SysAnnouncement.user_name, SysUser.user_full_name)
        .join(SysUser, JOIN.LEFT_OUTER, on=(SysAnnouncement.user_name == SysUser.user_name))
        .where(SysAnnouncement.status)
        .order_by(SysAnnouncement.datetime.desc())
    )

    announcements = []
    for announcement in query.dicts():
        announcements.append(
            f'『{announcement["datetime"]:%Y/%m/%d} {announcement["user_name"]}({announcement["user_full_name"] if announcement["user_full_name"] else "Unknown"})』{announcement["announcement"]}'
        )
    return announcements
