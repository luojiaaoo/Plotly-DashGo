from server import app
from common.utilities import util_jwt
import feffery_utils_components as fuc
import feffery_antd_components as fac
from dash import dcc, html
from dash_view.pages import main, login
from common.utilities.util_menu_access import MenuAccess
from common.exception import NotFoundUserException
from config.access_factory import AccessFactory
import sys
from database.sql_db.conn import initialize_database
from dash_view.framework.func import render_func_content

# 检查Python运行版本
if sys.version_info < (3, 9):
    raise Exception('Python version must above 3.9 !!')

# 初始化数据库
initialize_database()

# 启动检查权限
AccessFactory.check_access_meta()

# 用户授权路由
app.layout = lambda: fuc.FefferyTopProgress(
    [
        *render_func_content(),
        # 应用根容器
        html.Div(
            id='root-container',
        ),
    ],
    listenPropsMode='include',
    includeProps=['root-container.children'],
    minimum=0.33,
    color='#1677ff',
)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
