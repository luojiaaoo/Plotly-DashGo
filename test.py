import dash
import feffery_antd_components as fac
from dash import Patch
from dash.dependencies import Input, Output,State
from dash import dcc
from dash import set_props

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    update_title=None,
)

app.layout = (
    # 存储tab的key，和UI保持同步
    dcc.Store(id="global-tabs-keys", data=['首页']),
    fac.AntdButton(children='ADD', id='add'),
    fac.AntdTabs(
        id='tabs-container',
        items=[
            {
                'label': '首页',
                'key': '首页',
                'closable': True,
                'children': 'I am robot',
            }
        ],
        type='editable-card',
        className={
            'width': '100%',
            'paddingLeft': '15px',
            'paddingRight': '15px',
        },
    ),
)


@app.callback(
    Output('tabs-container', 'items', allow_duplicate=True),
    Input('add', 'nClicks'),
    State("global-tabs-keys", "data"),
    prevent_initial_call=True,
)
def callback_func(nClicks,keys):
    print(nClicks)
    p = Patch()
    p.append(
        {
            'label': str(nClicks),
            'key': str(nClicks),
            'closable': True,
            'children': 'I am robot',
        }
    )
    set_props("global-tabs-keys", {"data": keys + [str(nClicks)]})
    return p

@app.callback(
    Output('tabs-container', 'items', allow_duplicate=True),
    Input('tabs-container', 'latestDeletePane'),
    State("global-tabs-keys", "data"),
    prevent_initial_call=True,
)
def callback_func(latestDeletePane, keys):
    idx = keys.index(latestDeletePane)
    p = Patch()
    del p[idx]
    keys = list(keys)
    keys.pop(idx)
    set_props("global-tabs-keys", {"data": keys})
    return p

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=False)
