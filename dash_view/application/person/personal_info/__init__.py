from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash import html
from dash_components import ShadowDiv
from database.sql_db.dao import user
from common.utilities.util_path import get_avatar_path
from flask_babel import gettext as _  # noqa


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('个人信息')


icon = None
logger = Log.get_logger(__name__)
order = 1


def render_content(menu_access: MenuAccess, **kwargs):
    access_metas: List[str] = menu_access.get_access_metas(__name__)
    user_info = user.get_user_info(menu_access.user_name)
    return html.Div(
        [
            ShadowDiv(
                children=[
                    fac.AntdCenter(
                        fac.AntdButton(
                            fac.AntdAvatar(
                                id='global-head-avatar',
                                mode='image',
                                shape='square',
                                src=get_avatar_path(menu_access.user_name),
                                alt=menu_access.user_info.user_full_name,
                                size=120,
                            ),
                            id='global-head-avatar-botton',
                            type='text',
                            shape='circle',
                            style={
                                'height': '120px',
                                'width': '120px',
                                'marginBottom': '10px',
                            },
                        )
                    ),
                    fac.AntdDivider(
                        _('个人信息'),
                        innerTextOrientation='left',
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
                    'display': 'flex',
                    'flexDirection': 'column',
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
            ShadowDiv(
                className={
                    'flex': 'auto',
                    'marginLeft': '8px',
                },
            ),
        ],
        style={'display': 'flex'},
    )
