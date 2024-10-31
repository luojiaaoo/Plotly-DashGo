from flask import request, session, redirect, send_from_directory, abort
import dash
from config.dash_melon_conf import ShowConf, FlaskConf, BabelConf, CommonConf
from user_agents import parse
from flask_babel import Babel
from common.exception import AttackException
from flask_babel import gettext as _  # noqa
from common.utilities.util_logger import Log
from config.dash_melon_conf import PathProj
from common.utilities.util_dash import CustomDash

logger = Log.get_logger(__name__)


# dash实例
app = CustomDash(
    __name__,
    suppress_callback_exceptions=True,
    compress=True,
    update_title=None,
    serve_locally=CommonConf.DASH_SERVE_LOCALLY,
    extra_hot_reload_paths=[],
)
app.server.config['COMPRESS_ALGORITHM'] = FlaskConf.COMPRESS_ALGORITHM
app.server.config['COMPRESS_BR_LEVEL'] = FlaskConf.COMPRESS_BR_LEVEL
app.server.config['BABEL_DEFAULT_LOCALE'] = BabelConf.BABEL_DEFAULT_LOCALE
app.server.config['BABEL_DEFAULT_TIMEZONE'] = BabelConf.BABEL_DEFAULT_TIMEZONE
app.server.config['BABEL_TRANSLATION_DIRECTORIES'] = BabelConf.BABEL_TRANSLATION_DIRECTORIES
app.server.config['LANGUAGES'] = BabelConf.LANGUAGES
app.server.secret_key = FlaskConf.COOKIE_SESSION_SECRET_KEY
app.title = ShowConf.WEB_TITLE

# flask实例
server = app.server


# 头像获取接口
@server.route('/avatar/<user_name>')
def download_file(user_name):
    file_name = f'{user_name}.jpg'
    if '..' in user_name:
        try:
            raise AttackException(
                f'有人尝试通过头像文件接口攻击，URL:{request.url}，IP:{request.remote_addr}'
            )
        except AttackException as e:
            logger.warning(e, exc_info=True)
        abort(403)
    else:
        return send_from_directory(PathProj.AVATAR_DIR_PATH, file_name)


# 国际化
def select_locale():
    # 优先从session中获取
    lang_session = session.get('lang', None)
    lang_auto = request.accept_languages.best_match(server.config['LANGUAGES'])
    return lang_session or lang_auto


babel = Babel(app=server)
babel.init_app(app=server, locale_selector=select_locale)


# 首页拦截器
@server.before_request
def main_page_redirct():
    if request.path == '/':
        return redirect('/dashboard_/workbench')


# 恶意访问管理页面拦截器
@server.before_request
def ban_admin():
    if request.path.startswith('/admin'):
        try:
            raise AttackException(
                f'有人尝试访问不存在的管理页面，URL:{request.url}，IP:{request.remote_addr}'
            )
        except AttackException as e:
            logger.warning(e, exc_info=True)
        abort(403)


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
            return "<h1 style='color: red'>IP:{}, {}</h1>".format(
                request_addr, _('请不要使用IE浏览器或360浏览器兼容模式')
            )
        elif bw == 'Chrome' and bw_version < 71:
            return "<h1 style='color: red'>IP:{}, {}</h1>".format(
                request_addr,
                _('Chrome内核版本号太低，请升级浏览器'),
            ) + "<h1 style='color: red'><a href='https://www.google.cn/chrome/'>{}</a>{}</h1>".format(
                _('点击此处'),
                _('可下载最新版Chrome浏览器'),
            )
