from server import app
from dash.dependencies import Input, Output, State

app.clientside_callback(
    """
    (data) => {
        if (data) {
            window.dash_clientside.set_props(
                'monitor-sys-info',
                {
                    children: data
                }
            )
        }
    }
    """,
    Input('monitor-sys-info-sse', 'data'),
    prevent_initial_call=True,
)
