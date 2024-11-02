import os
from flask import request
from feffery_dash_utils.i18n_utils import Translator

translator = Translator(
    translations=[
        # 全局无主题文案
        './translations/locales.json',
        # 各组件文档主题文案
        *[
            os.path.join('./translations/topic_locales', path)
            for path in os.listdir('./translations/topic_locales')
        ],
    ],
)


def get_current_locale() -> str:
    """获取当前国际化语种"""
    return request.cookies.get(translator.cookie_name, 'zh-cn')