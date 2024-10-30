from dash import get_asset_url
from database.sql_db.dao.user import get_user_avatar_filename
import os


def get_avatar_path(user_name: str):
    return get_asset_url(os.path.join('avatars', get_user_avatar_filename(user_name)))
