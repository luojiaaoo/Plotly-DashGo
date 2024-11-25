from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash_components import Card, Table
from database.sql_db.dao import dao_user
from dash_callback.application.access_ import role_mgmt_c  # noqa
from i18n import t__access, t__default

# 二级菜单的标题、图标和显示顺序
title = '角色管理'
icon = None
logger = Log.get_logger(__name__)
order = 1

access_metas = ('角色管理-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    from config.access_factory import AccessFactory

    return fac.AntdCol(
        [
            fac.AntdRow(
                fac.AntdButton(
                    id='role-mgmt-button-add',
                    children=t__access('添加角色'),
                    type='primary',
                    icon=fac.AntdIcon(icon='antd-plus'),
                    style={'marginBottom': '10px'},
                )
            ),
            fac.AntdRow(
                [
                    Card(
                        Table(
                            id='role-mgmt-table',
                            columns=[
                                {'title': t__access('角色名称'), 'dataIndex': 'role_name'},
                                {'title': t__access('角色状态'), 'dataIndex': 'role_status', 'renderOptions': {'renderType': 'tags'}},
                                {'title': t__access('角色描述'), 'dataIndex': 'role_remark'},
                                {'title': t__access('更新时间'), 'dataIndex': 'update_datetime'},
                                {'title': t__access('更新人'), 'dataIndex': 'update_by'},
                                {'title': t__access('创建时间'), 'dataIndex': 'create_datetime'},
                                {'title': t__access('创建人'), 'dataIndex': 'create_by'},
                                {'title': t__default('操作'), 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}},
                            ],
                            data=[
                                {
                                    'key': i.role_name,
                                    **i.__dict__,
                                    'role_status': {'tag': t__default('启用' if i['user_status'] else '停用'), 'color': 'cyan' if i.role_status else 'volcano'},
                                    'operation': [
                                        {
                                            'content': t__default('编辑'),
                                            'type': 'primary',
                                            'custom': 'update:' + i.role_name,
                                        },
                                        *(
                                            [
                                                {
                                                    'content': t__default('删除'),
                                                    'type': 'primary',
                                                    'custom': 'delete:' + i.role_name,
                                                    'danger': True,
                                                }
                                            ]
                                            if i.role_name != 'admin'
                                            else []
                                        ),
                                    ],
                                }
                                for i in dao_user.get_role_info(exclude_disabled=False)
                            ],
                            pageSize=10,
                        ),
                        style={'width': '100%'},
                    ),
                    fac.AntdModal(
                        children=[
                            fac.AntdForm(
                                [
                                    fac.AntdFormItem(fac.AntdText(id='role-mgmt-update-role-name'), label=t__access('角色名称')),
                                    fac.AntdFormItem(fac.AntdSwitch(id='role-mgmt-update-role-status'), label=t__access('角色状态')),
                                    fac.AntdFormItem(fac.AntdInput(id='role-mgmt-update-role-remark', mode='text-area'), label=t__access('角色描述')),
                                    fac.AntdFormItem(
                                        fac.AntdTree(
                                            id='role-menu-access-tree-select-update',
                                            treeData=MenuAccess.gen_antd_tree_data_menu_item_access_meta(AccessFactory.dict_access_meta2menu_item),
                                            multiple=True,
                                            checkable=True,
                                            showLine=True,
                                        ),
                                        label=t__access('菜单权限'),
                                    ),
                                ],
                                labelCol={'span': 5},
                                wrapperCol={'span': 19},
                            )
                        ],
                        destroyOnClose=False,
                        renderFooter=True,
                        okText=t__default('确定'),
                        cancelText=t__default('取消'),
                        title=t__access('角色编辑'),
                        mask=False,
                        maskClosable=False,
                        id='role-mgmt-update-modal',
                    ),
                    fac.AntdModal(
                        children=[
                            fac.AntdForm(
                                [
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='role-mgmt-add-role-name', debounceWait=500),
                                        label=t__access('角色名称'),
                                        required=True,
                                        id='role-mgmt-add-role-name-form',
                                        hasFeedback=True,
                                    ),
                                    fac.AntdFormItem(fac.AntdSwitch(id='role-mgmt-add-role-status', checked=True), label=t__access('角色状态'), required=True),
                                    fac.AntdFormItem(fac.AntdInput(id='role-mgmt-add-role-remark', mode='text-area', autoSize={'minRows': 1, 'maxRows': 3}), label=t__access('角色描述')),
                                    fac.AntdFormItem(
                                        fac.AntdTree(
                                            id='role-menu-access-tree-select-add',
                                            treeData=MenuAccess.gen_antd_tree_data_menu_item_access_meta(AccessFactory.dict_access_meta2menu_item),
                                            multiple=True,
                                            checkable=True,
                                            showLine=True,
                                        ),
                                        label=t__access('菜单权限'),
                                    ),
                                ],
                                labelCol={'span': 5},
                                wrapperCol={'span': 19},
                            )
                        ],
                        destroyOnClose=False,
                        renderFooter=True,
                        okText=t__default('确定'),
                        cancelText=t__default('取消'),
                        title=t__access('添加角色'),
                        mask=False,
                        maskClosable=False,
                        id='role-mgmt-add-modal',
                    ),
                    fac.AntdModal(
                        children=[
                            fac.AntdText(t__access('您确定要删除角色 ')),
                            fac.AntdText(
                                id='role-mgmt-delete-role-name',
                                type='danger',
                                underline=True,
                            ),
                            fac.AntdText('?'),
                        ],
                        destroyOnClose=False,
                        renderFooter=True,
                        okText=t__default('确定'),
                        cancelText=t__default('取消'),
                        okButtonProps={'danger': True},
                        title=t__default('确认要删除？'),
                        mask=False,
                        maskClosable=False,
                        id='role-mgmt-delete-affirm-modal',
                    ),
                ],
            ),
        ],
    )
