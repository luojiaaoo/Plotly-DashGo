import feffery_antd_components as fac
import feffery_utils_components as fuc
from flask import request
from i18n import translator


def render_lang_content(color='#95afc0'):
    locale = request.cookies.get(translator.cookie_name) or translator.root_locale
    return fac.AntdTooltip(
        fac.AntdButton(
            fac.Fragment(
                # 国际化cookie
                fuc.FefferyCookie(id='global-locale', expires=3600 * 24 * 365, cookieKey=translator.cookie_name)
            ),
            id='global-locale-switch',
            icon=fac.AntdIcon(
                icon='md-translate',
                style={
                    'fontSize': '1.2em',
                    'verticalAlign': '-0.4em',
                    'color': color,
                },
            ),
            type='text',
            clickExecuteJsString=(
                """
                    window.dash_clientside.set_props('global-locale', { value: '%s' })
                    window.dash_clientside.set_props('global-reload', { reload: true })
                """
                % ('zh-cn' if locale == 'en-us' else 'en-us')
            ),
        ),
        placement='bottom',
        title='English / 中文',
    )
