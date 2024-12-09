import feffery_utils_components as fuc
from config.dash_melon_conf import LoginConf
from dash import dcc
from dash.dependencies import Input, Output, State
from server import app
from dash.exceptions import PreventUpdate
import dash
from i18n import t__other


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
    r"""
    (data) => {
        function SHA256(s){
            var chrsz   = 8;
            var hexcase = 0;
            function safe_add (x, y) {
                var lsw = (x & 0xFFFF) + (y & 0xFFFF);
                var msw = (x >> 16) + (y >> 16) + (lsw >> 16);
                return (msw << 16) | (lsw & 0xFFFF);
            }
            function S (X, n) { return ( X >>> n ) | (X << (32 - n)); }
            function R (X, n) { return ( X >>> n ); }
            function Ch(x, y, z) { return ((x & y) ^ ((~x) & z)); }
            function Maj(x, y, z) { return ((x & y) ^ (x & z) ^ (y & z)); }
            function Sigma0256(x) { return (S(x, 2) ^ S(x, 13) ^ S(x, 22)); }
            function Sigma1256(x) { return (S(x, 6) ^ S(x, 11) ^ S(x, 25)); }
            function Gamma0256(x) { return (S(x, 7) ^ S(x, 18) ^ R(x, 3)); }
            function Gamma1256(x) { return (S(x, 17) ^ S(x, 19) ^ R(x, 10)); }
            function core_sha256 (m, l) {
                var K = new Array(0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5, 0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5, 0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3, 0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174, 0xE49B69C1, 0xEFBE4786, 0xFC19DC6, 0x240CA1CC, 0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA, 0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7, 0xC6E00BF3, 0xD5A79147, 0x6CA6351, 0x14292967, 0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13, 0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85, 0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3, 0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070, 0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5, 0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3, 0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208, 0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2);
                var HASH = new Array(0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19);
                var W = new Array(64);
                var a, b, c, d, e, f, g, h, i, j;
                var T1, T2;
                m[l >> 5] |= 0x80 << (24 - l % 32);
                m[((l + 64 >> 9) << 4) + 15] = l;
                for ( var i = 0; i<m.length; i+=16 ) {
                    a = HASH[0];
                    b = HASH[1];
                    c = HASH[2];
                    d = HASH[3];
                    e = HASH[4];
                    f = HASH[5];
                    g = HASH[6];
                    h = HASH[7];
                    for ( var j = 0; j<64; j++) {
                        if (j < 16) W[j] = m[j + i];
                        else W[j] = safe_add(safe_add(safe_add(Gamma1256(W[j - 2]), W[j - 7]), Gamma0256(W[j - 15])), W[j - 16]);
                        T1 = safe_add(safe_add(safe_add(safe_add(h, Sigma1256(e)), Ch(e, f, g)), K[j]), W[j]);
                        T2 = safe_add(Sigma0256(a), Maj(a, b, c));
                        h = g;
                        g = f;
                        f = e;
                        e = safe_add(d, T1);
                        d = c;
                        c = b;
                        b = a;
                        a = safe_add(T1, T2);
                    }
                    HASH[0] = safe_add(a, HASH[0]);
                    HASH[1] = safe_add(b, HASH[1]);
                    HASH[2] = safe_add(c, HASH[2]);
                    HASH[3] = safe_add(d, HASH[3]);
                    HASH[4] = safe_add(e, HASH[4]);
                    HASH[5] = safe_add(f, HASH[5]);
                    HASH[6] = safe_add(g, HASH[6]);
                    HASH[7] = safe_add(h, HASH[7]);
                }
                return HASH;
            }
            function str2binb (str) {
                var bin = Array();
                var mask = (1 << chrsz) - 1;
                for(var i = 0; i < str.length * chrsz; i += chrsz) {
                    bin[i>>5] |= (str.charCodeAt(i / chrsz) & mask) << (24 - i%32);
                }
                return bin;
            }
            function Utf8Encode(string) {
                string = string.replace(/\r\n/g,"\n");
                var utftext = "";
                for (var n = 0; n < string.length; n++) {
                    var c = string.charCodeAt(n);
                    if (c < 128) {
                        utftext += String.fromCharCode(c);
                    }
                    else if((c > 127) && (c < 2048)) {
                        utftext += String.fromCharCode((c >> 6) | 192);
                        utftext += String.fromCharCode((c & 63) | 128);
                    }
                    else {
                        utftext += String.fromCharCode((c >> 12) | 224);
                        utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                        utftext += String.fromCharCode((c & 63) | 128);
                    }
                }
                return utftext;
            }
            function binb2hex (binarray) {
                var hex_tab = hexcase ? "0123456789ABCDEF" : "0123456789abcdef";
                var str = "";
                for(var i = 0; i < binarray.length * 4; i++) {
                    str += hex_tab.charAt((binarray[i>>2] >> ((3 - i%4)*8+4)) & 0xF) +
                    hex_tab.charAt((binarray[i>>2] >> ((3 - i%4)*8  )) & 0xF);
                }
                return str;
            }
            s = Utf8Encode(s);
            return binb2hex(core_sha256(str2binb(s), s.length * chrsz));
        }
        const hashHex = SHA256(data);
        return hashHex;
    }
    """,
    Output('login-password-sha256', 'data'),
    Input('login-password', 'value'),
    prevent_initial_call=True,
)


