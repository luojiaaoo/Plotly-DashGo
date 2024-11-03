from server import app
from common.utilities import util_jwt
from dash_view.pages import main, login
from common.utilities.util_menu_access import MenuAccess
from flask import session
from config.access_factory import AccessFactory

# 启动检查权限
AccessFactory.check_access_meta()


def valid_token():
    """if valid token, return True, else return False"""
    rt_access = util_jwt.jwt_decode_from_session(
        verify_exp=True, force_logout_if_exp=False, ignore_exp=False, force_logout_if_invalid=False
    )  # can not force logout, because global-reload component do not exists
    if isinstance(rt_access, util_jwt.AccessFailType):
        return login.render_content()
    else:
        # 如果session是永久，也就是用户登录勾选了保存会话，刷新jwt令牌，继续延长令牌有效期
        if session.permanent:
            util_jwt.jwt_encode_save_access_to_session(
                {'user_name': rt_access['user_name']}, session_permanent=True
            )
        return main.render_content(
            # 获取用户菜单权限，根据权限初始化主页内容
            menu_access=MenuAccess(rt_access['user_name']),
        )


# 用户授权路由
app.layout = valid_token

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)
