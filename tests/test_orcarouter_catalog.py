"""Model discovery and capability filtering.

Fixtures cover every capability the entry points use: text-only chat, image-input
chat, embedding, image generation, video and rerank.
"""

import json

import pytest

from common.orcarouter.catalog import (
    CAPABILITY_CHAT,
    CAPABILITY_EMBEDDING,
    CAPABILITY_IMAGE,
    CAPABILITY_RERANK,
    CAPABILITY_VIDEO,
    VERIFIED_FALLBACK_CATALOG,
    build_model_option,
    fallback_catalog,
    filter_models,
    list_model_options,
    parse_catalog,
)
from common.orcarouter.credentials import OrcaCredential
from common.orcarouter.errors import CatalogError, NeedsReauthError

# --------------------------------------------------------------------------------------
# Fixtures: one record per capability shape the catalog actually serves
# --------------------------------------------------------------------------------------

TEXT_ONLY = {
    'id': 'deepseek/deepseek-v4-pro',
    'name': 'DeepSeek V4 Pro',
    'supported_endpoint_types': ['openai', 'openai-response'],
    'architecture': {'input_modalities': ['text']},
    'context_length': 1048576,
}
IMAGE_CHAT = {
    'id': 'anthropic/claude-opus-4.8',
    'name': 'Claude Opus 4.8',
    'supported_endpoint_types': ['openai', 'anthropic'],
    'architecture': {'input_modalities': ['text', 'image', 'file']},
    'context_length': 1000000,
}
AUDIO_CHAT = {
    'id': 'google/gemini-3.5-flash',
    'name': 'Gemini 3.5 Flash',
    'supported_endpoint_types': ['openai', 'gemini'],
    'architecture': {'input_modalities': ['text', 'image', 'audio', 'video']},
}
UNDECLARED = {
    'id': 'mystery/model-x',
    'name': 'Mystery',
    'supported_endpoint_types': ['openai'],
    'architecture': {},  # declares nothing
}
EMBEDDING = {
    'id': 'openai/text-embedding-3-large',
    'supported_endpoint_types': ['embeddings'],
    'architecture': {'input_modalities': ['text']},
}
IMAGE_GEN = {
    'id': 'openai/gpt-image-1',
    'supported_endpoint_types': ['image-generation'],
    'architecture': {'input_modalities': ['text']},
}
VIDEO_GEN = {
    'id': 'openai/sora-2',
    'supported_endpoint_types': ['openai-video'],
    'architecture': {'input_modalities': ['text']},
}
RERANK = {
    'id': 'jina/jina-reranker-v2',
    'supported_endpoint_types': ['jina-rerank'],
    'architecture': {'input_modalities': ['text']},
}
ALL = [TEXT_ONLY, IMAGE_CHAT, AUDIO_CHAT, UNDECLARED, EMBEDDING, IMAGE_GEN, VIDEO_GEN, RERANK]


def ids(options):
    return [option['value'] for option in options]


# --------------------------------------------------------------------------------------
# Chat
# --------------------------------------------------------------------------------------


def test_chat_filter_keeps_text_capable_models_and_drops_non_text_endpoints():
    selected = ids(filter_models(ALL, CAPABILITY_CHAT))
    assert 'deepseek/deepseek-v4-pro' in selected
    assert 'anthropic/claude-opus-4.8' in selected
    for excluded in ('openai/gpt-image-1', 'openai/sora-2', 'jina/jina-reranker-v2'):
        assert excluded not in selected


def test_a_model_with_no_supported_endpoint_types_is_not_advertised_as_chat():
    selected = ids(filter_models([{'id': 'weird/model', 'architecture': {}}], CAPABILITY_CHAT))
    assert selected == []


def test_a_record_offering_only_a_non_text_route_is_never_a_chat_model():
    both = {
        'id': 'hybrid/model',
        'supported_endpoint_types': ['image-generation', 'openai'],
        'architecture': {'input_modalities': ['text']},
    }
    only_image = {'id': 'image/model', 'supported_endpoint_types': ['image-generation']}
    assert ids(filter_models([both, only_image], CAPABILITY_CHAT)) == ['hybrid/model']


# --------------------------------------------------------------------------------------
# Multimodal fail-closed
# --------------------------------------------------------------------------------------


def test_image_attachment_keeps_only_models_declaring_image_input():
    selected = ids(filter_models(ALL, CAPABILITY_CHAT, required_modalities=['image']))
    assert 'anthropic/claude-opus-4.8' in selected
    assert 'google/gemini-3.5-flash' in selected
    assert 'deepseek/deepseek-v4-pro' not in selected, 'text-only must be filtered out'


def test_undeclared_modality_fails_closed():
    """A model that does not declare image input is excluded, not assumed compatible."""
    assert ids(filter_models([UNDECLARED], CAPABILITY_CHAT, required_modalities=['image'])) == []
    assert ids(filter_models([UNDECLARED], CAPABILITY_CHAT)) == ['mystery/model-x']