# 密码登录
@app.callback(
    [
        Output('login-location-refresh-container', 'children', allow_duplicate=True),
        Output('login-store-fc', 'data'),
        Output('login-message-container', 'children', allow_duplicate=True),
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
    if vc_style['display'] == 'flex' and dash.ctx.triggered_prop_ids == {'login-password.nSubmit': 'login-password'}:
        raise PreventUpdate
    # e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 为空字符串的sha256加密结果
    if not user_name or password_sha256 == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' or not password_sha256:
        return (
            dash.no_update,
            dash.no_update,
            fuc.FefferyFancyMessage(t__other('请输入账号和密码'), type='error'),
            True,
        )
    if need_vc and vc_input != pic_vc_value:
        return (
            dash.no_update,
            dash.no_update,
            fuc.FefferyFancyMessage(t__other('验证码错误，请重新输入'), type='error'),
            True,
        )

    def user_login(user_name: str, password_sha256: str, is_keep_login_status: bool) -> bool:
        from database.sql_db.dao import dao_user
        from common.utilities.util_jwt import jwt_encode_save_access_to_session

        if dao_user.user_password_verify(user_name=user_name, password_sha256=password_sha256):
            jwt_encode_save_access_to_session({'user_name': user_name}, session_permanent=is_keep_login_status)
            return True
        return False

    if user_login(user_name, password_sha256, is_keep_login_status):
        return (
            dcc.Location(pathname='/dashboard_/workbench', refresh=True, id='index-redirect'),
            0,  # 重置登录失败次数
            dash.no_update,
            dash.no_update,
        )
    else:
        return (
            dash.no_update,
            (fc or 0) + 1,
            fuc.FefferyFancyMessage(t__other('用户名或密码错误'), type='error'),
            True,
        )


# 动态码登录
@app.callback(
    [
        Output('login-location-refresh-container', 'children', allow_duplicate=True),
        Output('login-message-container', 'children', allow_duplicate=True),
        Output('login-otp', 'value'),
    ],
    Input('login-otp', 'value'),
    State('login-username-otp', 'value'),
    prevent_initial_call=True,
)
def otp_login(otp_value, user_name):
    from otpauth import TOTP
    from database.sql_db.dao import dao_user
    from common.utilities.util_jwt import jwt_encode_save_access_to_session

    otp_secret = dao_user.get_otp_secret(user_name)
    totp = TOTP(otp_secret.encode())
    if totp.verify(int(otp_value)):
        jwt_encode_save_access_to_session({'user_name': user_name}, session_permanent=False)
        return (
            dcc.Location(pathname='/dashboard_/workbench', refresh=True, id='index-redirect'),
            dash.no_update,
            dash.no_update,
        )
    else:
        return (
            dash.no_update,
            fuc.FefferyFancyMessage(t__other('动态码验证错误'), type='error'),
            None,
        )
