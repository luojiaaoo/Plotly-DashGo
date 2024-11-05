from common.utilities.util_menu_access import MenuAccess
from typing import List
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html
from dash import dcc
from dash_components import Card, Table
from database.sql_db.dao import dao_user
import dash_callback.application.access_.user_mgmt_c  # noqa
from functools import partial
from i18n import translator

_ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
def get_title():
    return _('用户管理')


icon = None
logger = Log.get_logger(__name__)
order = 3

access_metas = ('用户管理-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    logger.debug(f'用户：{menu_access.user_name}，访问：{__name__}，参数列表：{kwargs}，权限元：{access_metas}')
    return fac.AntdCol(
        [
            fac.AntdRow(
                fac.AntdButton(
                    id='user-mgmt-button-add',
                    children=_('添加用户'),
                    type='primary',
                    icon=fac.AntdIcon(icon='antd-plus'),
                    style={'marginBottom': '10px'},
                )
            ),
            fac.AntdRow(
                [
                    Card(
                        Table(
                            id='user-mgmt-table',
                            columns=[
                                {'title': _('用户名'), 'dataIndex': 'user_name'},
                                {'title': _('全名'), 'dataIndex': 'user_full_name'},
                                {'title': _('用户状态'), 'dataIndex': 'user_status', 'renderOptions': {'renderType': 'tags'}},
                                {'title': _('用户描述'), 'dataIndex': 'user_remark'},
                                {'title': _('性别'), 'dataIndex': 'user_sex'},
                                {'title': _('邮箱'), 'dataIndex': 'user_email'},
                                {'title': _('电话号码'), 'dataIndex': 'phone_number'},
                                {'title': _('更新时间'), 'dataIndex': 'update_datetime'},
                                {'title': _('更新人'), 'dataIndex': 'update_by'},
                                {'title': _('创建时间'), 'dataIndex': 'create_datetime'},
                                {'title': _('创建人'), 'dataIndex': 'create_by'},
                                {'title': _('操作'), 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}},
                            ],
                            data=[
                                {
                                    'key': i.user_name,
                                    **i.__dict__,
                                    'user_status': {'tag': dao_user.get_status_str(i.user_status), 'color': 'cyan' if i.user_status else 'volcano'},
                                    'operation': [
                                        {
                                            'content': _('编辑'),
                                            'type': 'primary',
                                            'custom': 'update:' + i.user_name,
                                        },
                                        {
                                            'content': _('删除'),
                                            'type': 'primary',
                                            'custom': 'delete:' + i.user_name,
                                            'danger': True,
                                        },
                                    ],
                                }
                                for i in dao_user.get_user_info()
                            ],
                            pageSize=10,
                        ),
                        style={'width': '100%'},
                    ),
                    fac.AntdModal(
                        children=[
                            fac.AntdForm(
                                [
                                    fac.AntdFlex(
                                        [
                                            fac.AntdFormItem(
                                                fac.AntdInput(id='user-mgmt-add-user-name', debounceWait=500),
                                                label=_('用户名'),
                                                id='user-mgmt-add-user-name-form',
                                                hasFeedback=True,
                                            ),
                                            fac.AntdFormItem(fac.AntdInput(id='user-mgmt-add-user-full-name'), label=_('全名')),
                                        ]
                                    ),
                                    fac.AntdFlex(
                                        [
                                            fac.AntdFormItem(fac.AntdInput(id='user-mgmt-add-user-email'), label=_('邮箱')),
                                            fac.AntdFormItem(fac.AntdInput(id='user-mgmt-add-phone-number'), label=_('电话号码')),
                                        ]
                                    ),
                                    fac.AntdFlex(
                                        [
                                            fac.AntdFormItem(fac.AntdSwitch(id='user-mgmt-add-user-status'), label=_('用户状态'), style={'flex': 1}),
                                            fac.AntdFormItem(
                                                fac.AntdSelect(
                                                    id='user-mgmt-add-user-sex',
                                                    options=[
                                                        {'label': _('男'), 'value': '男'},
                                                        {'label': _('女'), 'value': '女'},
                                                        {'label': _('未知'), 'value': '未知'},
                                                    ],
                                                    defaultValue='男',
                                                    allowClear=False,
                                                ),
                                                label=_('性别'),
                                                style={'flex': 1},
                                            ),
                                            fac.AntdFormItem(fac.AntdInput(id='user-mgmt-add-password'), label=_('密码'), style={'flex': 2}),
                                        ]
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='user-mgmt-add-user-remark', mode='text-area'), label=_('用户描述'), labelCol={'flex': '1'}, wrapperCol={'flex': '5'}
                                    ),
                                    fac.AntdFormItem(fac.AntdSelect(id='user-mgmt-add-roles'), label=_('角色'), labelCol={'flex': '1'}, wrapperCol={'flex': '5'}),
                                    fac.AntdFormItem(fac.AntdSelect(id='user-mgmt-add-groups'), label=_('团队'), labelCol={'flex': '1'}, wrapperCol={'flex': '5'}),
                                    fac.AntdFormItem(fac.AntdSelect(id='user-mgmt-add-admin-groups'), label=_('管理团队'), labelCol={'flex': '1'}, wrapperCol={'flex': '5'}),
                                ],
                                labelAlign='left',
                                className={'.ant-form-item': {'marginBottom': '12px', 'marginRight': '8px'}},
                            )
                        ],
                        destroyOnClose=False,
                        renderFooter=True,
                        okText=_('确定'),
                        cancelText=_('取消'),
                        title=_('添加用户'),
                        mask=False,
                        maskClosable=False,
                        id='user-mgmt-add-modal',
                        style={'boxSizing': 'border-box'},
                    ),
                    fac.AntdModal(
                        children=[
                            fac.AntdText(_('您确定要删除用户')),
                            fac.AntdText(
                                'xxxx',
                                id='user-mgmt-delete-user-name',
                                type='danger',
                                underline=True,
                            ),
                            fac.AntdText('?'),
                        ],
                        destroyOnClose=False,
                        renderFooter=True,
                        okText=_('确定'),
                        cancelText=_('取消'),
                        okButtonProps={'danger': True},
                        title=_('确认要删除？'),
                        mask=False,
                        maskClosable=False,
                        id='user-mgmt-delete-affirm-modal',
                    ),
                ],
            ),
        ],
    )
