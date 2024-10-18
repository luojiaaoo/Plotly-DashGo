import os

import dash
from config.dash_melon_conf import ShowConf,FlaskConf

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    compress=True,
    update_title=None,
)
app.server.config['COMPRESS_ALGORITHM'] = 'br'
app.server.config['COMPRESS_BR_LEVEL'] = 9
app.server.secret_key = FlaskConf.COOKIE_SESSION_SECRET_KEY
app.title = ShowConf.WEB_TITLE