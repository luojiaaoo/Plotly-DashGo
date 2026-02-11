from flask import request, redirect, send_from_directory, abort
from config.dashgo_conf import ShowConf, FlaskConf, CommonConf, PathProj
from loguru import logger
from common.exception import global_exception_handler
from common.utilities.util_dash import CustomDash
from common.constant import HttpStatusConstant
from typing import Optional, List
from i18n import t__other


# dash实例
app = CustomDash(
    __name__,
    suppress_callback_exceptions=True,
    compress=True,
    update_title=None,
    serve_locally=CommonConf.DASH_SERVE_LOCALLY,
    extra_hot_reload_paths=[],
    on_error=global_exception_handler,
)
app.server.config["COMPRESS_ALGORITHM"] = FlaskConf.COMPRESS_ALGORITHM
app.server.config["COMPRESS_BR_LEVEL"] = FlaskConf.COMPRESS_BR_LEVEL
app.server.secret_key = FlaskConf.COOKIE_SESSION_SECRET_KEY
app.title = ShowConf.WEB_TITLE

# flask实例
server = app.server


# 头像获取接口
@server.route("/avatar/<user_name>")
def download_file(user_name):
    file_name = f"{user_name}.jpg"
    if ".." in user_name:
        logger.warning(
            f"有人尝试通过头像文件接口攻击，URL:{request.url}，IP:{request.remote_addr}"
        )
        abort(HttpStatusConstant.FORBIDDEN)
    else:
        return send_from_directory(PathProj.AVATAR_DIR_PATH, file_name)


# nginx代理后，拦截直接访问
@server.before_request
def ban_bypass_proxy():
    from config.dashgo_conf import ProxyConf

    if ProxyConf.NGINX_PROXY and request.headers.get("X-Forwarded-For") is None:
        abort(HttpStatusConstant.FORBIDDEN)


# 恶意访问管理页面拦截器
@server.before_request
def ban_admin():
    if request.path.startswith("/admin"):
        from common.utilities.util_browser import get_browser_info

        browser_info = get_browser_info()
        logger.warning(
            f"有人尝试访问不存在的管理页面，URL:{browser_info.url}，IP:{browser_info.request_addr}"
        )
        abort(HttpStatusConstant.NOT_FOUND)


# 获取用户浏览器信息
@server.before_request
def get_user_agent_info():
    from common.utilities.util_browser import get_browser_info

    browser_info = get_browser_info()
    if browser_info.type == "ie":
        return "<h1 style='color: red'>IP:{}, {}</h1>".format(
            browser_info.request_addr, t__other("请不要使用IE内核浏览器")
        )
    elif (
        browser_info.type == "chrome"
        and browser_info.version is not None
        and browser_info.version < 88
    ):
        return "<h1 style='color: red'>IP:{}, {}</h1>".format(
            browser_info.request_addr,
            t__other("Chrome内核版本号太低，请升级浏览器"),
        )


# 自动管理数据库上下文
@server.before_request
def _db_connect():
    from database.sql_db.conn import db

    db().connect(reuse_if_open=True)


@server.teardown_request
def _db_close(exc):
    from database.sql_db.conn import db

    _db = db()
    if not _db.is_closed():
        _db.close()


# 首页重定向
@server.before_request
def main_page_redirct():
    if request.method == "GET":
        if request.path == "/":
            return redirect("/sys_dashboard/workbench")


def serve(
    *,
    host: str = "localhost",
    port: int = 7777,
    reload: bool = False,
    reload_includes: Optional[List[str]] = None,
    reload_excludes: Optional[List[str]] = None,
    workers: Optional[int] = 4,
    access_log: bool = False,
    **kwargs,
):
    import uvicorn
    from uvicorn.middleware.wsgi import WSGIMiddleware

    # Create a terminal panel to announce OS initialization and provide useful info
    from rich.align import Align
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich import box
    import platform

    panel_group = [
        Align.center(
            f"\n\n[bold dark_orange]running on:[/bold dark_orange] [bold cyan]http://{host}:{port}[/bold cyan]"
        ),
    ]

    console = Console()
    console.print(
        Panel(
            Group(*panel_group),
            title=ShowConf.APP_NAME,
            expand=False,
            border_style="dark_orange",
            box=box.DOUBLE_EDGE,
            padding=(2, 2),
        )
    )

    uvicorn.run(
        app=WSGIMiddleware(server),
        host=host,
        port=port,
        reload=reload,
        reload_includes=reload_includes,
        reload_excludes=reload_excludes,
        workers=None if platform.system() == "Windows" else workers,
        access_log=access_log,
        **kwargs,
    )
