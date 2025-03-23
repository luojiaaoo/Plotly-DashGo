from server import app
import feffery_utils_components as fuc
from dash import html, dcc
from config.access_factory import AccessFactory
from database.sql_db.conn import initialize_database
import feffery_antd_components as fac
from dash.dependencies import Input, Output, State
from dash import set_props
from common.utilities import util_jwt
from dash_view.pages import main, login
from common.utilities.util_menu_access import MenuAccess
from common.exception import NotFoundUserException
from common.utilities.util_logger import Log
import sys

logger = Log.get_logger(__name__)

# 检查Python运行版本
if sys.version_info < (3, 9):
    raise Exception('Python version must above 3.9 !!')

# 初始化数据库
initialize_database()

# 启动检查权限
AccessFactory.check_access_meta()

# 全局功能组件+全局消息提示+全局通知信息+URL初始化中继组件+根容器
app.layout = lambda: fuc.FefferyTopProgress(
    [
        # 全局url监听组件，仅仅起到监听的作用
        fuc.FefferyLocation(id='global-url-location'),
        # 注入全局消息提示容器
        fac.Fragment(id='global-message-container'),
        # 注入全局通知信息容器
        fac.Fragment(id='global-notification-container'),
        # URL初始化中继组件，触发root_router回调执行
        dcc.Store(id='global-url-init-load'),
        # 应用根容器
        html.Div(id='root-container'),
        # 全局永久cookie登录令牌组件
        fuc.FefferyCookie(id='global-cookie-authorization-permanent', cookieKey='global-cookie-authorization-permanent', secure=True, expires=3600 * 24 * 365),
        # 全局会话cookie登录令牌组件
        fuc.FefferyCookie(id='global-cookie-authorization-session', cookieKey='global-cookie-authorization-session', secure=True),
    ],
    listenPropsMode='include',
    includeProps=['root-container.children'],
    minimum=0.33,
    color='#1677ff',
)


def handle_root_router_error(e):
    """处理根节点路由错误"""
    from dash_view.pages import page_500

    set_props(
        'root-container',
        {
            'children': page_500.render(e),
        },
    )


@app.callback(
    Output('root-container', 'children'),
    Input('global-url-init-load', 'data'),
    prevent_initial_call=True,
    on_error=handle_root_router_error,
)
def root_router(href):
    """判断是登录还是未登录"""
    rt_access = util_jwt.jwt_decode_from_session(verify_exp=True)
    if isinstance(rt_access, util_jwt.AccessFailType):
        return login.render_content()
    else:
        try:
            menu_access = MenuAccess(rt_access['user_name'])
        # 找不到该授权用户
        except NotFoundUserException as e:
            logger.warning(e.message)
            util_jwt.clear_access_token_from_session()
            return login.render_content()
        # # 如果session是永久，也就是用户登录勾选了保存会话，刷新jwt令牌，继续延长令牌有效期
        # if session.permanent:
        #     util_jwt.jwt_encode_save_access_to_session({'user_name': rt_access['user_name']}, session_permanent=True)
        return main.render_content(
            # 获取用户菜单权限，根据权限初始化主页内容
            menu_access=menu_access,
        )


# 如果首次加载，更新中继url
app.clientside_callback(
    """
        (href,trigger) => {
            if(trigger=='load'){
                return href;
            }else{
                return window.dash_clientside.no_update;
            }
        }
    """,
    Output('global-url-init-load', 'data'),
    Input('global-url-location', 'href'),
    [
        State('global-url-location', 'trigger'),
    ],
    prevent_initial_call=True,
)
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
