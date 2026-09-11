# OrcaRouter integration

[OrcaRouter](https://www.orcarouter.ai) is an OpenAI-compatible AI gateway built for both models and agents, with adaptive routing, automatic failover, zero-markup inference, observability, guardrails, and agent-tool governance. It also runs gateway-level, zero-trust security for AI agents on the same endpoint — screening every prompt/response and governing every tool call on a default-deny basis, with no application code changes.

DashGo registers OrcaRouter as a first-class provider under **Settings → OrcaRouter**.

## Two ways to connect

Both produce the **same** kind of credential — a normal OrcaRouter API key (`sk-orca-…`) that belongs to the user, is billed to their account, is listed in their console and is revocable by them at any time. Both drive the same inference endpoint and the same model catalog.

| Choice | ID | Use when | Credential source |
| --- | --- | --- | --- |
| OrcaRouter - API | `orcarouter` | you already hold a key | paste an `sk-orca-…` key |
| OrcaRouter - Auth | `orcarouter-oauth` | you have no key yet | OAuth 2.0 + PKCE in a browser |

A user without a browser can still paste a key; a user without a key can authorize an account.

### 1. API key

Paste the key under "1. OrcaRouter - API" and save. It is stored with the project's existing secret mechanism — the `sys_orcarouter_credential` table, encrypted by `util_encrypt` (AES-CBC under `CommonConf.ENCRYPT_KEY`). No new secret store is introduced. The UI only ever shows a masked value such as `sk-orca-…SZFS`, and the key can be cleared at any time.

The format check only catches obvious input mistakes; an `sk-orca-…` prefix is not proof that a credential is valid, and this integration never sends a billable request just to make a settings form look green.

Key management and revocation: <https://www.orcarouter.ai/console/authorized-apps>

### 2. Connect with OrcaRouter (OAuth 2.0 + PKCE)

Click **Connect with OrcaRouter**. Two authorization methods are offered:

* **Paste authorization code (Flow B, default)** — the consent screen displays a code which the user pastes back. DashGo is self-hosted software whose install address differs on every deployment, so there is no callback address to predict; Flow B needs none.
* **Automatic browser callback (Flow A)** — for a browser running on the same machine as DashGo. It listens on a random `127.0.0.1` port and compares `state` in constant time before the code is used.

Both always send `code_challenge_method=S256`. Every attempt generates a fresh verifier and state from the operating system CSPRNG; the challenge is unpadded `base64url(sha256(verifier))`. The verifier never enters a URL and is never logged — it appears only in the code-exchange request body. No client secret is involved and no redirect URI has to be pre-registered.

The exchanged key is a **durable API key, not a refresh token**: it is reused across restarts until it is revoked. There is no proactive refresh and no re-authorization on every launch (a cap of 10 PKCE-issued keys per user per 24 hours applies). When inference returns `401`, only the **exact credential generation that issued the rejected request** is marked as needing re-authorization; a late failure from an old request cannot mark a freshly re-authorized credential broken. The old secret is not silently deleted before a new login succeeds.

## Model catalog and capability filtering

The single source of truth is `GET /v1/models` on the configured origin, read with the user's own API key so the result is the set of models that workspace can actually call. Model IDs keep their `vendor/model` namespace, and the model control is a **dropdown**, never a free-text field.

Each entry point filters independently, from catalog metadata rather than from the model name:

| Entry point | Rule |
| --- | --- |
| Text chat | `?capability=chat`, and `supported_endpoint_types` includes one of openai / anthropic / gemini / openai-response |
| Multimodal understanding | text chat, plus `architecture.input_modalities` **explicitly** contains the modality actually uploaded (image / audio / video / file) |
| Embeddings | `?capability=embedding`, or strictly matching the `embeddings` endpoint |
| Image generation | `?capability=image`, or strictly matching `image-generation` |
| Video generation | strictly matching `openai-video` |
| Rerank | strictly matching `jina-rerank` |

A model that does not declare a capability **fails closed** and is never mixed into that dropdown. Changing the capability, toggling an attachment modality or replacing the credential recomputes the options, and a previously selected model that is no longer compatible is cleared with a prompt rather than kept silently.

The API key never reaches the browser: the catalog is fetched server-side and only minimal model metadata (ID, name, context length, input modalities, reasoning support) is returned to the front end.

A successful live fetch is authoritative. If it fails (timeout, network error, unexpected shape) a small **verified fallback catalog** is used and the UI says so, rather than degrading to free text:

`openai/gpt-5.5`, `anthropic/claude-opus-4.8`, `google/gemini-3.5-flash`, `deepseek/deepseek-v4-pro`, `orcarouter/auto`

The fallback keeps its verified context length, input modalities and reasoning-effort ladder (`openai/gpt-5.5` carries low / medium / high / xhigh).

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `ORCA_BASE_URL` | none | shared origin for self-hosted deployments; fallback for both below |
| `ORCA_AUTH_BASE_URL` | `https://www.orcarouter.ai` | authentication and code exchange; explicit value wins |
| `ORCA_API_BASE_URL` | `https://api.orcarouter.ai/v1` | inference and model discovery; explicit value wins |

> Authentication lives on `www.orcarouter.ai` with its API under `/api/v1/auth`; the inference relay is `api.orcarouter.ai` under `/v1`.
> `https://api.orcarouter.ai/v1/auth/keys` is a 404 — these are two unrelated public origins and neither may be derived from the other.

Remote origins must use HTTPS; plain HTTP is permitted only for loopback development.

## Layout

```
src/common/orcarouter/
├─ __init__.py       provider IDs, display labels, console link
├─ errors.py         terminal, user-actionable error types
├─ origins.py        origin resolution and network policy
├─ pkce.py           PKCE primitives and the exchange contract
├─ credentials.py    the credential seam and its two adapters
├─ catalog.py        catalog parsing and capability filtering
├─ transport.py      Bearer transport for inference and discovery
├─ loopback.py       the Flow A callback listener
└─ runtime.py        the facade the page and entry points use
```

Neither inference nor discovery can tell which adapter produced the credential: both yield the same `OrcaCredential`.

## Tests

```bash
python -m pytest tests/ -q                      # unit and flow tests, no network, no real key
python -m pytest tests/ -q -m slow              # adds the Flow A loopback-socket tests
ORCA_E2E_BASE_URL=http://127.0.0.1:8090 python -m pytest tests/e2e -m e2e   # real-browser screenshots
```

`tests/test_orcarouter_flow.py` drives authorize → callback/paste → exchange → persist against a local fake auth server, using no real credential. A real authorization always requires a human to approve it in a browser.
