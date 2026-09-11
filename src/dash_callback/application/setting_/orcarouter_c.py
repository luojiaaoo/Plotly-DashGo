"""Callbacks for the OrcaRouter provider page.

This module owns the whole GUI lifecycle of an OrcaRouter authorization:

* the two authentication choices (paste a key, or connect an account);
* the PKCE attempt, including every terminal path that must release the login lock
  (success, denial, exchange error, timeout, explicit cancel, switching method, and
  ``pagehide``);
* a monotonically increasing generation so a late response from an abandoned login
  can never overwrite a newer one;
* capability-filtered model discovery, where the options handed to the selector are
  always the filtered list and an incompatible previous value is cleared.

The Flow B (out-of-band) code is pasted back into this page. ``pagehide`` is handled
without depending on a guarded ``finally``: the browser clears the busy flag and the
hint synchronously, then posts a ``keepalive`` cancellation to ``/orcarouter/cancel``
so the server-side attempt is released even though the page is going away.
"""

from typing import Optional

import dash
import feffery_antd_components as fac
from dash import set_props
from dash.dependencies import Input, Output, State

from common.orcarouter import runtime
from common.orcarouter.catalog import (
    CAPABILITY_CHAT,
    CAPABILITY_EMBEDDING,
    CAPABILITY_IMAGE,
    CAPABILITY_RERANK,
    CAPABILITY_VIDEO,
)
from common.orcarouter.errors import CredentialError, NeedsReauthError, OrcaRouterError
from common.utilities.util_logger import Log
from dash_components import MessageManager
from i18n import t__setting
from server import app

logger = Log.get_logger(__name__)

#: UI capability name -> catalog capability constant.
_UI_CAPABILITY_MAP = {
    'chat': CAPABILITY_CHAT,
    'multimodal': CAPABILITY_CHAT,
    'embedding': CAPABILITY_EMBEDDING,
    'image': CAPABILITY_IMAGE,
    'video': CAPABILITY_VIDEO,
    'rerank': CAPABILITY_RERANK,
}

#: Capabilities that can never carry an attachment modality.
_TEXT_ONLY_CAPABILITIES = {'embedding', 'image', 'video', 'rerank'}

#: Install the ``pagehide`` listener once. It runs inside the real page, so the busy
#: flag and the authorization hint are cleared synchronously — the restored page must
#: not come back permanently busy — and the server-side attempt is cancelled with
#: ``keepalive`` rather than relying on a guarded ``finally`` that deliberately
#: refuses to mutate state for an abandoned generation.
_CLIENT_PAGEHIDE_HANDLER = """
(connectState) => {
    if (connectState && connectState.generation) {
        window.__orcaCurrentGeneration = connectState.generation;
    }
    if (window.__orcaPagehideBound) { return window.dash_clientside.no_update; }
    window.__orcaPagehideBound = true;
    window.addEventListener('pagehide', () => {
        const busy = document.getElementById('orcarouter-connect-busy');
        const hint = document.getElementById('orcarouter-connect-hint-fragment');
        const cancel = document.getElementById('orcarouter-cancel-connect');
        if (busy) { busy.innerHTML = ''; }
        if (hint) { hint.innerHTML = ''; }
        if (cancel) { cancel.disabled = true; }
        const generation = window.__orcaCurrentGeneration || 0;
        try {
            fetch('/orcarouter/cancel', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: new URLSearchParams({generation: String(generation)}).toString(),
                keepalive: true,
            });
        } catch (e) { /* the page is going away */ }
    });
    return window.dash_clientside.no_update;
}
"""


def _ui_capability(name: str) -> str:
    return _UI_CAPABILITY_MAP.get(name, CAPABILITY_CHAT)


def _required_modalities(ui_capability: str, attachments: Optional[list[str]]) -> list[str]:
    if ui_capability in _TEXT_ONLY_CAPABILITIES:
        return []
    return [m for m in (attachments or []) if m]


def _masked_status(credential) -> str:
    if credential is None:
        return '未配置'
    state = '需要重新授权' if credential.needs_reauth else '已配置'
    return f'{state} · {credential.api_base} · {credential.masked_key}'


def _short_error(exc: Exception) -> str:
    if isinstance(exc, OrcaRouterError):
        return str(exc)
    return f'[{type(exc).__name__}] {exc}'


def _authorize_url_value(state) -> str:
    return (state or {}).get('authorize_url') or ''


# ======================================================================================
# Authorization flow
# ======================================================================================


def _release_ui() -> None:
    """Clear every piece of the in-progress authorization UI.

    Called on success, denial, exchange error, timeout and explicit cancel, so the
    login lock is released on every terminal path and not only the happy one.
    """
    set_props('orcarouter-connect-busy', {'children': None})
    set_props('orcarouter-connect-hint-fragment', {'children': None})
    set_props('orcarouter-cancel-connect', {'disabled': True})


