from common.utilities.util_menu_access import MenuAccess
from typing import List
from dash_components import Card
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from functools import partial
from i18n import translator

__ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
title = '工作台'
icon = None
order = 1
logger = Log.get_logger(__name__)

access_metas = ('工作台-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return Card(
        fac.AntdSpace(
            [
                fac.AntdAvatar(
                    id='workbench-avatar',
                    mode='image',
                    src=f'/avatar/{menu_access.user_info.user_name}',
                    alt=menu_access.user_info.user_full_name,
                    size=70,
                    style={'marginRight': '20px'}
                ),
                fac.AntdText(__('你好，')),
                fac.AntdText(menu_access.user_info.user_full_name,id='workbench-user-full-name'),
            ]
        )
    )
