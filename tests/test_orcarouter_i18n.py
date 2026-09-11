"""Localization: every shipped locale resolves the new provider strings.

The project ships two locales — ``zh-cn`` (the root locale) and ``en-us`` — across a
root catalog plus one catalog per topic. A key added to only one of them silently
falls back forever, so parity is asserted directly.
"""

import json
import re
from pathlib import Path

TRANSLATIONS = Path(__file__).resolve().parent.parent / 'src' / 'translations'
SETTING_TOPIC = TRANSLATIONS / 'topic_locales' / 'setting.json'

#: The topic catalog the OrcaRouter provider page reads through.
NEW_PROVIDER_FILES = (
    Path(__file__).resolve().parent.parent / 'src' / 'dash_view' / 'application' / 'setting_' / 'orcarouter.py',
    Path(__file__).resolve().parent.parent / 'src' / 'dash_callback' / 'application' / 'setting_' / 'orcarouter_c.py',
)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def test_setting_catalog_has_both_shipped_locales():
    catalog = load(SETTING_TOPIC)
    assert catalog['root_locale'] == 'zh-cn'
    missing = [key for key, value in catalog['contents'].items() if 'en-us' not in value]
    assert missing == [], f'keys without an en-us translation: {missing}'


def test_every_literal_used_by_the_provider_page_has_a_catalog_entry():
    """No hardcoded English/Chinese label may bypass the i18n catalog."""
    catalog = load(SETTING_TOPIC)
    literals = set()
    for path in NEW_PROVIDER_FILES:
        source = path.read_text(encoding='utf-8')
        literals |= set(re.findall(r"t__setting\(\s*'([^']+)'", source))
        literals |= set(re.findall(r't__setting\(\s*\"([^\"]+)\"', source))

    unmapped = sorted(literal for literal in literals if literal not in catalog['contents'])
    assert unmapped == [], f'provider strings missing from setting.json: {unmapped}'


def test_both_authentication_method_labels_are_localized():
    """The two auth choices are the tenant of this PR; both must resolve in both locales."""
    from common.orcarouter import AUTH_METHOD_LABELS, AUTH_METHODS

    catalog = load(SETTING_TOPIC)
    assert len(AUTH_METHODS) == 2
    for method in AUTH_METHODS:
        label = AUTH_METHOD_LABELS[method]
        assert label in catalog['contents'], f'{label} is not in the setting catalog'
        assert catalog['contents'][label]['en-us']


def test_provider_page_capabilities_are_all_localized():
    catalog = load(SETTING_TOPIC)
    for label in ('文本对话', '多模态理解', '向量嵌入', '图片生成', '视频生成', '重排序'):
        assert label in catalog['contents'], f'{label} is missing from the setting catalog'
        assert catalog['contents'][label]['en-us']


def test_attachment_modalities_are_all_localized():
    catalog = load(SETTING_TOPIC)
    for label in ('图片', '音频', '视频', '文件'):
        assert label in catalog['contents']


def test_the_provider_page_is_reachable_in_the_menu_registry():
    """A provider nobody can open is not integrated."""
    import app  # noqa: F401  - builds the layout and validates the access metas
    from config.access_factory import AccessFactory

    assert 'OrcaRouter接口-页面' in AccessFactory.get_dict_access_meta2menu_item()
    assert 'OrcaRouter接口-页面' in AccessFactory.admin_access_meta


def test_localized_strings_resolve_through_the_real_translator():
    """The catalog is loaded by the project's own translator, not just by json.load."""
    import app
    from i18n import t__setting

    with app.app.server.test_request_context('/'):
        assert t__setting('文本对话') in ('文本对话', 'Text chat')
        assert t__setting('OrcaRouter - API') == 'OrcaRouter - API'
