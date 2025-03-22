import feffery_utils_components as fuc
import feffery_antd_components as fac
from config.dashgo_conf import ShowConf, JwtConf, LoginConf
from dash import dcc
from dash_view.framework.lang import render_lang_content
from flask import session
import dash_callback.pages.login_c  # noqa
from i18n import t__other


def render_content():
    return fuc.FefferyDiv(
        children=[
            fac.Fragment(id='login-message-container'),
            fuc.FefferyDiv(
                id='login-container',
                children=[
                    fuc.FefferyDiv(
                        id='login-title',
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
                                'key': '密码登录',
                                'label': fac.AntdText(
                                    t__other('密码登录'),
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
                                                            placeholder=t__other('请输入用户名'),
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
                                                            placeholder=t__other('请输入密码'),
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
                                                        placeholder=t__other('请输入验证码'),
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
                                                label=t__other('保持{}小时免登录').format(JwtConf.JWT_EXPIRE_MINUTES // 60),
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
                                                t__other('登录'),
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
                                            dcc.Store(id='login-password-sha256'),
                                            # 全局cookie登录令牌组件
                                            fuc.FefferyCookie(
                                                id='global-cookie-authorization',
                                                cookieKey='global-cookie-authorization',
                                                secure=True,
                                                **(dict(expires=3600 * 24 * 365) if session.get('keep_login') else {}),
                                            ),
                                        ],
                                        direction='vertical',
                                        className={
                                            'width': '100%',
                                        },
                                    )
                                ],
                            },
                            {
                                'key': '动态码登录',
                                'label': fac.AntdText(
                                    t__other('动态码登录'),
                                    className={
                                        'color': 'rgb(22,119,255)',
                                    },
                                ),
                                'children': [
                                    fac.AntdSpace(
                                        [
                                            fac.AntdInput(
                                                id='login-username-otp',
                                                prefix=fac.AntdIcon(icon='antd-user'),
                                                placeholder=t__other('请输入用户名'),
                                                className={
                                                    'marginTop': '20px',
                                                    'marginBottom': '20px',
                                                },
                                            ),
                                            fac.AntdText(t__other('动态码：'), keyboard=True, strong=True),
                                            fac.AntdOTP(id='login-otp'),
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
                        size='small',
                        tabBarGutter=0,
                        tabBarRightExtraContent=render_lang_content(),
                    ),
                    # >>>>> 重定向组件
                    fac.Fragment(id='login-location-refresh-container'),
                    # >>>>> 地址栏控制组件
                    dcc.Location(id='login-location-no-refresh', refresh=False),
                    # >>>>> 消息组件
                    fac.Fragment(id='login-message-container'),
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
