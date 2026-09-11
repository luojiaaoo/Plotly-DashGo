"""Live model discovery and capability filtering.

The single source of truth for what a user can select is
``GET {api_base}/models`` on the *inference* origin, read with the user's own
OrcaRouter API key so the result is the set of models that workspace can actually
call. Model IDs keep their ``vendor/model`` namespace untouched.

Capability rules are applied to catalog metadata only — never to the model name:

===========================  ==========================================================
entry point                  requirement
===========================  ==========================================================
text chat / agent            ``?capability=chat`` and ``supported_endpoint_types``
                             intersects the text route set
multimodal understanding     the above, plus ``architecture.input_modalities``
                             explicitly contains the modality being uploaded
embedding                    ``?capability=embedding``
image generation             ``?capability=image``
video generation             ``openai-video`` endpoint type
rerank                       ``jina-rerank`` endpoint type
===========================  ==========================================================

A model that does not *declare* a capability is excluded from that capability
(fail closed). When live discovery fails, the verified seed below is used and
reported as degraded; it is never mixed into a successful live result.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from .errors import CatalogError

#: Route types the text chat completions adapter can speak.
TEXT_ENDPOINT_TYPES = frozenset({'openai', 'anthropic', 'gemini', 'openai-response'})

#: Endpoint types that are structurally not text chat, whatever the name suggests.
NON_TEXT_ENDPOINT_TYPES = frozenset({'image-generation', 'openai-video', 'jina-rerank'})

#: Capability selector for each entry point.
CAPABILITY_CHAT = 'chat'
CAPABILITY_EMBEDDING = 'embedding'
CAPABILITY_IMAGE = 'image'
CAPABILITY_VIDEO = 'video'
CAPABILITY_RERANK = 'rerank'

#: Discovery limits so a catalog response cannot consume unbounded memory or
#: advertise routes this client cannot speak.
CATALOG_TIMEOUT_SECONDS = 10
CATALOG_MAX_BYTES = 4 * 1024 * 1024
CATALOG_MAX_ITEMS = 2000

#: Reasoning-effort ladder carried by the verified seed. Live records that advertise
#: reasoning keep the ladder they were verified with instead of silently losing it.
_VERIFIED_EFFORTS = ('low', 'medium', 'high', 'xhigh')

#: Small, verified cold-start catalog. Used only when live discovery fails, and shown
#: as degraded. Sources: GET https://api.orcarouter.ai/v1/models (verified 2026-09-11).
VERIFIED_FALLBACK_CATALOG: tuple[dict[str, Any], ...] = (
    {
        'id': 'openai/gpt-5.5',
        'name': 'OpenAI: GPT-5.5',
        'context_length': 1000000,
        'max_completion_tokens': 128000,
        'supported_endpoint_types': ['openai', 'openai-response'],
        'architecture': {'input_modalities': ['text', 'image', 'file'], 'output_modalities': ['text']},
        'reasoning': True,
        'reasoning_efforts': list(_VERIFIED_EFFORTS),
    },
    {
        'id': 'anthropic/claude-opus-4.8',
        'name': 'Anthropic: Claude Opus 4.8',
        'context_length': 1000000,
        'max_completion_tokens': 128000,
        'supported_endpoint_types': ['openai', 'anthropic', 'openai-response'],
        'architecture': {'input_modalities': ['text', 'image', 'file'], 'output_modalities': ['text']},
        'reasoning': True,
        'reasoning_efforts': list(_VERIFIED_EFFORTS),
    },
    {
        'id': 'google/gemini-3.5-flash',
        'name': 'Gemini 3.5 Flash',
        'context_length': 1048576,
        'max_completion_tokens': 65536,
        'supported_endpoint_types': ['openai', 'gemini'],
        'architecture': {'input_modalities': ['text', 'image', 'video', 'file', 'audio'], 'output_modalities': ['text']},
        'reasoning': True,
        'reasoning_efforts': list(_VERIFIED_EFFORTS),
    },
    {
        'id': 'deepseek/deepseek-v4-pro',
        'name': 'DeepSeek: DeepSeek V4 Pro',
        'context_length': 1048576,
        'max_completion_tokens': 384000,
        'supported_endpoint_types': ['openai', 'openai-response'],
        'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']},
        'reasoning': True,
        'reasoning_efforts': list(_VERIFIED_EFFORTS),
    },
    {
        'id': 'orcarouter/auto',
        'name': 'OrcaRouter Auto',
        'context_length': 200000,
        'max_completion_tokens': None,
        'supported_endpoint_types': ['openai', 'openai-response', 'anthropic', 'gemini'],
        'architecture': {'input_modalities': ['text'], 'output_modalities': ['text'], 'auto_routed': True},
        'reasoning': False,
        'reasoning_efforts': [],
    },
)


class ModelOption(dict):
    """A model catalog record with its capability analysis attached.

    A plain ``dict`` so it serialises straight into Dash component props, and so the
    Dash layer never has to import this module's filtering internals.
    """

    @property
    def id(self) -> str:
        return self['value']


def _modalities(record: dict) -> list[str]:
    architecture = record.get('architecture') or {}
    if not isinstance(architecture, dict):
        return []
    modalities = architecture.get('input_modalities') or []
    return [str(m).lower() for m in modalities] if isinstance(modalities, list) else []


def _endpoint_types(record: dict) -> set[str]:
    types = record.get('supported_endpoint_types') or []
    return {str(t).lower() for t in types} if isinstance(types, list) else []


def is_text_chat(record: dict) -> bool:
    """True when a record is usable for text chat by the OpenAI-compatible adapter.

    ``supported_endpoint_types`` must *declare* at least one text route. A record that
    declares nothing is not advertised as a chat model: the catalog is the only source
    of capability truth, and a missing declaration is not a claim of support.
    """
    if not record.get('id'):
        return False
    endpoints = _endpoint_types(record)
    return bool(endpoints & TEXT_ENDPOINT_TYPES)


def supports_input_modality(record: dict, modality: str) -> bool:
    """Fail closed: an undeclared modality is not supported."""
    return modality.lower() in _modalities(record)


def filter_models(records: Iterable[dict], capability: str, *, required_modalities: Iterable[str] = ()) -> list[ModelOption]:
    """Return the records usable for ``capability``, in catalog order.

    ``required_modalities`` is what the *calling entry point* actually uploads: those
    modalities must be explicitly declared, or the model is dropped.
    """
    required = [m.lower() for m in required_modalities if m and str(m).lower() != 'text']
    selected: list[ModelOption] = []

    for record in records:
        if not isinstance(record, dict) or not record.get('id'):
            continue
        endpoints = _endpoint_types(record)

        if capability == CAPABILITY_CHAT:
            if not is_text_chat(record):
                continue
            if required and not all(supports_input_modality(record, m) for m in required):
                continue
        elif capability == CAPABILITY_EMBEDDING:
            if 'embeddings' not in endpoints:
                continue
        elif capability == CAPABILITY_IMAGE:
            if 'image-generation' not in endpoints:
                continue
        elif capability == CAPABILITY_VIDEO:
            if 'openai-video' not in endpoints:
                continue
        elif capability == CAPABILITY_RERANK:
            if 'jina-rerank' not in endpoints:
                continue
        else:
            raise ValueError(f'unknown capability {capability!r}')

        selected.append(build_model_option(record, capability, required))

    return selected


def build_model_option(record: dict, capability: str, required: list[str]) -> ModelOption:
    """Reduce a catalog record to the minimal metadata the UI needs.

    Only these fields ever reach the browser: the API key is never part of a model
    record, and the raw catalog payload is dropped rather than forwarded.
    """
    option: ModelOption = ModelOption(
        {
            'value': record['id'],
            'label': record.get('name') or record['id'],
            'model_id': record['id'],
            'capability': capability,
            'supported_endpoint_types': sorted(_endpoint_types(record)),
            'input_modalities': _modalities(record),
            'context_length': record.get('context_length'),
            'max_completion_tokens': record.get('max_completion_tokens'),
            'reasoning': bool(record.get('reasoning')),
            'reasoning_efforts': list(record.get('reasoning_efforts') or []),
        }
    )
    return option


def parse_catalog(payload: Any) -> list[dict]:
    """Accept only the documented ``{"data": [...]}`` shape, bounded in size."""
    records = payload.get('data') if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise CatalogError('Model catalog response had an unexpected shape')
    if len(records) > CATALOG_MAX_ITEMS:
        raise CatalogError(f'Model catalog advertised more than {CATALOG_MAX_ITEMS} models')
    return [r for r in records if isinstance(r, dict)]


def fallback_catalog() -> list[dict]:
    """The verified seed, as fresh copies so callers cannot mutate the constant."""
    return [json.loads(json.dumps(record)) for record in VERIFIED_FALLBACK_CATALOG]


def list_model_options(
    credential,
    *,
    capability: str = CAPABILITY_CHAT,
    required_modalities: Iterable[str] = (),
    session=None,
) -> tuple[list[ModelOption], bool]:
    """Discover models and filter them for one entry point.

    Returns ``(options, degraded)``. ``degraded`` is true only when live discovery
    failed and the verified seed is being shown, so the UI can say so.
    """
    from .transport import fetch_models

    try:
        records = fetch_models(credential, capability=capability, session=session)
    except CatalogError:
        return filter_models(fallback_catalog(), capability, required_modalities=required_modalities), True
    return filter_models(records, capability, required_modalities=required_modalities), False
