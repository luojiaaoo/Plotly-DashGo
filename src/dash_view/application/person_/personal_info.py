from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html
from dash_components import Card
from dash import dcc
from database.sql_db.dao import dao_user
from config.enums import Sex
import dash_callback.application.person_.personal_info_c  # noqa
from i18n import t__person, t__default, t__access


# 二级菜单的标题、图标和显示顺序
title = '个人信息'
icon = None
logger = Log.get_logger(__name__)
order = 1
access_metas = ('个人信息-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    user_info = dao_user.get_user_info([menu_access.user_name], exclude_disabled=True)[0]
    return html.Div(
        [
            Card(
                children=[
                    fac.AntdCenter(
                        dcc.Upload(
                            fac.AntdButton(
                                [
                                    fac.AntdAvatar(
                                        id='personal-info-avatar',
                                        mode='image',
                                        src=f'/avatar/{menu_access.user_info.user_name}',
                                        alt=menu_access.user_info.user_full_name,
                                        size=120,
                                        className={
                                            'position': 'absolute',
                                        },
                                    ),
                                    fuc.FefferyDiv(
                                        fac.AntdIcon(icon='antd-edit', style={'fontSize': '25px'}),
                                        className={
                                            'fontWight': 'bold',
                                            'color': '#f0f0f0',
                                            'width': '100%',
                                            'height': '100%',
                                            'position': 'absolute',
                                            'display': 'flex',
                                            'justify-content': 'center',
                                            'align-items': 'center',
                                            'zIndex': 999,
                                            'background': 'rgba(0, 0, 0, 0.3)',
                                            'opacity': 0,
                                            'transition': 'opacity 0.5s ease-in-out',
                                            'borderRadius': '50%',
                                            '&:hover': {
                                                'opacity': 1,
                                            },
                                        },
                                    ),
                                ],
                                type='text',
                                shape='circle',
                                style={
                                    'height': '120px',
                                    'width': '120px',
                                    'marginBottom': '10px',
                                    'position': 'relative',
                                },
                            ),
                            id='personal-info-avatar-upload-choose',
                            accept='.jpeg,.jpg,.png',
                            max_size=10 * 1024 * 1024,
                        ),
                    ),
                    fac.AntdDivider(
                        t__person('个人信息'),
                        innerTextOrientation='center',
                        fontStyle='oblique',
                        lineColor='#808080',
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(t__person('用户：')),
                            fac.AntdText(user_info.user_name),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(t__person('全名：')),
                            fac.AntdInput(defaultValue=user_info.user_full_name, variant='borderless', readOnly=True, id='personal-info-user-full-name'),
                            fac.AntdButton(fac.AntdIcon(icon='antd-edit'), type='link', id='personal-info-user-full-name-edit'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(t__person('状态：')),
                            fac.AntdText(t__default('启用' if user_info.user_status else '停用')),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(t__person('性别：')),
                            fac.AntdSelect(
                                options=[{'label': t__access(i.value), 'value': i.value} for i in Sex],
                                defaultValue=user_info.user_sex,
                                value=user_info.user_sex,
                                variant='borderless',
                                id='personal-info-user-sex',
                                allowClear=False,
                            ),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(t__person('邮箱：')),
                            fac.AntdInput(defaultValue=user_info.user_email, variant='borderless', readOnly=True, id='personal-info-user-email'),
                            fac.AntdButton(fac.AntdIcon(icon='antd-edit'), type='link', id='personal-info-user-email-edit'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(t__person('电话：')),
                            fac.AntdInput(defaultValue=user_info.phone_number, variant='borderless', readOnly=True, id='personal-info-phone-number'),
                            fac.AntdButton(fac.AntdIcon(icon='antd-edit'), type='link', id='personal-info-phone-number-edit'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(t__person('描述：')),
                            fac.AntdInput(defaultValue=user_info.user_remark, variant='borderless', readOnly=True, id='personal-info-user-remark'),
                            fac.AntdButton(fac.AntdIcon(icon='antd-edit'), type='link', id='personal-info-user-remark-edit'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(t__person('密码：')),
                            fac.AntdButton(t__person('修改密码'), type='link', id='personal-info-password-edit', style={'width': '0px'}),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(t__person('动态码：')),
                            fac.AntdPopconfirm(
                                fac.AntdButton(t__person('绑定动态码'), type='link'), title='如已绑定，再次绑定会导致之前的认证码失效，请确认', id='personal-info-show-otp-modal'
                            ),
                        ]
                    ),
                ],
                className={
                    'flex': 'None',
                    'min-width': '15em',
                    '& .ant-card-body': {
                        'display': 'flex',
                        'flexDirection': 'column',
                    },
                    '& .ant-space > :nth-child(1) > :first-child': {
                        'word-break': 'keep-all',
                        'font-weight': 'bold',
                        'display': 'block',
                        'width': '6em',
                    },
                    '& .ant-space > :nth-child(2) > :first-child': {
                        'display': 'block',
                        'padding': '3px 11px',
                        'width': '13em',
                    },
                    '& .ant-space > :nth-child(2) > :first-child > :first-child': {
                        'padding': '0',
                    },
                    '& .user_info_value': {
                        'word-break': 'keep-all',
                    },
                },
            ),
            fac.AntdModal(
                children=[
                    fac.AntdForm(
                        [
                            fac.AntdFormItem(fac.AntdInput(id='personal-info-change-password-old', mode='password'), label=t__person('旧密码'), required=True),
                            fac.AntdFormItem(fac.AntdInput(id='personal-info-change-password-new', mode='password'), label=t__person('新密码'), required=True),
                            fac.AntdFormItem(fac.AntdInput(id='personal-info-change-password-new-again', mode='password'), label=t__person('确认密码'), required=True),
                        ],
                        className={'.ant-form-item': {'marginBottom': '12px', 'marginRight': '8px'}},
                    )
                ],
                destroyOnClose=False,
                renderFooter=True,
                okText=t__default('确定'),
                cancelText=t__default('取消'),
                title=t__person('修改密码'),
                id='personal-info-change-password-modal',
            ),
            fac.AntdModal(
                children=[
                    fac.AntdSpace(
                        [
                            fac.AntdFormItem(fac.AntdInput(id='personal-info-verify-password-for-rqcode', mode='password'), label=t__person('旧密码'), required=True),
                            fac.AntdButton(t__person('生成授权二维码'), type='primary', id='personal-info-otp-show-rqcode'),
                            html.Div(id='personal-info-otp-rqcode-container'),
                        ],
                        direction='vertical',
                    )
                ],
                visible=False,
                renderFooter=False,
                maskClosable=False,
                destroyOnClose=False,
                title=t__person('绑定动态码（生成后，之前的动态码失效）'),
                id='personal-info-otp-modal',
            ),
        ],
        style={'display': 'flex'},
    )
