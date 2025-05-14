import feffery_antd_components as fac
import feffery_utils_components as fuc
from dash import dcc, html


def render():
    return [
        #
        # >>>>> 地址组件，缓存已打开的标签页的面包屑、展开key、选中key，避免无效回调
        # 地址栏控制组件
        dcc.Location(id='main-dcc-url', refresh=False),
        # 地址栏监听组件
        fuc.FefferyLocation(id='main-url-location'),
        # URL中继组件，用于保存最后一次新建的标签页的URL，如果在已打开的标签页之间切换，不触发路由回调
        dcc.Store(id='main-url-relay'),
        # 保存打开过的标签页的面包屑、展开key、选中key作为缓存
        dcc.Store(id='main-opened-tab-pathname-infos', data={}),
        #
        # >>>>> 当初始化load页面时，访问的页面不为主页，主动加载主页，然后跳转目标页
        # 当标签页重载时，如访问页面不是首页，保存访问地址
        dcc.Store(id='main-url-pathname-last-when-load'),
        dcc.Store(id='main-url-search-last-when-load'),
        dcc.Store(id='main-url-hash-last-when-load'),
        # 触发进入目标页面上面Store保存的访问地址的超时组件
        fuc.FefferyTimeout(id='main-url-timeout-last-when-load'),
        #
        # >>>>> 功能组件
        # 监听窗口大小
        fuc.FefferyWindowSize(id='main-window-size'),
        # 退出登录提示弹窗
        fac.AntdModal(
            html.Div(
                [
                    fac.AntdIcon(icon='fc-high-priority', style={'fontSize': '28px'}),
                    fac.AntdText(
                        '登录状态已过期/无效，请重新登录',
                        style={'marginLeft': '5px'},
                    ),
                ]
            ),
            id='main-token-err-modal',
            visible=False,
            maskClosable=False,
            closable=False,
            title='系统提示',
            okText='重新登录',
            renderFooter=True,
            centered=True,
            cancelButtonProps={'style': {'display': 'none'}},
        ),
        #
        # >> 多页面交互缓存
        dcc.Store(id='main-task-mgmt-jump-to-task-log-job-id-store'),
    ]
