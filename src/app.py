from server import app, server  # noqa: F401
import feffery_utils_components as fuc
from dash import html, dcc
from config.access_factory import AccessFactory
import feffery_antd_components as fac
from dash.dependencies import Input, Output, State
from dash import set_props
from common.utilities import util_jwt, util_authorization
from dash_view.pages import main, login
from common.utilities.util_menu_access import MenuAccess
from common.exception import NotFoundUserException
from common.utilities.util_logger import Log
import sys

logger = Log.get_logger(__name__)

# 检查Python运行版本
if sys.version_info < (3, 9):
    raise Exception('Python version must above 3.9 !!')

# 启动检查权限
AccessFactory.check_access_meta()

# 全局功能组件+全局消息提示+全局通知信息+URL初始化中继组件+根容器
app.layout = lambda: fuc.FefferyTopProgress(
    [
        fuc.FefferySetFavicon(favicon='/assets/logo.ico'),
        # 全局url监听组件，仅仅起到监听的作用
        fuc.FefferyLocation(id='global-url-location'),
        # 注入全局消息提示容器
        fac.Fragment(id='global-message-container'),
        # 注入全局通知信息容器
        fac.Fragment(id='global-notification-container'),
        # 注入js执行
        fuc.FefferyExecuteJs(id='global-execute-js-output'),
        # 注入强制网页刷新组件
        fuc.FefferyReload(id='global-reload'),
        # 注入重定向组件容器，返回dcc.Location组件，重定向到新页面
        fac.Fragment(id='global-redirect-container'),
        # URL初始化中继组件，触发root_router回调执行
        dcc.Store(id='global-url-init-load'),
        # 应用根容器
        html.Div(id='root-container'),
    ],
    listenPropsMode='include',
    includeProps=['root-container.children'],
    minimum=0.33,
    color='#1677ff',
)


def handle_root_router_error(e):
    """处理根节点路由错误"""
    from dash_view.pages import page_500

    logger = Log.get_logger('global_exception')
    logger.exception(f'[exception]{e}')

    set_props(
        'root-container',
        {
            'children': page_500.render_content(e),
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
    rt_access = util_authorization.auth_validate(verify_exp=True)
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
            href=href,
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

app.clientside_callback(
    # 初始化vscode editor配置
    """
        (id) => {
        const script = document.createElement('script');
        script.textContent = `
            var require = {
                baseUrl: '/assets/vendor',
                paths: {'vs': 'monaco-editor/min/vs'},
                'vs/nls': { availableLanguages: { '*': 'zh-cn' } }
            }
        `;
        document.body.appendChild(script);
        return window.dash_clientside.no_update;
    }""",
    Input('root-container', 'id'),
)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8090, debug=True)
