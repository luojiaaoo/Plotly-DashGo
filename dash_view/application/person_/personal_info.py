from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html
from dash_components import Card
from dash import dcc
from database.sql_db.dao import dao_user
import dash_callback.application.person_.personal_info_c  # noqa
from functools import partial
from i18n import translator

_ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
title = '个人信息'
icon = None
logger = Log.get_logger(__name__)
order = 1
access_metas = ('个人信息-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    access_metas: List[str] = menu_access.all_access_metas
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
                        _('个人信息'),
                        innerTextOrientation='center',
                        fontStyle='oblique',
                        lineColor='#808080',
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('用户：')),
                            fac.AntdText(user_info.user_name, className='user_info_value'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('全名：')),
                            fac.AntdInput(value=user_info.user_full_name, className='user_info_value', variant='borderless', readOnly=True),
                            fac.AntdButton(fac.AntdIcon(icon='antd-edit'), type='link'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('状态：')),
                            fac.AntdText(_('启用' if user_info.user_status else '停用'), className='user_info_value'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('性别：')),
                            fac.AntdText(_(user_info.user_sex), className='user_info_value'),
                            fac.AntdButton(fac.AntdIcon(icon='antd-edit'), type='link'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('邮箱：')),
                            fac.AntdText(user_info.user_email, className='user_info_value'),
                            fac.AntdButton(fac.AntdIcon(icon='antd-edit'), type='link'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('电话：')),
                            fac.AntdText(user_info.phone_number, className='user_info_value'),
                            fac.AntdButton(fac.AntdIcon(icon='antd-edit'), type='link'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('描述：')),
                            fac.AntdText(user_info.user_remark),
                            fac.AntdButton(fac.AntdIcon(icon='antd-edit'), type='link'),
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
                    '& .user_info_value': {
                        'word-break': 'keep-all',
                    },
                },
            ),
            Card(
                className={
                    'flex': 'auto',
                    'marginLeft': '8px',
                },
            ),
        ],
        style={'display': 'flex'},
    )
