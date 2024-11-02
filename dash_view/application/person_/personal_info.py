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
def get_title():
    return _('个人信息')


icon = None
logger = Log.get_logger(__name__)
order = 1
access_metas = ('个人信息-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    access_metas: List[str] = menu_access.all_access_metas
    user_info = dao_user.get_user_info(menu_access.user_name)
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
                            fac.AntdText(_('用户：'), className='user_info_name'),
                            fac.AntdText(user_info.user_name, className='user_info_value'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('全名：'), className='user_info_name'),
                            fac.AntdText(user_info.user_full_name, className='user_info_value'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('状态：'), className='user_info_name'),
                            fac.AntdText(_(user_info.status), className='user_info_value'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('性别：'), className='user_info_name'),
                            fac.AntdText(_(user_info.sex), className='user_info_value'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('团队：'), className='user_info_name'),
                            fac.AntdText('/'.join(user_info.groups), className='user_info_value'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('类型：'), className='user_info_name'),
                            fac.AntdText(_(user_info.user_type), className='user_info_value'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('邮箱：'), className='user_info_name'),
                            fac.AntdText(user_info.email, className='user_info_value'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('电话：'), className='user_info_name'),
                            fac.AntdText(user_info.phone_number, className='user_info_value'),
                        ]
                    ),
                    fac.AntdSpace(
                        [
                            fac.AntdText(_('说明：'), className='user_info_name'),
                            fac.AntdText(user_info.remark),
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
                    '& .user_info_name': {
                        'word-break': 'keep-all',
                        'font-weight': 'bold',
                        'display': 'block',
                        'width': '6em',
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
