from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash_components import Card, Table
from database.sql_db.dao import dao_user
from dash_callback.application.access_ import group_mgmt_c  # noqa
from functools import partial
from i18n import translator

_ = partial(translator.t)


# 二级菜单的标题、图标和显示顺序
title = '团队管理'
icon = None
order = 4
access_metas = ('团队管理-页面',)
logger = Log.get_logger(__name__)


def render_content(menu_access: MenuAccess, **kwargs):
    from config.access_factory import AccessFactory

    logger.debug(f'用户：{menu_access.user_name}，访问：{__name__}，参数列表：{kwargs}，权限元：{menu_access.all_access_metas}')
    return fac.AntdCol(
        [
            fac.AntdRow(
                fac.AntdButton(
                    id='group-mgmt-button-add',
                    children=_('添加团队'),
                    type='primary',
                    icon=fac.AntdIcon(icon='antd-plus'),
                    style={'marginBottom': '10px'},
                )
            ),
            fac.AntdRow(
                [
                    Card(
                        Table(
                            id='group-mgmt-table',
                            columns=[
                                {'title': _('团队名称'), 'dataIndex': 'group_name'},
                                {'title': _('团队状态'), 'dataIndex': 'group_status', 'renderOptions': {'renderType': 'tags'}},
                                {'title': _('团队描述'), 'dataIndex': 'group_remark'},
                                {'title': _('更新时间'), 'dataIndex': 'update_datetime'},
                                {'title': _('更新人'), 'dataIndex': 'update_by'},
                                {'title': _('创建时间'), 'dataIndex': 'create_datetime'},
                                {'title': _('创建人'), 'dataIndex': 'create_by'},
                                {'title': _('操作'), 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}},
                            ],
                            data=[
                                {
                                    'key': i.group_name,
                                    **i.__dict__,
                                    'group_status': {'tag': '启用' if i.group_status else '停用', 'color': 'cyan' if i.group_status else 'volcano'},
                                    'operation': [
                                        {
                                            'content': _('编辑'),
                                            'type': 'primary',
                                            'custom': 'update:' + i.group_name,
                                        },
                                        {
                                            'content': _('删除'),
                                            'type': 'primary',
                                            'custom': 'delete:' + i.group_name,
                                            'danger': True,
                                        },
                                    ],
                                }
                                for i in dao_user.get_group_info(exclude_disabled=False)
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
                                                fac.AntdInput(id='group-mgmt-add-group-name', debounceWait=500),
                                                label=_('团队名'),
                                                id='group-mgmt-add-group-name-form',
                                                hasFeedback=True,
                                            ),
                                            fac.AntdFormItem(fac.AntdSwitch(id='group-mgmt-add-group-status'), label=_('团队状态'), required=True),
                                        ]
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='group-mgmt-add-group-remark', mode='text-area', autoSize={'minRows': 1, 'maxRows': 3}),
                                        label=_('团队描述'),
                                        labelCol={'flex': '1'},
                                        wrapperCol={'flex': '5'},
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdSelect(id='group-mgmt-add-group-roles', mode='multiple'), label=_('绑定角色'), labelCol={'flex': '1'}, wrapperCol={'flex': '5'}
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdSelect(id='group-mgmt-add-group-admin-users', mode='multiple'), label=_('管理员'), labelCol={'flex': '1'}, wrapperCol={'flex': '5'}
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdSelect(id='group-mgmt-add-group-users', mode='multiple'), label=_('成员'), labelCol={'flex': '1'}, wrapperCol={'flex': '5'}
                                    ),
                                ],
                                labelAlign='left',
                                className={'.ant-form-item': {'marginBottom': '12px', 'marginRight': '8px'}},
                            )
                        ],
                        destroyOnClose=False,
                        renderFooter=True,
                        okText=_('确定'),
                        cancelText=_('取消'),
                        title=_('添加团队'),
                        mask=False,
                        maskClosable=False,
                        id='group-mgmt-add-modal',
                        style={'boxSizing': 'border-box'},
                    ),
                    fac.AntdModal(
                        children=[
                            fac.AntdText(_('您确定要删除团队')),
                            fac.AntdText(
                                id='group-mgmt-delete-group-name',
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
                        id='group-mgmt-delete-affirm-modal',
                    ),
                    fac.AntdModal(
                        children=[
                            fac.AntdForm(
                                [
                                    fac.AntdFlex(
                                        [
                                            fac.AntdFormItem(fac.AntdText(id='group-mgmt-update-group-name'), label=_('团队名')),
                                            fac.AntdFormItem(fac.AntdSwitch(id='group-mgmt-update-group-status'), label=_('团队状态'), required=True),
                                        ]
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='group-mgmt-update-group-remark', mode='text-area', autoSize={'minRows': 1, 'maxRows': 3}),
                                        label=_('团队描述'),
                                        labelCol={'flex': '1'},
                                        wrapperCol={'flex': '5'},
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdSelect(id='group-mgmt-update-group-roles', mode='multiple'), label=_('绑定角色'), labelCol={'flex': '1'}, wrapperCol={'flex': '5'}
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdSelect(id='group-mgmt-update-group-admin-users', mode='multiple'),
                                        label=_('管理员'),
                                        labelCol={'flex': '1'},
                                        wrapperCol={'flex': '5'},
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdSelect(id='group-mgmt-update-group-users', mode='multiple'), label=_('成员'), labelCol={'flex': '1'}, wrapperCol={'flex': '5'}
                                    ),
                                ],
                                labelAlign='left',
                                className={'.ant-form-item': {'marginBottom': '12px', 'marginRight': '8px'}},
                            )
                        ],
                        destroyOnClose=False,
                        renderFooter=True,
                        okText=_('确定'),
                        cancelText=_('取消'),
                        title=_('更新团队'),
                        mask=False,
                        maskClosable=False,
                        id='group-mgmt-update-modal',
                        style={'boxSizing': 'border-box'},
                    ),
                ],
            ),
        ],
    )
