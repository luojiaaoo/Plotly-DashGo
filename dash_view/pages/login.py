import feffery_utils_components as fuc
import feffery_antd_components as fac
from config.dash_melon_conf import ShowConf, JwtConf, LoginConf
from dash import dcc
from dash.dependencies import Input, Output, State
from server import app
from dash.exceptions import PreventUpdate
import dash
from dash_view.framework.lang import render_lang_content
from flask_babel import gettext as _  # noqa

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


def render_content():
    return fuc.FefferyDiv(
        children=[
            fuc.FefferyDiv(
                id='login-container',
                children=[
                    fuc.FefferyDiv(
                        children=ShowConf.APP_NAME,
                        className={
                            'fontWeight': 'bold',
                            'letterSpacing': '2px',
                            'fontFamily': "'Microsoft YaHei', sans-serif",
                            'fontSize': '30px',
                            'height': '15%',
                            'display': 'flex',
                            'justifyContent': 'center',
                            'alignItems': 'center',
                            'color': 'rgb(245,245,245)',
                            'padding': '20px 0 0 0',
                        },
                    ),
                    fac.AntdTabs(
                        items=[
                            {
                                'key': '账号密码登录',
                                'label': fac.AntdText(
                                    _('账号密码登录'),
                                    className={
                                        'color': 'rgb(22,119,255)',
                                    },
                                ),
                                'children': [
                                    fac.AntdSpace(
                                        [
                                            fac.AntdForm(
                                                [
                                                    fac.AntdFormItem(
                                                        fac.AntdInput(
                                                            id='login-username',
                                                            prefix=fac.AntdIcon(icon='antd-user'),
                                                            placeholder=_('请输入用户名'),
                                                            className={
                                                                'marginTop': '20px',
                                                            },
                                                        ),
                                                        className={'marginBottom': 0},
                                                    ),
                                                    fac.AntdFormItem(
                                                        fac.AntdInput(
                                                            id='login-password',
                                                            prefix=fac.AntdIcon(icon='antd-lock'),
                                                            mode='password',
                                                            passwordUseMd5=True,
                                                            placeholder=_('请输入密码'),
                                                            className={
                                                                'marginTop': '25px',
                                                            },
                                                        ),
                                                        className={'marginBottom': 0},
                                                    ),
                                                ],
                                            ),
                                            fac.AntdFlex(
                                                [
                                                    fac.AntdInput(
                                                        id='login-verify-code-input',
                                                        prefix=fac.AntdIcon(icon='antd-right'),
                                                        placeholder=_('请输入验证码'),
                                                        allowClear=True,
                                                        className={
                                                            'marginRight': '20px',
                                                        },
                                                    ),
                                                    fuc.FefferyCaptcha(
                                                        id='login-verify-code-pic',
                                                        width=100,
                                                        charNum=LoginConf.VERIFY_CODE_CHAR_NUM,
                                                    ),
                                                ],
                                                id='login-verify-code-container',
                                                className={
                                                    'marginTop': '20px',
                                                },
                                                style={
                                                    'display': 'None',
                                                },
                                            ),
                                            fac.AntdCheckbox(
                                                id='login-keep-login-status',
                                                label=_('保持{}小时免登录').format(
                                                    JwtConf.JWT_EXPIRE_MINUTES // 60
                                                ),
                                                checked=False,
                                                className={
                                                    'marginTop': '10px',
                                                    'fontWeight': 'bold',
                                                    'letterSpacing': '2px',
                                                    'fontFamily': "'Microsoft YaHei', sans-serif",
                                                    'fontSize': '12px',
                                                    'color': 'rgb(245,245,245)',
                                                },
                                            ),
                                            fac.AntdButton(
                                                _('登录'),
                                                id='login-submit',
                                                type='primary',
                                                block=True,
                                                className={
                                                    'marginTop': '35px',
                                                    'height': '3em',
                                                    'borderRadius': '1.5em',
                                                },
                                            ),
                                            dcc.Store(id='login-store-need-vc', storage_type='local'),
                                            dcc.Store(id='login-store-fc', storage_type='local'),
                                            fuc.FefferyTimeout(id='timeout-trigger-verify-code', delay=0),
                                            dcc.Location(id='login-location-no-refresh', refresh=False),
                                            fac.Fragment(id='login-location-refresh-container'),
                                            dcc.Store(id='login-password-sha256'),
                                            fac.Fragment(id='login-message-container'),
                                            # 为了和主页main统一回调
                                            fuc.FefferyReload(id='global-reload'),
                                        ],
                                        direction='vertical',
                                        className={
                                            'width': '100%',
                                        },
                                    )
                                ],
                            },
                        ],
                        className={
                            'height': '85%',
                            'width': '90%',
                        },
                        tabBarRightExtraContent=render_lang_content(),
                    ),
                ],
                className={
                    'width': 'max(25%,300px)',
                    'height': 'max(40%,600px)',
                    'marginRight': '15%',
                    'backdropFilter': 'blur(10px)',
                    'backgroundColor': 'rgba(0, 0, 0, 0.15)',
                    'borderRadius': '10px',
                    'display': 'flex',
                    'flexDirection': 'column',
                    'justifyContent': 'center',
                    'alignItems': 'center',
                    'boxShadow': '0 10px 20px rgba(0, 0, 0, 0.4)',
                    'border': '1px solid rgba(255, 255, 255, 0.4)',
                    'animation': 'float 2s ease-in-out infinite',
                },
            ),
        ],
        className={
            'display': 'flex',
            'backgroundImage': 'url("/assets/imgs/login_background.jpeg")',
            'backgroundSize': 'cover',
            'backgroundPosition': 'center center',
            'backgroundAttachment': 'fixed',
            'backgroundRepeat': 'no-repeat',
            'width': '100vw',
            'height': '100vh',
            'justifyContent': 'flex-end',
            'alignItems': 'center',
            '.ant-input-affix-wrapper, .ant-tabs-tab .ant-typography, .ant-btn': {
                'letterSpacing': '2px',
                'fontFamily': "'Microsoft YaHei', sans-serif",
                'fontSize': '18px',
                'width': '100%',
                'padding': '10px 10px',
            },
        },
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
        State('login-verify-code-container', 'style'),
        State('login-keep-login-status', 'checked'),
    ],
    prevent_initial_call=True,
)
def login(
    nClicks,
    password_nSubmit,
    vc_input_nSubmit,
    user_name,
    password_sha256,
    need_vc,
    vc_input,
    pic_vc_value,
    fc,
    vc_style,
    is_keep_login_status,
):
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
    if not nClicks and not password_nSubmit and not vc_input_nSubmit:
        raise PreventUpdate
    if vc_style['display'] == 'flex' and dash.ctx.triggered_prop_ids == {
        'login-password.nSubmit': 'login-password'
    }:
        raise PreventUpdate
    # e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 为空字符串的sha256加密结果
    if (
        not user_name
        or password_sha256 == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        or not password_sha256
    ):
        return (
            dash.no_update,
            dash.no_update,
            fuc.FefferyFancyMessage(_('请输入账号和密码'), type='error'),
            True,
        )
    if need_vc and vc_input != pic_vc_value:
        return (
            dash.no_update,
            dash.no_update,
            fuc.FefferyFancyMessage(_('验证码错误，请重新输入'), type='error'),
            True,
        )
    from common.api.user import login

    if login.user_login(user_name, password_sha256, is_keep_login_status):
        return (
            dcc.Location(pathname='/dashboard/workbench', refresh=True, id='index-redirect'),
            0,  # 重置登录失败次数
            dash.no_update,
            dash.no_update,
        )
    else:
        return (
            dash.no_update,
            (fc or 0) + 1,
            fuc.FefferyFancyMessage(_('用户名或密码错误'), type='error'),
            True,
        )
