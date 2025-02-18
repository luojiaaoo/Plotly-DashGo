from common.utilities.util_menu_access import MenuAccess
import random
import feffery_antd_charts as fact
import feffery_antd_components as fac
import feffery_utils_components as fuc
from feffery_dash_utils.style_utils import style
from dash_components import Card
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from i18n import t__dashboard


# 二级菜单的标题、图标和显示顺序
title = '工作台'
icon = None
order = 1
logger = Log.get_logger(__name__)

access_metas = ('工作台-页面',)


def chart_block(title, chart):
    """示例自定义组件，返回仪表盘区块"""

    return fac.AntdFlex(
        [
            fac.AntdText(
                title,
                style=style(borderLeft='3px solid #1890ff', paddingLeft=8, fontSize=15),
            ),
            chart,
        ],
        vertical=True,
        gap=8,
        style=style(height='calc(100% - 20px)'),
    )


def render_content(menu_access: MenuAccess, **kwargs):
    return fac.AntdSpace(
        [
            Card(
                fac.AntdSpace(
                    [
                        fac.AntdAvatar(
                            id='workbench-avatar',
                            mode='image',
                            src=f'/avatar/{menu_access.user_info.user_name}',
                            alt=menu_access.user_info.user_full_name,
                            size=70,
                            style={'marginRight': '20px'},
                        ),
                        fac.AntdText(t__dashboard('你好，')),
                        fac.AntdText(menu_access.user_info.user_full_name, id='workbench-user-full-name'),
                    ]
                )
            ),
            fuc.FefferyGrid(
                [
                    fuc.FefferyGridItem(
                        chart_block(
                            title='折线图示例',
                            chart=fact.AntdLine(
                                data=[
                                    {
                                        'date': f'2020-0{i}',
                                        'y': random.randint(50, 100),
                                    }
                                    for i in range(1, 10)
                                ],
                                xField='date',
                                yField='y',
                                slider={},
                            ),
                        ),
                        key='折线图示例',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='面积图示例',
                            chart=fact.AntdArea(
                                data=[
                                    {
                                        'date': f'2020-0{i}',
                                        'y': random.randint(50, 100),
                                    }
                                    for i in range(1, 10)
                                ],
                                xField='date',
                                yField='y',
                                areaStyle={'fill': 'l(270) 0:#ffffff 0.5:#7ec2f3 1:#1890ff'},
                            ),
                        ),
                        key='面积图示例',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='柱状图示例',
                            chart=fact.AntdColumn(
                                data=[
                                    {
                                        'date': f'2020-0{i}',
                                        'y': random.randint(0, 100),
                                        'type': f'item{j}',
                                    }
                                    for i in range(1, 10)
                                    for j in range(1, 4)
                                ],
                                xField='date',
                                yField='y',
                                seriesField='type',
                                isGroup=True,
                            ),
                        ),
                        key='柱状图示例',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='条形图示例',
                            chart=fact.AntdBar(
                                data=[
                                    {
                                        'year': '1951 年',
                                        'value': 38,
                                    },
                                    {
                                        'year': '1952 年',
                                        'value': 52,
                                    },
                                    {
                                        'year': '1956 年',
                                        'value': 61,
                                    },
                                    {
                                        'year': '1957 年',
                                        'value': 145,
                                    },
                                    {
                                        'year': '1958 年',
                                        'value': 48,
                                    },
                                ],
                                xField='value',
                                yField='year',
                                seriesField='year',
                                legend={
                                    'position': 'top-left',
                                },
                            ),
                        ),
                        key='条形图示例',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='饼图示例',
                            chart=fact.AntdPie(
                                data=[
                                    {
                                        'type': f'item{i}',
                                        'x': random.randint(50, 100),
                                    }
                                    for i in range(1, 6)
                                ],
                                colorField='type',
                                angleField='x',
                                radius=0.9,
                            ),
                        ),
                        key='饼图示例',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='双轴图示例',
                            chart=fact.AntdDualAxes(
                                data=[
                                    # 左轴数据
                                    [
                                        {
                                            'date': f'2020-0{i}',
                                            'y1': random.randint(50, 100),
                                        }
                                        for i in range(1, 10)
                                    ],
                                    # 右轴数据
                                    [
                                        {
                                            'date': f'2020-0{i}',
                                            'y2': random.randint(100, 1000),
                                        }
                                        for i in range(1, 10)
                                    ],
                                ],
                                xField='date',
                                yField=['y1', 'y2'],
                                geometryOptions=[
                                    {'geometry': 'line'},
                                    {'geometry': 'column'},
                                ],
                            ),
                        ),
                        key='双轴图示例',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='迷你面积图示例',
                            chart=fact.AntdTinyArea(
                                data=[random.randint(50, 100) for _ in range(20)],
                                height=60,
                                smooth=True,
                            ),
                        ),
                        key='迷你面积图示例',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='进度条图示例',
                            chart=fact.AntdProgress(percent=0.7, barWidthRatio=0.2),
                        ),
                        key='进度条图示例',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='进度环图示例',
                            chart=fact.AntdRingProgress(
                                percent=0.6,
                                color=['#F4664A', '#E8EDF3'],
                                innerRadius=0.85,
                                radius=0.98,
                                statistic={
                                    'title': {
                                        'style': {
                                            'color': '#363636',
                                            'fontSize': '12px',
                                            'lineHeight': '14px',
                                        },
                                        'formatter': {'func': "() => '进度'"},
                                    },
                                },
                            ),
                        ),
                        key='进度环图示例',
                    ),
                ],
                layouts=[
                    dict(i='折线图示例', x=0, y=0, w=1, h=2),
                    dict(i='面积图示例', x=1, y=0, w=1, h=2),
                    dict(i='柱状图示例', x=2, y=0, w=1, h=2),
                    dict(i='条形图示例', x=0, y=1, w=1, h=2),
                    dict(i='饼图示例', x=1, y=1, w=1, h=2),
                    dict(i='双轴图示例', x=2, y=1, w=1, h=2),
                    dict(i='迷你面积图示例', x=0, y=2, w=1, h=1),
                    dict(i='进度条图示例', x=1, y=2, w=1, h=1),
                    dict(i='进度环图示例', x=2, y=2, w=1, h=2),
                ],
                cols=3,
                rowHeight=150,
                placeholderBorderRadius='5px',
                margin=[12, 12],
            ),
        ],
        direction='vertical',
        style={'width': '100%'},
    )
