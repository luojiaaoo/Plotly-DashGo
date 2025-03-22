from dash import html
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style


def render(e: str = None):
    """渲染500状态页面"""

    if e is None:
        e = Exception("500状态页演示示例错误")

    return fac.AntdCenter(
        fac.AntdResult(
            # 自定义状态图片
            icon=html.Img(
                src="/assets/imgs/status/500.svg",
                style=style(height="50vh", pointerEvents="none"),
            ),
            title=fac.AntdText("系统内部错误", style=style(fontSize=20)),
            subTitle="错误信息：" + str(e),
            extra=fac.AntdButton("返回首页", type="primary", href="/", target="_self"),
        ),
        style={"height": "calc(60vh + 100px)"},
    )