@app.callback(
    [
        Output('orcarouter-connect-state', 'data'),
        Output('orcarouter-connect-busy', 'children'),
    ],
    Input('orcarouter-start-oauth-connect', 'nClicks'),
    prevent_initial_call=True,
)
def start_oauth_connect(n_clicks):
    """Begin a PKCE attempt. A fresh verifier and state are generated here, every time.

    Flow B is used: DashGo is self-hosted software whose address differs on every
    deployment, so there is no callback address to predict.
    """
    try:
        payload = runtime.start_connect()
    except OrcaRouterError as exc:
        MessageManager.error(content=_short_error(exc))
        return dash.no_update, dash.no_update
    return payload, fac.AntdTag(content=t__setting('等待授权…'), color='processing')


@app.callback(
    [
        Output('orcarouter-authorize-url', 'value'),
        Output('orcarouter-open-authorize-url', 'href'),
        Output('orcarouter-open-authorize-url', 'disabled'),
        Output('orcarouter-oauth-status', 'children'),
        Output('orcarouter-cancel-connect', 'disabled'),
    ],
    Input('orcarouter-connect-state', 'data'),
    prevent_initial_call=True,
)
def render_connect_hint(state):
    """Publish the authorization URL and open the login lock.

    The verifier is never part of this payload — only the URL the user must open.
    """
    if not state or not state.get('authorize_url'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    return (
        state['authorize_url'],
        state['authorize_url'],
        False,
        state.get('instructions', ''),
        False,
    )


@app.callback(
    [
        Output('orcarouter-connect-state', 'data', allow_duplicate=True),
        Output('orcarouter-auth-code-input', 'value'),
        Output('orcarouter-auth-revision', 'data'),
    ],
    Input('orcarouter-submit-auth-code', 'nClicks'),
    [
        State('orcarouter-connect-state', 'data'),
        State('orcarouter-auth-code-input', 'value'),
        State('orcarouter-auth-revision', 'data'),
    ],
    prevent_initial_call=True,
)
def submit_auth_code(n_clicks, state, code, revision):
    """Exchange a pasted code for a key and persist it through the credential seam."""
    if not state or not state.get('generation'):
        MessageManager.error(content=t__setting('请先点击 Connect with OrcaRouter 发起授权'))
        return dash.no_update, dash.no_update, dash.no_update
    if not code:
        MessageManager.error(content=t__setting('请输入授权码'))
        return dash.no_update, dash.no_update, dash.no_update

    generation = state['generation']
    try:
        credential = runtime.complete_connect(generation, code)
    except (CredentialError, OrcaRouterError) as exc:
        _release_ui()
        MessageManager.error(content=_short_error(exc))
        return {}, '', (revision or 0) + 1

    _release_ui()
    MessageManager.success(content=t__setting('OrcaRouter 账号已连接'))
    # The generation that was just minted is logged, never the key itself.
    logger.info(f'OrcaRouter credential stored via PKCE generation={credential.generation}')
    return {}, '', (revision or 0) + 1


@app.callback(
    [
        Output('orcarouter-connect-state', 'data', allow_duplicate=True),
        Output('orcarouter-auth-code-input', 'value', allow_duplicate=True),
    ],
    Input('orcarouter-cancel-connect', 'nClicks'),
    State('orcarouter-connect-state', 'data'),
    prevent_initial_call=True,
)
def cancel_oauth_connect(n_clicks, state):
    """Explicit cancel: release the pending attempt and clear the UI."""
    generation = (state or {}).get('generation')
    if generation:
        runtime.cancel_connect(generation)
    _release_ui()
    MessageManager.info(content=t__setting('已取消授权'))
    return {}, ''


app.clientside_callback(
    _CLIENT_PAGEHIDE_HANDLER,
    Output('orcarouter-pagehide-listener', 'children', allow_duplicate=True),
    Input('orcarouter-connect-state', 'data'),
    prevent_initial_call=True,
)


# ======================================================================================
# API-key choice
# ======================================================================================


@app.callback(
    [
        Output('orcarouter-api-key-masked', 'children'),
        Output('orcarouter-connection-status', 'children'),
        Output('orcarouter-auth-revision', 'data', allow_duplicate=True),
        Output('orcarouter-connect-state', 'data', allow_duplicate=True),
    ],
    [
        Input('orcarouter-api-key-save', 'nClicks'),
        Input('orcarouter-api-key-clear', 'nClicks'),
    ],
    [
        State('orcarouter-api-key-input', 'value'),
        State('orcarouter-auth-revision', 'data'),
    ],
    prevent_initial_call=True,
)
def manage_api_key(save_clicks, clear_clicks, api_key, revision):
    """Save or clear the pasted key. Switching method releases any pending PKCE attempt."""
    trigger = dash.ctx.triggered_id
    revision = (revision or 0) + 1

    if trigger == 'orcarouter-api-key-clear':
        runtime.cancel_all_connects()
        runtime.clear_api_key()
        _release_ui()
        MessageManager.success(content=t__setting('已清除 OrcaRouter API Key'))
        return t__setting('未配置'), _masked_status(runtime.current_credential()), revision, {}

    if not api_key:
        MessageManager.error(content=t__setting('请输入 API Key'))
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    try:
        credential = runtime.save_api_key(api_key)
    except OrcaRouterError as exc:
        MessageManager.error(content=_short_error(exc))
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # A successful paste supersedes an in-flight browser authorization.
    runtime.cancel_all_connects()
    _release_ui()
    MessageManager.success(content=t__setting('OrcaRouter API Key 已保存'))
    logger.info(f'OrcaRouter credential stored via API key generation={credential.generation}')
    return credential.masked_key, _masked_status(credential), revision, {}


# ======================================================================================
# Model catalog
# ======================================================================================


def build_model_state(ui_capability: str, attachments: Optional[list[str]], current_value: Optional[str] = None) -> tuple:
    """Return ``(options_store, selector_options, value, status)`` for a capability set.

    Used both at render time — so the selector is populated the moment the page loads,
    the same way the other settings pages build their tabs — and by the refresh
    callback. The options handed to the selector are always the filtered list; a
    pre-send guard would not be enough.
    """
    ui_capability = ui_capability or 'chat'
    catalog_capability = _ui_capability(ui_capability)
    required = _required_modalities(ui_capability, attachments)

    credential = runtime.current_credential()
    if credential is None:
        return [], [], None, t__setting('未检测到 OrcaRouter 凭据，请先在上方配置 API Key 或连接账号')

    try:
        options, degraded = runtime.discover_model_options(
            capability=catalog_capability,
            required_modalities=required,
            credential=credential,
        )
    except NeedsReauthError as exc:
        return [], [], None, f'⚠ {_short_error(exc)}'
    except Exception as exc:  # pragma: no cover - defensive
        return [], [], None, f'⚠ {_short_error(exc)}'

    selector_options = [{'label': f'{option["label"]} ({option["model_id"]})', 'value': option['value']} for option in options]

    if degraded:
        status = t__setting('实时模型目录不可用，当前显示已验证的备用目录（降级）')
    elif not selector_options:
        status = t__setting('当前能力下没有可用模型')
    else:
        status = t__setting('模型目录就绪') + f' · {len(selector_options)}'

    value = current_value
    if value is not None and value not in {option['value'] for option in options}:
        value = None
        MessageManager.warning(content=t__setting('已选模型不再兼容当前能力/附件，请重新选择'))

    return [dict(option) for option in options], selector_options, value, status


def initial_model_state() -> tuple:
    """Render-time model state for the page's opening capability (text chat, no attachment)."""
    return build_model_state('chat', [])


def initial_credential_state() -> tuple:
    """Render-time credential display. Masked only — never the key itself."""
    credential = runtime.current_credential()
    masked = credential.masked_key if credential else t__setting('未配置')
    return masked, _masked_status(credential)


@app.callback(
    [
        Output('orcarouter-model-options-store', 'data'),
        Output('orcarouter-model-select', 'options'),
        Output('orcarouter-model-select', 'value'),
        Output('orcarouter-model-status', 'children'),
    ],
    [
        Input('orcarouter-model-capability', 'value'),
        Input('orcarouter-attachment-modality', 'value'),
        Input('orcarouter-model-refresh', 'nClicks'),
        Input('orcarouter-auth-revision', 'data'),
    ],
    State('orcarouter-model-select', 'value'),
    prevent_initial_call=False,
)
def refresh_model_options(ui_capability, attachments, refresh_clicks, revision, current_value):
    """Rebuild the selector options when the capability, the attachments or the credential change."""
    return build_model_state(ui_capability, attachments, current_value)


@app.callback(
    Output('orcarouter-model-detail', 'children'),
    Input('orcarouter-model-select', 'value'),
    State('orcarouter-model-options-store', 'data'),
    prevent_initial_call=True,
)
def render_model_detail(model_id, options):
    if not model_id:
        return ''
    for option in options or []:
        if option.get('value') == model_id:
            modalities = ', '.join(option.get('input_modalities') or []) or 'text'
            efforts = ', '.join(option.get('reasoning_efforts') or []) or '-'
            return (
                f'endpoints: {", ".join(option.get("supported_endpoint_types") or [])} · '
                f'context: {option.get("context_length")} · input: {modalities} · '
                f'reasoning: {option.get("reasoning")} ({efforts})'
            )
    return ''


# ======================================================================================
# Inference test
# ======================================================================================


@app.callback(
    Output('orcarouter-test-result', 'children'),
    Input('orcarouter-send-test', 'nClicks'),
    [
        State('orcarouter-model-select', 'value'),
        State('orcarouter-test-prompt', 'value'),
    ],
    prevent_initial_call=True,
)
def send_test_request(n_clicks, model_id, prompt):
    """One real completion through the provider adapter, using the stored credential."""
    credential = runtime.current_credential()
    if credential is None:
        return t__setting('未检测到 OrcaRouter 凭据')
    if not model_id:
        return t__setting('请先选择模型')
    try:
        body = runtime.send_chat(
            credential,
            model=model_id,
            messages=[{'role': 'user', 'content': prompt or 'ping'}],
            max_tokens=64,
        )
    except OrcaRouterError as exc:
        return f'⚠ {_short_error(exc)}'
    choices = body.get('choices') or []
    if not choices:
        return t__setting('推理接口返回了空响应')
    return (choices[0].get('message') or {}).get('content', '')
