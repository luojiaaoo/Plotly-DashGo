from flask import request, session, redirect
import dash
from config.dash_melon_conf import ShowConf, FlaskConf, BabelConf
from user_agents import parse
from flask_babel import Babel
from flask_babel import gettext as _  # noqa
from common.utilities.util_logger import Log

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


babel = Babel(app=server)
babel.init_app(app=server, locale_selector=select_locale)


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
            return (
                _("<h1 style='color: red'>IP:{}, 请不要使用IE浏览器或360浏览器兼容模式</h1>").format(request_addr)
            )
        elif bw == 'Chrome' and bw_version < 71:
            return (
                f"<h1 style='color: red'>IP:{request_addr}, {_("Chrome内核版本号太低，请升级浏览器")}</h1>"
                f"<h1 style='color: red'><a href='https://www.google.cn/chrome/'>{_('点击此处')}</a>{_('可下载最新版Chrome浏览器')}</h1>"
            )
