from flask import request, redirect, send_from_directory, abort
from config.dashgo_conf import ShowConf, FlaskConf, CommonConf, PathProj
from common.utilities.util_logger import Log
from common.exception import global_exception_handler
from common.utilities.util_dash import CustomDash
from common.constant import HttpStatusConstant
from i18n import t__other


logger = Log.get_logger(__name__)

# dash实例
app = CustomDash(
    __name__,
    suppress_callback_exceptions=True,
    compress=True,
    update_title=None,
    serve_locally=CommonConf.DASH_SERVE_LOCALLY,
    extra_hot_reload_paths=[],
    on_error=global_exception_handler,
)
app.server.config['COMPRESS_ALGORITHM'] = FlaskConf.COMPRESS_ALGORITHM
app.server.config['COMPRESS_BR_LEVEL'] = FlaskConf.COMPRESS_BR_LEVEL
app.server.secret_key = FlaskConf.COOKIE_SESSION_SECRET_KEY
app.title = ShowConf.WEB_TITLE

# flask实例
server = app.server


# 头像获取接口
@server.route('/avatar/<user_name>')
def download_file(user_name):
    file_name = f'{user_name}.jpg'
    if '..' in user_name:
        
        logger.warning(f'有人尝试通过头像文件接口攻击，URL:{request.url}，IP:{request.remote_addr}')
        abort(HttpStatusConstant.FORBIDDEN)
    else:
        return send_from_directory(PathProj.AVATAR_DIR_PATH, file_name)


# nginx代理后，拦截直接访问
@server.before_request
def ban_bypass_proxy():
    from config.dashgo_conf import ProxyConf

    if ProxyConf.NGINX_PROXY and request.headers.get('X-Forwarded-For') is None:
        abort(HttpStatusConstant.FORBIDDEN)


# 首页重定向
@server.before_request
def main_page_redirct():
    if request.path == '/':
        return redirect('/dashboard_/workbench')


# 恶意访问管理页面拦截器
@server.before_request
def ban_admin():
    if request.path.startswith('/admin'):
        from common.utilities.util_browser import get_browser_info
        browser_info = get_browser_info()
        logger.warning(f'有人尝试访问不存在的管理页面，URL:{browser_info.url}，IP:{browser_info.request_addr}')
        abort(HttpStatusConstant.NOT_FOUND)


# 获取用户浏览器信息
@server.before_request
def get_user_agent_info():
    from common.utilities.util_browser import get_browser_info

    browser_info = get_browser_info()
    if browser_info.type == 'ie':
        return "<h1 style='color: red'>IP:{}, {}</h1>".format(browser_info.request_addr, t__other('请不要使用IE内核浏览器'))
    elif browser_info.type == 'chrome' and browser_info.version is not None and browser_info.version < 88:
        return "<h1 style='color: red'>IP:{}, {}</h1>".format(
            browser_info.request_addr,
            t__other('Chrome内核版本号太低，请升级浏览器'),
        )
