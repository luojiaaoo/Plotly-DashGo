from dash.dependencies import Input, Output, State
from server import app
from common.utilities.util_file_trans import AvatarFile
from dash_components import MessageManager
from dash import set_props
from database.sql_db.dao import dao_user
from common.utilities.util_menu_access import get_menu_access
from uuid import uuid4
from functools import partial
from i18n import translator

__ = partial(translator.t)


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
    url = src.split('?')[0] + f'?{str(uuid4())}'
    # 个人页
    set_props('personal-info-avatar', {'src': url})
    # head
    set_props('global-head-avatar', {'src': url})
    # 工作台
    set_props('workbench-avatar', {'src': url})


app.clientside_callback(
    """(_) => {
        return [false, 'outlined']
    }""",
    [
        Output('personal-info-user-full-name', 'readOnly'),
        Output('personal-info-user-full-name', 'variant'),
    ],
    Input('personal-info-user-full-name-edit', 'nClicks'),
)


@app.callback(
    Input('personal-info-user-full-name', 'nSubmit'),
    [
        State('personal-info-user-full-name', 'value'),
        State('personal-info-user-full-name', 'defaultValue'),
    ],
)
def update_user_full_name(_, value, defaultValue):
    if dao_user.update_user_full_name(user_name=get_menu_access(only_get_user_name=True), user_full_name=value):
        MessageManager.success(content=__('用户全名更新成功'))
    else:
        set_props('personal-info-user-full-name', {'defaultValue': defaultValue})
        MessageManager.warning(content=__('用户全名更新失败'))
    set_props('personal-info-user-full-name', {'variant': 'borderless', 'readOnly': True})
