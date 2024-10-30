from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import set_props
import dash
from server import app
from common.utilities.util_file_trans import AvatarFile
from common.utilities.util_menu_access import get_menu_access, MenuAccess
from flask_babel import gettext as _  # noqa


# 头像上传模块
@app.callback(
    Input('personal-info-avatar-upload-choose', 'contents'),
    prevent_initial_call=True,
)
def callback_func(contents):
    menu_access = get_menu_access()
    if contents is not None:
        note, base_str = contents.split(',', 1)
        img_suffix = note.split(';')[0].split('/')[-1]

        AvatarFile.save_avatar_file(base64_str=base_str, img_type=img_suffix, user_name=menu_access.user_name)
    return dash.no_update
