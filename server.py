import os
from flask import request, session, redirect
import dash
from config.dash_melon_conf import ShowConf, FlaskConf
from user_agents import parse
from logging import Logger
from config.dash_melon_conf import LoginConf

logger = Logger(__name__)

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    compress=True,
    update_title=None,
)
app.server.config['COMPRESS_ALGORITHM'] = 'br'
app.server.config['COMPRESS_BR_LEVEL'] = 9
app.server.secret_key = FlaskConf.COOKIE_SESSION_SECRET_KEY
app.title = ShowConf.WEB_TITLE
server = app.server

# 首页拦截器
@server.before_request
def before_request():
    if request.path == '/':
        return redirect('/dashboard/workbench')

# 获取用户浏览器信息
@server.before_request
def get_user_agent_info():
    request_addr = request.remote_addr
    user_string = str(request.user_agent)
    user_agent = parse(user_string)
    bw = user_agent.browser.family
    if user_agent.browser.version != ():
        bw_version = user_agent.browser.version[0]
        if bw == 'IE':
            logger.warning(
                '[sys]请求人:{}||请求IP:{}||请求方法:{}||请求Data:{}',
                session.get('name'),
                request_addr,
                request.method,
                '用户使用IE内核',
            )
            return "<h1 style='color: red'>请不要使用IE浏览器或360浏览器兼容模式</h1>"
        if bw == 'Chrome' and bw_version < 71:
            logger.warning(
                '[sys]请求人:{}||请求IP:{}||请求方法:{}||请求Data:{}',
                session.get('name'),
                request_addr,
                request.method,
                '用户Chrome内核版本太低',
            )
            return (
                "<h1 style='color: red'>Chrome内核版本号太低，请升级浏览器</h1>"
                "<h1 style='color: red'><a href='https://www.google.cn/chrome/'>点击此处</a>可下载最新版Chrome浏览器</h1>"
            )



