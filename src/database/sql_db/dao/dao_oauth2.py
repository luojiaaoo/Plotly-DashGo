from peewee import DoesNotExist
from database.sql_db.entity.table_oauth2 import OAuth2Client, OAuth2AuthorizationCode, OAuth2Token
from typing import Optional
from database.sql_db.conn import db


def exist_client(client_id) -> Optional[OAuth2Client]:
    try:
        client: OAuth2Client = OAuth2Client.get(OAuth2Client.client_id == client_id)
        return client
    except DoesNotExist:
        return None


def insert_authorization_code(code, client_id, user_name, redirect_uri, expires_at, scope) -> bool:
    database = db()
    with database.atomic() as txn:
        try:
            OAuth2AuthorizationCode.create(
                code=code,
                client_id=client_id,
                user_name=user_name,
                redirect_uri=redirect_uri,
                expires_at=expires_at,
                scope=scope,
            )
        except Exception as e:
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def exist_code(code, client_id) -> Optional[OAuth2AuthorizationCode]:
    try:
        code: OAuth2AuthorizationCode = OAuth2AuthorizationCode.get((OAuth2AuthorizationCode.code == code) & (OAuth2AuthorizationCode.client_id == client_id))
        return code
    except DoesNotExist:
        return None


def validate_client(client_id, client_secret) -> Optional[OAuth2Client]:
    """验证客户端凭证"""
    try:
        client: OAuth2Client = OAuth2Client.get(OAuth2Client.client_id == client_id)
        if client.client_secret == client_secret:
            return client
        return None
    except DoesNotExist:
        return None


def insert_token(token, client_id, user_name, expires_at, scope) -> bool:
    database = db()
    with database.atomic() as txn:
        try:
            OAuth2Token.create(
                token=token,
                client_id=client_id,
                user_name=user_name,
                expires_at=expires_at,
                scope=scope,
            )
        except Exception as e:
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def exist_token(token) -> Optional[OAuth2Token]:
    try:
        token: OAuth2Token = OAuth2Token.get(OAuth2Token.token == token)
        return token
    except DoesNotExist:
        return None
