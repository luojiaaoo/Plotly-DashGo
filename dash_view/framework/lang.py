import feffery_antd_components as fac
from flask import session
from server import app
from dash.dependencies import Input, Output


# 切换中文
@app.callback(
    Output('global-reload', 'reload', allow_duplicate=True),
    Input('global-language-zh', 'nClicks'),
    prevent_initial_call=True,
)
def lang_zh(nClicks):
    session['lang'] = 'zh'
    return True


# 切换英文
@app.callback(
    Output('global-reload', 'reload', allow_duplicate=True),
    Input('global-language-en', 'nClicks'),
    prevent_initial_call=True,
)
def lang_en(nClicks):
    session['lang'] = 'en'
    return True


def render_lang_content():
    from server import select_locale, server

    return (
        fac.AntdCompact(
            [
                fac.AntdButton('ZH', id='global-language-zh'),
                fac.AntdButton('EN', id='global-language-en'),
            ],
            className={
                '& span': {'fontSize': '10px', 'fontWeight': 'bold'},
                '& .ant-btn': {'height': '1em'},
                '& #global-language-zh': {'backgroundColor': '#1C69D1', 'color': '#eee'}
                if session.get('lang', None)
                in [
                    'zh',
                    *([None] if (select_locale() or server.config['BABEL_DEFAULT_LOCALE'] == 'zh') else []),
                ]
                else {'color': '#999999'},
                '& #global-language-en': {'backgroundColor': '#1C69D1', 'color': '#eee'}
                if session.get('lang', None) in ['en', [None]]
                else {'color': '#999999'},
            },
        ),
    )