def test_audio_attachment_filters_to_models_that_declare_audio():
    assert ids(filter_models(ALL, CAPABILITY_CHAT, required_modalities=['audio'])) == ['google/gemini-3.5-flash']


def test_video_attachment_filters_to_models_that_declare_video():
    assert ids(filter_models(ALL, CAPABILITY_CHAT, required_modalities=['video'])) == ['google/gemini-3.5-flash']


def test_text_is_never_treated_as_a_required_attachment_modality():
    """Selecting "text" must not silently narrow the list."""
    assert len(filter_models(ALL, CAPABILITY_CHAT, required_modalities=['text'])) == len(filter_models(ALL, CAPABILITY_CHAT))


# --------------------------------------------------------------------------------------
# Other capabilities
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    'capability,expected',
    [
        (CAPABILITY_EMBEDDING, ['openai/text-embedding-3-large']),
        (CAPABILITY_IMAGE, ['openai/gpt-image-1']),
        (CAPABILITY_VIDEO, ['openai/sora-2']),
        (CAPABILITY_RERANK, ['jina/jina-reranker-v2']),
    ],
)
def test_each_capability_selects_only_its_own_endpoint_type(capability, expected):
    assert ids(filter_models(ALL, capability)) == expected


def test_unknown_capability_is_refused():
    with pytest.raises(ValueError):
        filter_models(ALL, 'telepathy')


# --------------------------------------------------------------------------------------
# Metadata preservation
# --------------------------------------------------------------------------------------


def test_option_keeps_the_vendor_namespace_and_capability_metadata():
    option = build_model_option(IMAGE_CHAT, CAPABILITY_CHAT, ['image'])
    assert option['model_id'] == 'anthropic/claude-opus-4.8'  # namespace untouched
    assert option['input_modalities'] == ['text', 'image', 'file']
    assert option['context_length'] == 1000000
    assert option['capability'] == 'chat'
    assert 'anthropic' in option['supported_endpoint_types']


def test_option_never_carries_a_credential_field():
    option = build_model_option(IMAGE_CHAT, CAPABILITY_CHAT, [])
    credential_fields = {'api_key', 'key', 'token', 'secret', 'authorization', 'code_verifier'}
    assert credential_fields.isdisjoint(set(option.keys()))


def test_verified_fallback_preserves_gpt_5_5_reasoning_ladder():
    """Adding live discovery must not erase a verified model's effort ladder."""
    gpt = next(record for record in VERIFIED_FALLBACK_CATALOG if record['id'] == 'openai/gpt-5.5')
    assert gpt['reasoning'] is True
    assert set(gpt['reasoning_efforts']) == {'low', 'medium', 'high', 'xhigh'}
    assert 'image' in gpt['architecture']['input_modalities']


def test_fallback_catalog_is_a_copy_not_the_shared_constant():
    first = fallback_catalog()
    first[0]['id'] = 'mutated'
    assert VERIFIED_FALLBACK_CATALOG[0]['id'] == 'openai/gpt-5.5'


def test_fallback_catalog_covers_every_documented_seed_model():
    assert {record['id'] for record in VERIFIED_FALLBACK_CATALOG} == {
        'openai/gpt-5.5',
        'anthropic/claude-opus-4.8',
        'google/gemini-3.5-flash',
        'deepseek/deepseek-v4-pro',
        'orcarouter/auto',
    }


# --------------------------------------------------------------------------------------
# Response parsing / bounds
# --------------------------------------------------------------------------------------


def test_parse_accepts_the_documented_envelope():
    assert parse_catalog({'data': [TEXT_ONLY]}) == [TEXT_ONLY]
    assert parse_catalog([TEXT_ONLY]) == [TEXT_ONLY]


def test_parse_rejects_an_unexpected_shape():
    with pytest.raises(CatalogError):
        parse_catalog({'models': []})
    with pytest.raises(CatalogError):
        parse_catalog('nope')


def test_parse_rejects_a_catalog_larger_than_the_bound():
    with pytest.raises(CatalogError):
        parse_catalog({'data': [{'id': f'm/{i}'} for i in range(2001)]})


# --------------------------------------------------------------------------------------
# Live discovery vs verified fallback
# --------------------------------------------------------------------------------------


def _credential():
    return OrcaCredential(
        api_key='sk-orca-' + 'a' * 32,
        auth_method='orcarouter',
        auth_base='https://www.orcarouter.ai',
        api_base='https://api.orcarouter.ai/v1',
    )


