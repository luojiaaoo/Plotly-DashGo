from server import app
from dash.dependencies import Input, Output, State

app.clientside_callback(
    """(data) => {
        console.log(data);
        data = data ? JSON.parse(data) : {};
        window.dash_clientside.set_props(
            'monitor-sys-info',
            {
                children: (data.content ? data.content.replace(/<line-break>/g, '\\n') : '')
            }
        );
    }""",
    Input('monitor-sys-info-sse', 'data'),
    prevent_initial_call=True,
)
