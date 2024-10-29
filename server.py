from flask import request, session, redirect
import dash
from config.dash_melon_conf import ShowConf, FlaskConf, BabelConf
from user_agents import parse
from flask_babel import Babel
from common.utilities.util_logger import Log
import pytz

logger = Log.get_logger(__name__)


# dash实例
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    compress=True,
    update_title=None,
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


# 国际化
def select_locale():
    # 优先从session中获取
    lang_session = session.get('lang', None)
    lang_request = request.args.get('lang', None)
    lang_auto = request.accept_languages.best_match(server.config['LANGUAGES'])
    return lang_session or lang_request or lang_auto


def select_timezone():
    # 从请求参数中获取时区信息
    timezone_session = session.get('lang', None)
    timezone_request = request.args.get('timezone', default='UTC')
    timezone = timezone_session or timezone_request
    # 检查时区是否有效
    if timezone in pytz.all_timezones:
        return timezone
    else:
        return None  # 返回默认时区


babel = Babel(app=server)
babel.init_app(app=server, locale_selector=select_locale, timezone_selector=select_timezone)


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
