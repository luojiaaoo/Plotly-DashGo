from dash.dependencies import Input, Output, State
from server import app
from common.utilities.util_file_trans import AvatarFile
from dash import set_props
from common.utilities.util_menu_access import get_menu_access
from uuid import uuid4


# 头像上传模块
@app.callback(
    Input('personal-info-avatar-upload-choose', 'contents'),
    [
        State('personal-info-avatar', 'src'),
        State('global-head-avatar', 'src'),
    ],
    prevent_initial_call=True,
)
def callback_func(contents, src, _):
    menu_access = get_menu_access()
    if contents is not None:
        note, base_str = contents.split(',', 1)
        img_suffix = note.split(';')[0].split('/')[-1]

        AvatarFile.save_avatar_file(base64_str=base_str, img_type=img_suffix, user_name=menu_access.user_name)
    # 强制刷新url，实际对象没变
    url = src.split('?')[0]+f'?{str(uuid4())}'
    # 个人页
    set_props('personal-info-avatar', {'src': url})
    # head
    set_props('global-head-avatar', {'src': url})
    # 工作台
    set_props('workbench-avatar', {'src': url})

