from flask import session
from server import app
from common.utilities import util_jwt
from dash_view.pages import main, login

def valid_token():
    ''' if valid token, return True, else return False '''
    rt_access = util_jwt.jwt_decode_from_session(verify_exp=True)
    if isinstance(rt_access, util_jwt.AccessFailType):
        return login.render_content()
    else:
        return main.render_content()

# 用户授权路由
app.layout = valid_token

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)
