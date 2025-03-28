from peewee import JOIN
from ..entity.table_announcement import SysAnnouncement
from ..entity.table_user import SysUser
from datetime import datetime
from typing import List
from dataclasses import dataclass
from database.sql_db.conn import db


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


@dataclass
class Announcement:
    datetime: datetime
    announcement: str
    name: str
    status: bool


# 获取全部的数据
def get_all_announcements() -> List[Announcement]:
    """获取全部公告内容"""
    query = (
        SysAnnouncement.select(SysAnnouncement.datetime, SysAnnouncement.announcement, SysAnnouncement.user_name, SysUser.user_full_name, SysAnnouncement.status)
        .join(SysUser, JOIN.LEFT_OUTER, on=(SysAnnouncement.user_name == SysUser.user_name))
        .order_by(SysAnnouncement.datetime.desc())
    )

    announcements = []
    for announcement in query.dicts():
        announcements.append(
            Announcement(
                **{
                    'datetime': f'{announcement["datetime"]:%Y-%m-%d %H:%M:%S}',
                    'announcement': announcement['announcement'],
                    'name': f'{announcement["user_name"]}({announcement["user_full_name"] if announcement["user_full_name"] else "Unknown"})',
                    'status': announcement['status'],
                }
            )
        )
    return announcements


def add_announcement(announcement: str, user_name: str) -> bool:
    """新增公告"""
    database = db()
    with database.atomic() as txn:
        SysAnnouncement.create(announcement=announcement, user_name=user_name, datetime=datetime.now(), status=True)



def delete_announcement(announcements: List[str]) -> bool:
    """删除公告"""
    database = db()
    with database.atomic() as txn:
        SysAnnouncement.delete().where(SysAnnouncement.announcement.in_(announcements)).execute()



def update_announcement_status(announcement: str, status: bool) -> bool:
    """更新公告状态"""
    database = db()
    with database.atomic() as txn:
        SysAnnouncement.update(status=status).where(SysAnnouncement.announcement == announcement).execute()

