from dash.dependencies import Input, Output, State
from server import app
from config.dash_melon_conf import LoginConf
from dash.exceptions import PreventUpdate
import dash
import feffery_utils_components as fuc
from dash import dcc

# 定义一个客户端回调函数，用于处理登录验证代码的显示逻辑，总是显示login的路径
app.clientside_callback(
    """
    (fc_count,timeoutCount) => {
        fc_count=fc_count || 0;
        if (fc_count>="""
    + str(LoginConf.VERIFY_CODE_SHOW_LOGIN_FAIL_COUNT)
    + """) {
            return [{'display':'flex'}, {'height': 'max(40%,600px)'}, 1, '/login'];
        }
        return [{'display':'None'}, {'height': 'max(35%,500px)'}, 0, '/login'];
    }
    """,
    [
        Output('login-verify-code-container', 'style'),
        Output('login-container', 'style'),
        Output('login-store-need-vc', 'data'),
        Output('login-location-no-refresh', 'pathname'),
    ],
    [
        Input('login-store-fc', 'data'),
        Input('timeout-trigger-verify-code', 'timeoutCount'),
    ],
    prevent_initial_call=True,
)


@app.callback(
    [
        Output('login-location-refresh-container', 'children'),
        Output('login-store-fc', 'data'),
        Output('login-message-container', 'children'),
        Output('login-verify-code-pic', 'refresh'),
    ],
    [
        Input('login-submit', 'nClicks'),
        Input('login-password', 'nSubmit'),
    ],
    [
        State('login-username', 'value'),
        State('login-password', 'value'),
        State('login-store-need-vc', 'data'),
        State('login-verify-code-input', 'value'),
        State('login-verify-code-pic', 'captcha'),
        State('login-store-fc', 'data'),
    ],
    prevent_initial_call=True,
)
def login(nClicks, nSubmit, username, password, need_vc, vc_input, pic_vc_value, fc):
    # 登录回调函数
    # 该函数处理用户的登录请求，并根据登录结果更新页面内容和状态
    # 参数:
    #   nClicks: 登录按钮点击次数
    #   nSubmit: 密码输入框提交次数
    #   username: 用户名
    #   password: 密码
    #   need_vc: 是否需要验证码
    #   vc_input: 用户输入的验证码
    #   pic_vc_value: 验证码图片中的正确验证码
    #   fc: 登录失败计数
    # 返回值:
    #   更新登录页面内容、登录状态和登录消息等
    if not nClicks and not nSubmit:
        raise PreventUpdate
    if not username or not password:
        return (
            dash.no_update,
            dash.no_update,
            fuc.FefferyFancyMessage('请输入账号和密码', type='error'),
            True,
        )
    if need_vc and vc_input != pic_vc_value:
        return (
            dash.no_update,
            dash.no_update,
            fuc.FefferyFancyMessage('验证码错误，请重新输入', type='error'),
            True,
        )
    if username == 'luoja' and password == '123456':
        return (
            dcc.Location(pathname='/dashborad', refresh=True, id='index-redirect'),
            0, # 重置登录失败次数
            dash.no_update,
            dash.no_update,
        )
    else:
        return (
            dash.no_update,
            fc + 1,
            fuc.FefferyFancyMessage('用户名或密码错误', type='error'),
            True,
        )
