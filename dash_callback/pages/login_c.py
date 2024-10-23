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

app.clientside_callback(
    """
    (data) => {
        // 将字符串转换为 Uint8Array
        const encoder = new TextEncoder();
        const dataUint8 = encoder.encode(data);

        // 使用 Web Cryptography API 计算 SHA-256 哈希
        return crypto.subtle.digest('SHA-256', dataUint8).then(hashBuffer => {
            // 将 ArrayBuffer 转换为十六进制字符串
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
            return hashHex;
        });
    }
    """,
    Output('login-password-sha256', 'data'),
    Input('login-password', 'value'),
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
        Input('login-verify-code-input', 'nSubmit'),
    ],
    [
        State('login-username', 'value'),
        State('login-password-sha256', 'data'),
        State('login-store-need-vc', 'data'),
        State('login-verify-code-input', 'value'),
        State('login-verify-code-pic', 'captcha'),
        State('login-store-fc', 'data'),
        State('login-verify-code-container','style')
    ],
    prevent_initial_call=True,
)
def login(nClicks, password_nSubmit, vc_input_nSubmit ,user_name, password_sha256, need_vc, vc_input, pic_vc_value, fc, vc_style):
    # 登录回调函数
    # 该函数处理用户的登录请求，并根据登录结果更新页面内容和状态
    # 参数:
    #   nClicks: 登录按钮点击次数
    #   nSubmit: 密码输入框提交次数
    #   user_name: 用户名
    #   password: 密码
    #   need_vc: 是否需要验证码
    #   vc_input: 用户输入的验证码
    #   pic_vc_value: 验证码图片中的正确验证码
    #   fc: 登录失败计数
    # 返回值:
    #   更新登录页面内容、登录状态和登录消息等
    if not nClicks and not password_nSubmit and not password_nSubmit:
        raise PreventUpdate
    if vc_style['display'] == 'flex' and dash.ctx.triggered_prop_ids=={'login-password.nSubmit': 'login-password'}:
        raise PreventUpdate
    # e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 为空字符串的sha256加密结果
    if not user_name or password_sha256=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' or not password_sha256:
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
    from common.api.user import login

    if login.user_login(user_name, password_sha256):
        return (
            dcc.Location(pathname='/dashborad', refresh=True, id='index-redirect'),
            0,  # 重置登录失败次数
            dash.no_update,
            dash.no_update,
        )
    else:
        return (
            dash.no_update,
            (fc or 0) + 1,
            fuc.FefferyFancyMessage('用户名或密码错误', type='error'),
            True,
        )
