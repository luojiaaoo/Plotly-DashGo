from server import app
from dash.dependencies import Input, Output, State
import feffery_antd_components as fac
from dash_components import Table
import dash
from dash import set_props, ClientsideFunction
from dash_components import MessageManager
import time
from feffery_dash_utils.style_utils import style


app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='inject_xterm_js',
    ),
    Input('host-node-init-timeout', 'timeoutCount'),
    State('host-node-xterm-mount-target', 'id'),
)
