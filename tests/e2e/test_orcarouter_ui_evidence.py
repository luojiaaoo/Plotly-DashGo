"""Real-browser end-to-end evidence for the OrcaRouter provider page.

Run against a live DashGo instance with an OrcaRouter credential already stored through
the project's own save path (``common.orcarouter.runtime.save_api_key``), so the browser
never receives the API key: the page is only ever handed masked metadata and a model
list the server produced.

    ORCA_E2E_BASE_URL=http://127.0.0.1:8090 python -m pytest tests/e2e -m e2e

Produces the three screenshots required by the contribution checklist plus a
``manifest.json`` describing them.
"""

import hashlib
import json
import os
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

BASE_URL = os.environ.get('ORCA_E2E_BASE_URL', 'http://127.0.0.1:8090')
EVIDENCE_DIR = Path(os.environ.get('ORCA_EVIDENCE_DIR', '/work/evidence'))
CHROMIUM = os.environ.get('ORCA_CHROMIUM', '/usr/bin/chromium')

CATALOG_URL = 'https://api.orcarouter.ai/v1/models?capability=chat'


def _catalog_counts():
    """The authoritative catalog, read server-side with the user's own key."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'src'))
    from common.orcarouter import runtime
    from common.orcarouter.catalog import CAPABILITY_CHAT

    runtime.set_store(None)
    all_chat, degraded = runtime.discover_model_options(capability=CAPABILITY_CHAT)
    image_chat, _ = runtime.discover_model_options(capability=CAPABILITY_CHAT, required_modalities=['image'])
    assert degraded is False, 'this test requires live discovery to succeed'
    return all_chat, image_chat


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture(scope='module')
def page():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=CHROMIUM,
            args=['--no-sandbox', '--disable-dev-shm-usage'],
        )
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()
        _login(page)
        yield page
        browser.close()


def _login(page):
    page.goto(f'{BASE_URL}/login', wait_until='networkidle', timeout=60000)
    page.fill('#login-username', 'admin')
    page.fill('#login-password', 'admin123')
    page.click('#login-submit')
    page.wait_for_timeout(4000)


def _open_provider_page(page):
    page.goto(f'{BASE_URL}/setting_/orcarouter', wait_until='networkidle', timeout=60000)
    page.wait_for_selector('#orcarouter-start-oauth-connect', timeout=30000)
    # Wait for the catalog callback to populate the selector.
    page.wait_for_function(
        "() => { const s = document.querySelector('#orcarouter-model-select'); return s && s.closest('.ant-select'); }",
        timeout=30000,
    )
    page.wait_for_timeout(6000)


def _open_dropdown(page):
    page.click('#orcarouter-model-select')
    page.wait_for_selector('.ant-select-dropdown', state='visible', timeout=15000)
    page.wait_for_timeout(800)


def _collect_dropdown_option_ids(page):
    """Read every option the selector offers, scrolling the virtualised list.

    Ant Design renders only a window of options at a time, so counting the nodes
    currently in the DOM would under-report. Walking the list to the end and
    collecting distinct titles is what makes the count a real measurement.

    Returns ``{model_id: title}``, parsed from the ``Label (vendor/model)`` shape the
    selector renders, so the comparison against the catalog is exact rather than a
    substring match.
    """
    page.evaluate(
        """() => {
            const holder = document.querySelector('.ant-select-dropdown .rc-virtual-list-holder');
            if (holder) { holder.scrollTop = 0; }
        }"""
    )
    page.wait_for_timeout(300)
    titles = set()
    for _ in range(80):
        titles.update(
            page.evaluate(
                """() => [...document.querySelectorAll('.ant-select-dropdown .ant-select-item-option')].map(
                    (node) => node.getAttribute('title') || node.textContent.trim())"""
            )
        )
        before = len(titles)
        advanced = page.evaluate(
            """() => {
                const holder = document.querySelector('.ant-select-dropdown .rc-virtual-list-holder');
                if (!holder) { return false; }
                const previous = holder.scrollTop;
                holder.scrollTop = previous + holder.clientHeight * 0.8;
                return holder.scrollTop > previous;
            }"""
        )
        page.wait_for_timeout(120)
        if not advanced and len(titles) == before:
            break

    found = {}
    for title in titles:
        match = re.search(r'\(([^()]+)\)\s*$', title)
        if match:
            found[match.group(1)] = title
    return found


def _reset_dropdown_scroll(page):
    page.evaluate(
        """() => {
            const holder = document.querySelector('.ant-select-dropdown .rc-virtual-list-holder');
            if (holder) { holder.scrollTop = 0; }
        }"""
    )
    page.wait_for_timeout(300)


def _selected_model(page):
    """The model currently shown in the selector, or '' when nothing is selected.

    A single-select Ant Design dropdown renders its selection in
    ``.ant-select-selection-item``; the inner search input's ``value`` stays empty.
    """
    return page.evaluate(
        """() => {
            const trigger = document.querySelector('#orcarouter-model-select').closest('.ant-select');
            const item = trigger.querySelector('.ant-select-selection-item');
            if (!item) { return ''; }
            const title = item.getAttribute('title') || item.textContent || '';
            const match = title.match(/\\(([^()]+)\\)\\s*$/);
            return match ? match[1] : title.trim();
        }"""
    )


def _dropdown_metrics(page, trigger_selector='#orcarouter-model-select'):
    return page.evaluate(
        """(sel) => {
            const trigger = document.querySelector(sel).closest('.ant-select');
            const panel = document.querySelector('.ant-select-dropdown');
            const listbox = panel.querySelector('[role="listbox"]');
            const cs = getComputedStyle(panel);
            const t = trigger.getBoundingClientRect();
            const p = panel.getBoundingClientRect();
            const bg = cs.backgroundColor;
            const m = bg.match(/rgba?\\(([^)]+)\\)/);
            const alpha = m && m[1].split(',').length === 4 ? parseFloat(m[1].split(',')[3]) : 1;
            return {
                listbox_present: !!listbox,
                aria_expanded: trigger.querySelector('[aria-expanded]')?.getAttribute('aria-expanded'),
                panel_width: Math.round(p.width),
                trigger_panel_right_delta: Math.round(Math.abs(p.right - t.right)),
                trigger_panel_left_delta: Math.round(Math.abs(p.left - t.left)),
                opaque_background: alpha === 1 && bg !== 'rgba(0, 0, 0, 0)',
                visible_border: cs.borderTopWidth !== '0px' && cs.borderTopStyle !== 'none',
                border_width: cs.borderTopWidth,
                background: bg,
            };
        }""",
        trigger_selector,
    )


def test_orcarouter_provider_evidence(page):
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    all_chat, image_chat = _catalog_counts()
    expected_all = {option['value'] for option in all_chat}
    expected_image = {option['value'] for option in image_chat}
    assert expected_image < expected_all, 'the image filter must be a strict subset'

    _open_provider_page(page)

    # ---------------------------------------------------------------- auth methods
    key_input = page.locator('#orcarouter-api-key-input')
    assert key_input.count() == 1, 'the API-key entry must be present'

    # The key field must be masked: never a plain text input.
    input_type = key_input.get_attribute('type')
    assert input_type == 'password', f'the API key input must be a password field, got {input_type!r}'
    assert key_input.is_editable(), 'the API key field must be interactive'

    connect = page.locator('#orcarouter-start-oauth-connect')
    assert connect.is_visible() and connect.is_enabled(), 'the PKCE connect entry must be usable'
    assert 'OrcaRouter' in connect.inner_text()

    # Only test data goes in the field; the real credential lives server-side.
    key_input.fill('sk-orca-PLACEHOLDER-TEST-DATA')
    page.wait_for_timeout(300)

    masked = page.locator('#orcarouter-api-key-masked').inner_text()
    assert masked and 'sk-orca-' in masked, 'the stored credential must be shown masked'
    assert 'PLACEHOLDER-TEST-DATA' not in masked
    assert os.environ.get('ORCAROUTER_API_KEY', 'unset') not in page.content(), 'the real key is in the DOM'

    # Clear the field again so the screenshot carries no credential-shaped string.
    key_input.fill('')
    page.wait_for_timeout(300)

    page.screenshot(path=str(EVIDENCE_DIR / 'auth-methods.png'))
    auth_metrics = {
        'api_key_visible': True,
        'pkce_visible': True,
        'secret_masked': input_type == 'password',
        'controls_enabled': connect.is_enabled(),
    }

    # ------------------------------------------------------- text model dropdown
    _open_dropdown(page)
    metrics = _dropdown_metrics(page)
    rendered = _collect_dropdown_option_ids(page)
    assert metrics['listbox_present'], 'the dropdown must expose role=listbox'
    assert metrics['aria_expanded'] == 'true'
    assert set(rendered) == expected_all, (
        f'selector offered {len(rendered)} models, catalog has {len(expected_all)}; '
        f'missing={sorted(expected_all - set(rendered))[:5]} extra={sorted(set(rendered) - expected_all)[:5]}'
    )
    assert metrics['opaque_background'], f'dropdown background is not opaque: {metrics["background"]}'
    assert metrics['visible_border'], f'dropdown has no visible border: {metrics["border_width"]}'
    assert metrics['trigger_panel_right_delta'] <= 2, f'panel right edge is {metrics["trigger_panel_right_delta"]}px from the trigger'
    # Every rendered option came from the live catalog, so the options really are the API's.
    page.screenshot(path=str(EVIDENCE_DIR / 'text-model-dropdown.png'))
    text_metrics = {
        'dropdown_open': True,
        'item_count': len(rendered),
        'panel_width': metrics['panel_width'],
        'trigger_panel_right_delta': metrics['trigger_panel_right_delta'],
        'opaque_background': metrics['opaque_background'],
        'visible_border': metrics['visible_border'],
    }

    # Pick a text-only model, so the incompatible-clearing rule can be observed.
    text_only = next(option['value'] for option in all_chat if 'image' not in (option.get('input_modalities') or []))
    _reset_dropdown_scroll(page)
    page.locator(f'.ant-select-item-option[title="{rendered[text_only]}"]').first.click()
    page.wait_for_timeout(1500)
    page.keyboard.press('Escape')
    page.wait_for_timeout(500)
    assert _selected_model(page) == text_only, 'the chosen model should be the current selection before the attachment is added'

    # -------------------------------------------------- multimodal model dropdown
    # Attach an image: the selector must now offer only models declaring image input.
    page.locator('#orcarouter-attachment-modality').get_by_text('图片', exact=True).click()
    page.wait_for_timeout(5000)

    _open_dropdown(page)
    metrics = _dropdown_metrics(page)
    rendered = _collect_dropdown_option_ids(page)
    assert set(rendered) == expected_image, f'multimodal selector offered {len(rendered)} models, catalog has {len(expected_image)}'
    assert len(rendered) < len(expected_all)
    assert metrics['trigger_panel_right_delta'] <= 2
    assert metrics['opaque_background'] and metrics['visible_border']
    page.screenshot(path=str(EVIDENCE_DIR / 'multimodal-model-dropdown.png'))
    multimodal_metrics = {
        'dropdown_open': True,
        'item_count': len(rendered),
        'panel_width': metrics['panel_width'],
        'trigger_panel_right_delta': metrics['trigger_panel_right_delta'],
        'opaque_background': metrics['opaque_background'],
        'visible_border': metrics['visible_border'],
    }

    # The previously selected text-only model is no longer in the list and was cleared.
    assert text_only not in expected_image
    page.keyboard.press('Escape')
    page.wait_for_timeout(500)
    assert _selected_model(page) == '', 'an incompatible selection must be cleared, not kept silently'

    manifest = {
        'automation': {
            'framework': 'playwright',
            'test_command': 'ORCA_E2E_BASE_URL=$BASE_URL python -m pytest tests/e2e -m e2e',
            'passed': True,
            'catalog_source': CATALOG_URL,
            'catalog_model_count': len(expected_all),
            'image_model_count': len(expected_image),
        },
        'artifacts': [
            {
                'kind': 'auth-methods',
                'path': str(EVIDENCE_DIR / 'auth-methods.png'),
                'sha256': _sha256(EVIDENCE_DIR / 'auth-methods.png'),
                'ui': auth_metrics,
            },
            {
                'kind': 'text-model-dropdown',
                'path': str(EVIDENCE_DIR / 'text-model-dropdown.png'),
                'sha256': _sha256(EVIDENCE_DIR / 'text-model-dropdown.png'),
                'ui': text_metrics,
            },
            {
                'kind': 'multimodal-model-dropdown',
                'path': str(EVIDENCE_DIR / 'multimodal-model-dropdown.png'),
                'sha256': _sha256(EVIDENCE_DIR / 'multimodal-model-dropdown.png'),
                'ui': multimodal_metrics,
            },
        ],
    }
    (EVIDENCE_DIR / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
