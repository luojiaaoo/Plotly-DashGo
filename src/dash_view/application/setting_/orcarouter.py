import feffery_antd_components as fac
from dash import dcc
from feffery_dash_utils.style_utils import style

from common.orcarouter import AUTH_METHOD_LABELS, AUTH_METHODS, CONSOLE_AUTHORIZED_APPS_URL
from common.utilities.util_logger import Log
from common.utilities.util_menu_access import MenuAccess
from dash_callback.application.setting_ import orcarouter_c
from dash_components import Card
from i18n import t__setting

# 二级菜单的标题、图标和显示顺序
title = 'OrcaRouter接口'
icon = None
logger = Log.get_logger(__name__)
order = 3
access_metas = ('OrcaRouter接口-页面',)

#: Catalog capabilities offered by the model selector, in the order they are shown.
_CAPABILITY_CHOICES = [
    ('chat', '文本对话'),
    ('multimodal', '多模态理解'),
    ('embedding', '向量嵌入'),
    ('image', '图片生成'),
    ('video', '视频生成'),
    ('rerank', '重排序'),
]

#: Non-text modalities an attachment can carry, per entry point.
_ATTACHMENT_CHOICES = [
    ('image', '图片'),
    ('audio', '音频'),
    ('video', '视频'),
    ('file', '文件'),
]


