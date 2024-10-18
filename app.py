from flask import session
from server import app
from common.utilities import util_jwt
from dash_view.pages import main, login


def router_login():
    if session.get('Authorization') and util_jwt.jwt_decode(session.get('Authorization'), verify_exp=True):
        return main.render_content()
    else:
        return login.render_content()


# 用户授权路由
app.layout = router_login

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)
