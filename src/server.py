from flask import request, redirect, send_from_directory, abort, jsonify
from common.exception import OAuth2Error
from common.utilities.util_oauth2 import current_token, require_oauth
from config.dashgo_conf import ShowConf, FlaskConf, CommonConf, PathProj
from common.utilities.util_logger import Log
from common.exception import global_exception_handler
from common.utilities.util_dash import CustomDash
from common.constant import HttpStatusConstant
from datetime import datetime, timedelta
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


# 自动管理数据库上下文
@server.before_request
def _db_connect():
    from database.sql_db.conn import db

    db().connect(reuse_if_open=True)


@server.teardown_request
def _db_close(exc):
    from database.sql_db.conn import db

    _db = db()
    if not _db.is_closed():
        _db.close()


@server.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    """第一步grant用户确认阶段
    OAuth2授权端点
    参数：
    - client_id: 客户端ID（必须）
    - redirect_uri: 重定向URI（必须）
    - response_type: 必须为'code'
    - scope: 请求的权限范围（可选，本项目为必选）
    - state: 客户端状态值（可选，本项目为必选）
    """
    from flask import request, render_template_string
    from common.utilities.util_jwt import jwt_decode_from_session, AccessFailType
    from common.utilities.util_oauth2 import authorize_html
    from config.dashgo_conf import OAuth2Conf
    from database.sql_db.dao.dao_oauth2 import exist_client, insert_authorization_code
    from yarl import URL
    import secrets

    # 1. 如果没登陆，登录了再来认证
    if isinstance((rt_access := jwt_decode_from_session()), AccessFailType):
        return redirect(URL.build(path='/login').with_query({'next': request.url}).__str__())
    ### 参数检查
    user_name = rt_access['user_name']
    # 检查client_id
    if request.args.get('client_id') is None:
        raise OAuth2Error('Invalid_client_id')
    client = exist_client(client_id=request.args.get('client_id'))
    # 检查scope
    if request.args.get('scope') is None or client.check_scope(request.args.get('scope').split()):
        raise OAuth2Error('Invalid_scope')
    # 检查redirect_uri
    if request.args.get('redirect_uri') is None or client.check_redirect_uri(request.args.get('redirect_uri')):
        raise OAuth2Error('Invalid_redirect_uri')
    # 检查response_type
    if request.args.get('response_type') != 'code':
        raise OAuth2Error('Invalid_response_type')
    # 检查state
    if request.args.get('state') is None:
        raise OAuth2Error('Invalid_state')
    # 2. 登录啦，是否同意授权？
    if request.method == 'GET' and request.args.get('confirm') != 'yes':
        return render_template_string(authorize_html, scope=request.args.get('scope'), client_id=request.args.get('client_id'), user_name=user_name)

    # 3. 同意授权
    grant_user = rt_access['user_name'] if request.form['confirm'] or request.args.get('confirm') == 'yes' else None
    if grant_user is None:
        raise OAuth2Error('NOT_IMPLEMENTED', HttpStatusConstant.NOT_IMPLEMENTED)
    # 生成code授权码
    if insert_authorization_code(
        code=(auth_code := secrets.token_urlsafe(OAuth2Conf.OAuth2AuthorizationCodeLength)),
        client_id=request.args.get('client_id'),
        user_name=user_name,
        expires_at=datetime.now() + timedelta(minutes=OAuth2Conf.OAuth2AuthorizationCodeExpiresInMinutes),
        redirect_uri=request.args.get('redirect_uri'),
        scope=request.args.get('scope'),
    ):
        return redirect(URL(request.args.get('redirect_uri')).with_query({'code': auth_code, 'state': request.args.get('state')}).__str__())
    else:
        raise OAuth2Error('Internal error: Authorization code generation failed')


@server.route('/oauth/token', methods=['POST'])
def issue_token():
    """第三步token发放
    OAuth2令牌端点
    支持授权码模式（authorization_code）
    参数：
    - grant_type: 必须为'authorization_code'
    - code: 授权码（必须）
    - redirect_uri: 必须与授权请求时一致
    - client_id: 客户端ID（必须）
    - client_secret: 客户端密钥（必须）
    """
    import secrets
    from database.sql_db.dao.dao_oauth2 import exist_code, validate_client, insert_token
    from config.dashgo_conf import OAuth2Conf

    # 验证客户端凭证
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    client = validate_client(client_id, client_secret)
    if not client:
        raise OAuth2Error('Invalid client credentials', HttpStatusConstant.UNAUTHORIZED)
    # 验证授权类型
    if request.form.get('grant_type') != 'authorization_code':
        raise OAuth2Error('Unsupported grant_type')
    # 获取授权码
    code = request.form.get('code')
    if not code:
        raise OAuth2Error('Missing authorization code')
    auth_code = exist_code(code=code, client_id=client_id)
    if not auth_code:
        raise OAuth2Error('Invalid authorization code', HttpStatusConstant.UNAUTHORIZED)
    # 验证授权码
    if not auth_code.is_valid():
        raise OAuth2Error('Authorization code expired')
    if not auth_code.check_client_id(client_id):
        raise OAuth2Error('Client mismatch')
    if not auth_code.check_redirect_uri(request.form.get('redirect_uri')):
        raise OAuth2Error('Redirect URI mismatch')
    if insert_token(
        token=(token_ := secrets.token_urlsafe(OAuth2Conf.OAuth2TokenLength)),
        client_id=client_id,
        user_name=auth_code.user_name,
        expires_at=datetime.now() + timedelta(minutes=OAuth2Conf.OAuth2TokenExpiresInMinutes),
        scope=auth_code.scope,
    ):
        auth_code.delete()
        return jsonify(
            {
                'token_type': 'bearer',
                'access_token': token_,
                'expires_in': OAuth2Conf.OAuth2TokenExpiresInMinutes * 60,
                'scope': auth_code.scope,
            }
        )
    else:
        raise OAuth2Error('Internal error: Token generation failed')


@server.route('/api/userinfo')
@require_oauth('userinfo')
def userinfo():
    """受保护端点"""
    from database.sql_db.dao.dao_user import get_user_info
    from common.utilities.util_menu_access import MenuAccess

    token = current_token()
    user = get_user_info(user_names=[token.user_name])[0]
    access_metas = MenuAccess(token.user_name).all_access_metas
    return jsonify(
        {
            'user_name': user.user_name,
            'user_full_name': user.user_full_name,
            'user_sex': user.user_sex,
            'access_metas': access_metas,
            'user_email': user.user_email,
            'phone_number': user.phone_number,
            'user_remark': user.user_remark,
        }
    )


# oauth2_grant登录后重定向
@server.before_request
def oauth2_grant_redirect():
    from common.utilities.util_jwt import jwt_decode_from_session, AccessFailType
    from yarl import URL

    if not isinstance(jwt_decode_from_session(), AccessFailType) and request.path == '/' and request.args.get('next') is not None:
        return redirect(URL(request.args.get('next')).extend_query(confirm='yes').__str__())


# OAuth2错误处理器
@server.errorhandler(OAuth2Error)
def handle_oauth2_error(e):
    return jsonify({'error': 'invalid_request', 'error_description': e.description}), e.status_code


# 首页重定向
@server.before_request
def main_page_redirct():
    if request.path == '/':
        return redirect('/dashboard_/workbench')