def render_method_card() -> fac.AntdCard:
    """The credential card: the two auth choices, side by side and clearly separate."""
    masked_key, connection_status = orcarouter_c.initial_credential_state()
    return Card(
        fac.AntdSpace(
            [
                fac.AntdAlert(
                    message=t__setting('OrcaRouter 凭据只保存在本机'),
                    description=t__setting('API Key 与账号授权两种方式都会得到一个由你的 OrcaRouter 账号计费、随时可撤销的 API Key，两者使用同一套推理接口与模型目录。'),
                    type='info',
                    showIcon=True,
                ),
                # ---- Choice 1: paste an existing key -------------------------------------
                fac.AntdDivider(
                    f'1. {t__setting(AUTH_METHOD_LABELS[AUTH_METHODS[0]])}',
                    innerTextOrientation='left',
                ),
                fac.AntdForm(
                    [
                        fac.AntdFormItem(
                            fac.AntdSpace(
                                [
                                    fac.AntdInput(
                                        id='orcarouter-api-key-input',
                                        mode='password',
                                        placeholder='sk-orca-…',
                                        style=style(width=360),
                                    ),
                                    fac.AntdButton(
                                        t__setting('保存'),
                                        id='orcarouter-api-key-save',
                                        type='primary',
                                    ),
                                    fac.AntdButton(
                                        t__setting('清除'),
                                        id='orcarouter-api-key-clear',
                                        danger=True,
                                    ),
                                ]
                            ),
                            label=t__setting('API Key'),
                        ),
                        fac.AntdFormItem(
                            fac.AntdSpace(
                                [
                                    fac.AntdText(masked_key, id='orcarouter-api-key-masked'),
                                    fac.AntdButton(
                                        t__setting('管理/撤销密钥'),
                                        id='orcarouter-api-key-dashboard',
                                        type='link',
                                        href=CONSOLE_AUTHORIZED_APPS_URL,
                                        target='_blank',
                                    ),
                                ]
                            ),
                            label=t__setting('当前密钥'),
                        ),
                    ],
                    labelCol={'span': 4},
                    wrapperCol={'span': 20},
                ),
                # ---- Choice 2: authorize with an account ---------------------------------
                fac.AntdDivider(
                    f'2. Connect with OrcaRouter ({t__setting(AUTH_METHOD_LABELS[AUTH_METHODS[1]])})',
                    innerTextOrientation='left',
                ),
                fac.AntdForm(
                    [
                        fac.AntdFormItem(
                            fac.AntdRadioGroup(
                                id='orcarouter-connect-flow',
                                options=[
                                    {'label': t__setting('粘贴授权码'), 'value': 'oob'},
                                    {'label': t__setting('浏览器自动回调'), 'value': 'loopback'},
                                ],
                                value='oob',
                                optionType='button',
                                buttonStyle='solid',
                            ),
                            label=t__setting('授权方式'),
                            tooltip=t__setting('自建部署地址不固定时使用粘贴授权码；浏览器与 DashGo 同机时可用自动回调'),
                        ),
                        fac.AntdFormItem(
                            fac.AntdSpace(
                                [
                                    fac.Fragment(id='orcarouter-connect-busy'),
                                    fac.AntdButton(
                                        'Connect with OrcaRouter',
                                        id='orcarouter-start-oauth-connect',
                                        type='primary',
                                        icon=fac.AntdIcon(icon='antd-link'),
                                    ),
                                    fac.AntdButton(
                                        t__setting('取消'),
                                        id='orcarouter-cancel-connect',
                                        disabled=True,
                                    ),
                                ]
                            ),
                            label='',
                        ),
                        # Everything below is the whole "login in progress" hint block. The
                        # pagehide handler empties it synchronously.
                        fac.Fragment(
                            fac.AntdSpace(
                                [
                                    fac.AntdText(t__setting('授权地址'), strong=True),
                                    fac.AntdSpace(
                                        [
                                            fac.AntdInput(
                                                id='orcarouter-authorize-url',
                                                readOnly=True,
                                                style=style(width=520),
                                            ),
                                            fac.AntdButton(
                                                t__setting('打开授权页面'),
                                                id='orcarouter-open-authorize-url',
                                                type='default',
                                                href='',
                                                target='_blank',
                                                disabled=True,
                                            ),
                                        ]
                                    ),
                                    fac.AntdSpace(
                                        [
                                            fac.AntdInput(
                                                id='orcarouter-auth-code-input',
                                                placeholder=t__setting('粘贴授权页面显示的授权码'),
                                                style=style(width=360),
                                            ),
                                            fac.AntdButton(
                                                t__setting('完成连接'),
                                                id='orcarouter-submit-auth-code',
                                                type='primary',
                                            ),
                                        ]
                                    ),
                                    fac.AntdText(id='orcarouter-oauth-status'),
                                ],
                                direction='vertical',
                                id='orcarouter-connect-hint',
                            ),
                            id='orcarouter-connect-hint-fragment',
                        ),
                        fac.AntdFormItem(
                            fac.AntdText(connection_status, id='orcarouter-connection-status'),
                            label=t__setting('连接状态'),
                        ),
                    ],
                    labelCol={'span': 4},
                    wrapperCol={'span': 20},
                ),
                dcc.Store(id='orcarouter-connect-state', data={}),
                dcc.Store(id='orcarouter-auth-revision', data=0),
                dcc.Store(id='orcarouter-client-state', data={'busy': False, 'hint': '', 'generation': 0}),
                dcc.Store(id='orcarouter-pagehide-signal', data=0),
                fac.Fragment(id='orcarouter-pagehide-listener'),
            ],
            direction='vertical',
            style=style(width='100%'),
        ),
        title=t__setting('OrcaRouter 接入方式'),
    )


