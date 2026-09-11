from datetime import datetime
from typing import List, Optional

from peewee import DoesNotExist, IntegrityError

from common.utilities.util_logger import Log
from database.sql_db.conn import db
from ..entity.table_orcarouter import SysOrcaRouterCredential

logger = Log.get_logger(__name__)

#: Every authentication method this integration can store.
support_auth_methods = [
    'orcarouter',
    'orcarouter-oauth',
]


def get_credential(auth_method: str) -> Optional[SysOrcaRouterCredential]:
    try:
        with db().atomic():
            return SysOrcaRouterCredential.select().where(SysOrcaRouterCredential.auth_method == auth_method).get()
    except DoesNotExist:
        return None


def list_credentials() -> List[SysOrcaRouterCredential]:
    credentials = [row for row in SysOrcaRouterCredential.select()]
    credentials.sort(key=lambda row: row.auth_method)
    return credentials


def upsert_credential(
    auth_method: str,
    api_key_encrypted: str,
    scope: str = '',
    user_id: str = '',
    needs_reauth: bool = False,
) -> bool:
    """Write a new credential generation, replacing whatever this method held.

    The previous stored secret is only replaced here, after a new one has been
    obtained — never deleted ahead of a successful replacement.
    """
    database = db()
    previous = get_credential(auth_method)
    generation = (previous.generation + 1) if previous else 1
    try:
        with database.atomic():
            if previous:
                SysOrcaRouterCredential.update(
                    api_key_encrypted=api_key_encrypted,
                    scope=scope,
                    user_id=user_id,
                    generation=generation,
                    needs_reauth=needs_reauth,
                    update_datetime=datetime.now(),
                ).where(SysOrcaRouterCredential.auth_method == auth_method).execute()
            else:
                SysOrcaRouterCredential.create(
                    auth_method=auth_method,
                    api_key_encrypted=api_key_encrypted,
                    scope=scope,
                    user_id=user_id,
                    generation=generation,
                    needs_reauth=needs_reauth,
                )
        return True
    except IntegrityError as e:
        logger.error(e, exc_info=True)
        return False


def mark_needs_reauth(auth_method: str, generation: int) -> bool:
    """Flag one exact credential generation as unusable.

    A late failure from an old request carries the generation it was issued under, so
    it can only ever mark that generation — a credential re-authorized in the meantime
    is untouched.
    """
    if not generation:
        return False
    try:
        with db().atomic():
            updated = (
                SysOrcaRouterCredential.update(needs_reauth=True, update_datetime=datetime.now())
                .where((SysOrcaRouterCredential.auth_method == auth_method) & (SysOrcaRouterCredential.generation == generation))
                .execute()
            )
        return bool(updated)
    except IntegrityError as e:
        logger.error(e, exc_info=True)
        return False


def delete_credential(auth_method: str) -> bool:
    try:
        with db().atomic():
            SysOrcaRouterCredential.delete().where(SysOrcaRouterCredential.auth_method == auth_method).execute()
        return True
    except IntegrityError as e:
        logger.error(e, exc_info=True)
        return False