def test_live_discovery_is_authoritative_and_not_mixed_with_the_seed(monkeypatch):
    live = [TEXT_ONLY]
    monkeypatch.setattr('common.orcarouter.transport.fetch_models', lambda *a, **k: live)
    options, degraded = list_model_options(_credential(), capability=CAPABILITY_CHAT)
    assert degraded is False
    assert ids(options) == ['deepseek/deepseek-v4-pro']
    # No seed model leaked in alongside the authoritative live result.
    assert 'openai/gpt-5.5' not in ids(options)


def test_discovery_failure_falls_back_to_the_verified_seed_and_is_marked_degraded(monkeypatch):
    def boom(*args, **kwargs):
        raise CatalogError('offline')

    monkeypatch.setattr('common.orcarouter.transport.fetch_models', boom)
    options, degraded = list_model_options(_credential(), capability=CAPABILITY_CHAT)
    assert degraded is True
    assert 'openai/gpt-5.5' in ids(options)
    # Reasoning metadata survives the degraded path.
    gpt = next(option for option in options if option['value'] == 'openai/gpt-5.5')
    assert set(gpt['reasoning_efforts']) == {'low', 'medium', 'high', 'xhigh'}


def test_degraded_multimodal_filter_still_fails_closed(monkeypatch):
    monkeypatch.setattr(
        'common.orcarouter.transport.fetch_models',
        lambda *a, **k: (_ for _ in ()).throw(CatalogError('offline')),
    )
    options, degraded = list_model_options(_credential(), capability=CAPABILITY_CHAT, required_modalities=['audio'])
    assert degraded is True
    # Only the seed model that actually declares audio input survives.
    assert ids(options) == ['google/gemini-3.5-flash']


def test_revoked_credential_raises_instead_of_degrading_to_the_seed(monkeypatch):
    """A revoked key is terminal; it must not be hidden behind a fallback catalog."""
    from common.orcarouter import runtime

    runtime.set_store(None)
    from common.orcarouter.credentials import InMemoryCredentialStore

    store = InMemoryCredentialStore()
    store.save('orcarouter', 'sk-orca-' + 'a' * 32)
    store.mark_needs_reauth('orcarouter', 1)
    runtime.set_store(store)

    with pytest.raises(NeedsReauthError):
        runtime.discover_model_options(capability=CAPABILITY_CHAT)


def test_discover_returns_nothing_without_a_credential():
    from common.orcarouter import runtime

    runtime.set_store(None)
    from common.orcarouter.credentials import InMemoryCredentialStore

    runtime.set_store(InMemoryCredentialStore())
    options, degraded = runtime.discover_model_options(capability=CAPABILITY_CHAT)
    assert options == [] and degraded is False


def test_transport_uses_the_capability_query_parameter(monkeypatch):
    seen = {}

    class Response:
        status_code = 200
        content = json.dumps({'data': [TEXT_ONLY]}).encode()

        class raw:
            @staticmethod
            def read(*args, **kwargs):
                return json.dumps({'data': [TEXT_ONLY]}).encode()

    class Session:
        def get(self, url, **kwargs):
            seen['url'] = url
            return Response()

    from common.orcarouter.transport import fetch_models

    fetch_models(_credential(), capability=CAPABILITY_CHAT, session=Session())
    assert seen['url'] == 'https://api.orcarouter.ai/v1/models?capability=chat'


# --------------------------------------------------------------------------------------
# Status handling
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize('status', [200, 201, 204])
def test_success_statuses_are_not_treated_as_failures(status):
    """A 2xx must never be mapped onto an error; only 4xx/5xx are failures."""
    from common.orcarouter.transport import _raise_for_status

    _raise_for_status(status, _credential())  # must not raise


@pytest.mark.parametrize('status', [400, 401, 403, 404, 429, 500, 503])
def test_failure_statuses_raise(status):
    from common.orcarouter.errors import OrcaRouterError
    from common.orcarouter.transport import _raise_for_status

    with pytest.raises(OrcaRouterError):
        _raise_for_status(status, _credential())


def test_a_successful_completion_is_returned_verbatim():
    """The end-to-end shape of a completion must survive the status handling."""

    from common.orcarouter.transport import chat_completion

    body = {'choices': [{'message': {'role': 'assistant', 'content': 'pong'}}], 'usage': {'total_tokens': 3}}

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return body

    class Session:
        def post(self, url, **kwargs):
            assert url == 'https://api.orcarouter.ai/v1/chat/completions'
            assert kwargs['headers']['Authorization'].startswith('Bearer sk-orca-')
            return Response()

    assert chat_completion(_credential(), model='openai/gpt-5.5', messages=[], session=Session()) == body


def test_a_401_from_inference_is_terminal_not_a_catalog_fallback():
    from common.orcarouter.errors import NeedsReauthError
    from common.orcarouter.transport import chat_completion

    class Response:
        status_code = 401

    class Session:
        def post(self, url, **kwargs):
            return Response()

    with pytest.raises(NeedsReauthError):
        chat_completion(_credential(), model='openai/gpt-5.5', messages=[], session=Session())
