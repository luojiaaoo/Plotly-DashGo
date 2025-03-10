import feffery_antd_components as fac
import feffery_utils_components as fuc
from dash import dcc, html
from server import app
from dash.dependencies import Input, Output

app.clientside_callback(
    """
    (okCounts) => {
        if (okCounts>0) {
            return true;
        }
    }
    """,
    Output('global-reload', 'reload'),
    Input('global-token-err-modal', 'okCounts'),
)


def render_func_content():
    return [
        #
        ############################################
        #           地 址 栏 功 能 组 件            #
        ############################################
        # 全局url监听组件，仅仅起到监听的作用
        fuc.FefferyLocation(id='global-url-location'),
        # 用于回调更新地址栏URL信息，不刷新页面
        dcc.Location(id='global-dcc-url', refresh=False),
        # 全局重定向组件容器，返回dcc.Location组件，重定向到新页面
        fac.Fragment(id='global-redirect-container'),
        #
        ############################################
        #              消 息 组 件                  #
        ############################################
        # 注入全局消息提示容器
        fac.Fragment(id='global-message-container'),
        # 注入全局通知信息容器
        fac.Fragment(id='global-notification-container'),
        #
        #################################################################
        # 标 签 页 的 缓 存 组 件 ， 减 少 没 必 要 的 主 路 由 回 调 执 行 #
        #################################################################
        # URL中继组件，用于保存最后一次新建的标签页的URL，如果在已打开的标签页之间切换，不触发路由回调
        dcc.Store(id='global-url-relay'),
        # 保存打开过的标签页的面包屑、展开key、选中key作为缓存
        dcc.Store(id='global-opened-tab-pathname-infos', data={}),
        #
        #################################################################
        #    在 打 开 工 作 页 之 后 ， 自 动 加 载 上 次 访 问 地 址      #
        #################################################################
        # 当标签页重载时，如访问页面不是首页，保存访问地址
        dcc.Store(id='global-url-last-when-load'),
        # 触发进入目标页面上面Store保存的访问地址的超时组件
        fuc.FefferyTimeout(id='global-url-timeout-last-when-load'),
        #
        ############################################
        #             功 能 组 件                   #
        ############################################
        # 全局强制网页刷新组件
        fuc.FefferyReload(id='global-reload'),
        # 全局js执行
        fuc.FefferyExecuteJs(id='global-execute-js-output'),
        # 监听窗口大小
        fuc.FefferyWindowSize(id='global-window-size'),
        #
        ############################################
        #         预 置 退 出 登 录 模 态 框         #
        ############################################
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
            id='global-token-err-modal',
            visible=False,
            maskClosable=False,
            closable=False,
            title='系统提示',
            okText='重新登录',
            renderFooter=True,
            centered=True,
            cancelButtonProps={'style': {'display': 'none'}},
        ),
    ]