def render_model_card() -> fac.AntdCard:
    """The capability-filtered model selector, driven by the live catalog.

    The options are built here, at render time, the same way the other settings pages
    build their tabs: it means the selector is populated the moment the page opens, and
    ``refresh_model_options`` only has to run when a filter actually changes.
    """
    model_options, selector_options, selected, catalog_status = orcarouter_c.initial_model_state()
    return Card(
        fac.AntdSpace(
            [
                fac.AntdForm(
                    [
                        fac.AntdFormItem(
                            fac.AntdRadioGroup(
                                id='orcarouter-model-capability',
                                options=[{'label': t__setting(label), 'value': value} for value, label in _CAPABILITY_CHOICES],
                                value='chat',
                                optionType='button',
                                buttonStyle='solid',
                            ),
                            label=t__setting('能力'),
                        ),
                        fac.AntdFormItem(
                            fac.AntdCheckboxGroup(
                                id='orcarouter-attachment-modality',
                                options=[{'label': t__setting(label), 'value': value} for value, label in _ATTACHMENT_CHOICES],
                                value=[],
                            ),
                            label=t__setting('附件模态'),
                            tooltip=t__setting('只显示明确声明支持这些输入模态的模型；未声明的一律不显示'),
                        ),
                        fac.AntdFormItem(
                            fac.AntdSpace(
                                [
                                    fac.AntdSelect(
                                        id='orcarouter-model-select',
                                        options=selector_options,
                                        value=selected,
                                        placeholder=t__setting('请选择模型'),
                                        optionFilterProp='label',
                                        allowClear=True,
                                        style=style(width=360),
                                        listHeight=320,
                                        # The dropdown is portalled to <body>, so it is styled by
                                        # its own popup class in assets/custom.css rather than by
                                        # the page's className. Matching the trigger width keeps
                                        # the panel edge aligned with the selector.
                                        popupClassName='orcarouter-model-dropdown',
                                        popupMatchSelectWidth=True,
                                    ),
                                    fac.AntdButton(
                                        t__setting('刷新模型目录'),
                                        id='orcarouter-model-refresh',
                                        type='default',
                                        icon=fac.AntdIcon(icon='antd-sync'),
                                    ),
                                ]
                            ),
                            label=t__setting('模型'),
                        ),
                        fac.AntdFormItem(
                            fac.AntdText(catalog_status, id='orcarouter-model-status'),
                            label=t__setting('目录状态'),
                        ),
                        fac.AntdFormItem(
                            fac.AntdText(id='orcarouter-model-detail'),
                            label=t__setting('模型能力'),
                        ),
                    ],
                    labelCol={'span': 4},
                    wrapperCol={'span': 20},
                ),
                dcc.Store(id='orcarouter-model-options-store', data=model_options),
            ],
            direction='vertical',
            style=style(width='100%'),
        ),
        title=t__setting('模型目录'),
    )


def render_test_card() -> fac.AntdCard:
    """A real request through the provider adapter, using whatever credential is stored."""
    return Card(
        fac.AntdSpace(
            [
                fac.AntdText(
                    t__setting('使用当前凭据向下游推理接口发送一次真实请求，用于验证接线。'),
                ),
                fac.AntdInput(
                    id='orcarouter-test-prompt',
                    mode='text-area',
                    autoSize={'minRows': 3, 'maxRows': 6},
                    value='Reply with the single word: pong',
                    style=style(width=560),
                ),
                fac.AntdSpace(
                    [
                        fac.AntdButton(
                            t__setting('发送测试请求'),
                            id='orcarouter-send-test',
                            type='primary',
                        ),
                    ]
                ),
                fac.AntdText(id='orcarouter-test-result'),
            ],
            direction='vertical',
            style=style(width='100%'),
        ),
        title=t__setting('推理测试'),
    )


def render_content(menu_access: MenuAccess, **kwargs):
    return fac.AntdSpace(
        [
            render_method_card(),
            render_model_card(),
            render_test_card(),
        ],
        direction='vertical',
        style=style(width='100%'),
        # The dropdown is a portal rendered outside this subtree, so its skin is set on
        # the popup class itself. An opaque background and a real border are required so
        # the list stays readable over whatever is behind it.
        className={
            '.ant-select-dropdown': {
                'backgroundColor': '#ffffff',
                'border': '1px solid #d9d9d9',
                'borderRadius': '6px',
                'boxShadow': '0 3px 6px -4px rgba(0,0,0,0.12), 0 6px 16px 0 rgba(0,0,0,0.08)',
                'padding': '4px',
            },
            '.ant-select-item-option': {
                'borderRadius': '4px',
            },
        },
    )
