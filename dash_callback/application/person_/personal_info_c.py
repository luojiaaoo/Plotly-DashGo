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


# 编辑全名开关
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


# 编辑全名
@app.callback(
    Input('personal-info-user-full-name', 'nSubmit'),
    [
        State('personal-info-user-full-name', 'value'),
        State('personal-info-user-full-name', 'defaultValue'),
    ],
)
def update_user_full_name(_, value, defaultValue):
    if dao_user.update_user_full_name(user_name=get_menu_access(only_get_user_name=True), user_full_name=value):
        set_props('workbench-user-full-name', {'children': value})
        MessageManager.success(content=__('用户全名更新成功'))
    else:
        set_props('personal-info-user-full-name', {'Value': defaultValue})
        MessageManager.warning(content=__('用户全名更新失败'))
    set_props('personal-info-user-full-name', {'variant': 'borderless', 'readOnly': True})


# 编辑性别
@app.callback(
    Input('personal-info-user-sex', 'value'),
    State('personal-info-user-sex', 'defaultValue'),
    prevent_initial_call=True,
)
def update_user_sex(value, defaultValue):
    if dao_user.update_user_sex(user_name=get_menu_access(only_get_user_name=True), user_sex=value):
        MessageManager.success(content=__('用户性别更新成功'))
    else:
        set_props('personal-info-user-sex', {'value': defaultValue})
        MessageManager.warning(content=__('用户性别更新失败'))


# 编辑邮箱开关
app.clientside_callback(
    """(_) => {
        return [false, 'outlined']
    }""",
    [
        Output('personal-info-user-email', 'readOnly'),
        Output('personal-info-user-email', 'variant'),
    ],
    Input('personal-info-user-email-edit', 'nClicks'),
)


# 编辑邮箱
@app.callback(
    Input('personal-info-user-email', 'nSubmit'),
    [
        State('personal-info-user-email', 'value'),
        State('personal-info-user-email', 'defaultValue'),
    ],
)
def update_user_email(_, value, defaultValue):
    if dao_user.update_user_email(user_name=get_menu_access(only_get_user_name=True), user_email=value):
        MessageManager.success(content=__('用户邮箱更新成功'))
    else:
        set_props('personal-info-user-email', {'Value': defaultValue})
        MessageManager.warning(content=__('用户邮箱更新失败'))
    set_props('personal-info-user-email', {'variant': 'borderless', 'readOnly': True})


# 编辑电话开关
app.clientside_callback(
    """(_) => {
        return [false, 'outlined']
    }""",
    [
        Output('personal-info-phone-number', 'readOnly'),
        Output('personal-info-phone-number', 'variant'),
    ],
    Input('personal-info-phone-number-edit', 'nClicks'),
)


# 编辑电话
@app.callback(
    Input('personal-info-phone-number', 'nSubmit'),
    [
        State('personal-info-phone-number', 'value'),
        State('personal-info-phone-number', 'defaultValue'),
    ],
)
def update_phone_number(_, value, defaultValue):
    if dao_user.update_phone_number(user_name=get_menu_access(only_get_user_name=True), phone_number=value):
        MessageManager.success(content=__('用户电话更新成功'))
    else:
        set_props('personal-info-phone-number', {'Value': defaultValue})
        MessageManager.warning(content=__('用户电话更新失败'))
    set_props('personal-info-phone-number', {'variant': 'borderless', 'readOnly': True})


# 编辑描述开关
app.clientside_callback(
    """(_) => {
        return [false, 'outlined']
    }""",
    [
        Output('personal-info-user-remark', 'readOnly'),
        Output('personal-info-user-remark', 'variant'),
    ],
    Input('personal-info-user-remark-edit', 'nClicks'),
)


# 编辑描述
@app.callback(
    Input('personal-info-user-remark', 'nSubmit'),
    [
        State('personal-info-user-remark', 'value'),
        State('personal-info-user-remark', 'defaultValue'),
    ],
)
def update_user_remark(_, value, defaultValue):
    if dao_user.update_user_remark(user_name=get_menu_access(only_get_user_name=True), user_remark=value):
        MessageManager.success(content=__('用户描述更新成功'))
    else:
        set_props('personal-info-user-remark', {'Value': defaultValue})
        MessageManager.warning(content=__('用户描述更新失败'))
    set_props('personal-info-user-remark', {'variant': 'borderless', 'readOnly': True})


# 修改密码开关
app.clientside_callback(
    """(_) => {
        return true
    }""",
    Output('personal-info-change-password-modal', 'visible'),
    Input('personal-info-password-edit', 'nClicks'),
)


# 修改密码
@app.callback(
    Input('personal-info-change-password-modal', 'okCounts'),
    [
        State('personal-info-change-password-old', 'value'),
        State('personal-info-change-password-new', 'value'),
        State('personal-info-change-password-new-again', 'value'),
    ],
)
def update_password(okCounts, old_password, new_password, new_password_again):
    if not old_password:
        MessageManager.warning(content=__('请填写旧密码'))
        return
    if new_password != new_password_again:
        MessageManager.warning(content=__('密码不一致，请重新填写'))
        return
    if dao_user.update_user_password(user_name=get_menu_access(only_get_user_name=True), new_password=new_password, old_password=old_password):
        MessageManager.success(content=__('用户密码更新成功'))
    else:
        MessageManager.warning(content=__('用户密码验证错误'))
