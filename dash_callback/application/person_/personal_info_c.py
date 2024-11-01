from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import set_props
import dash
from server import app
from common.utilities.util_file_trans import AvatarFile
from common.utilities.util_menu_access import get_menu_access, MenuAccess
from flask_babel import gettext as _  # noqa
from uuid import uuid4


# 头像上传模块
@app.callback(
    [
        Output('personal-info-avatar', 'src'),
        Output('global-head-avatar', 'src'),
    ],
    Input('personal-info-avatar-upload-choose', 'contents'),
    [
        State('personal-info-avatar', 'src'),
        State('global-head-avatar', 'src'),
    ],
    prevent_initial_call=True,
)
def callback_func(contents, src, src_):
    menu_access = get_menu_access()
    if contents is not None:
        note, base_str = contents.split(',', 1)
        img_suffix = note.split(';')[0].split('/')[-1]

        AvatarFile.save_avatar_file(base64_str=base_str, img_type=img_suffix, user_name=menu_access.user_name)
    # 强制刷新url，实际对象没变
    return src.split('?')[0]+f'?{str(uuid4())}', src_.split('?')[0]+f'?{str(uuid4())}'
