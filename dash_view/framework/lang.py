import feffery_antd_components as fac
from flask import request
from server import app
from dash.dependencies import Input, Output
import feffery_utils_components as fuc
from i18n import translator


def render_lang_content():
    return fac.AntdCompact(
        [
            fac.AntdButton(
                'ZH',
                id='global-language-zh',
                clickExecuteJsString="""
                    window.dash_clientside.set_props('global-locale', { value: 'zh-cn' })
                    window.dash_clientside.set_props('global-reload', { reload: true })
                """,
            ),
            fac.AntdButton(
                'EN',
                id='global-language-en',
                clickExecuteJsString="""
                    window.dash_clientside.set_props('global-locale', { value: 'en-us' })
                    window.dash_clientside.set_props('global-reload', { reload: true })
                """,
            ),
            fuc.FefferyCookie(
                id='global-locale',
                expires=3600 * 24 * 365,
                cookieKey=translator.cookie_name,
            ),
        ],
        className={
            '& span': {'fontSize': '10px', 'fontWeight': 'bold'},
            '& .ant-btn': {'height': '1.5em'},
            '& #global-language-zh': {'backgroundColor': '#1C69D1', 'color': '#eee'} if translator.get_current_locale() == 'zh-cn' else {'color': '#999999'},
            '& #global-language-en': {'backgroundColor': '#1C69D1', 'color': '#eee'} if translator.get_current_locale() == 'en-us' else {'color': '#999999'},
        },
    )
