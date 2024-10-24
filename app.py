from server import app
from common.utilities import util_jwt
from dash_view.pages import main, login
from common.utilities.util_menu_access import MenuAccess


def valid_token():
    """if valid token, return True, else return False"""
    rt_access = util_jwt.jwt_decode_from_session(
        verify_exp=True, force_logout_if_exp=False, ignore_exp=False, force_logout_if_invalid=False
    )  # can not force logout, because global_reload component do not exists
    if isinstance(rt_access, util_jwt.AccessFailType):
        return login.render_content()
    else:
        return main.render_content(
            # 获取用户菜单权限，根据权限初始化主页内容
            menu_access=MenuAccess(rt_access['user_name']),
        )


# 用户授权路由
app.layout = valid_token

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=False)
