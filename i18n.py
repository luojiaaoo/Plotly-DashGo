import os
from flask import request
from feffery_dash_utils.i18n_utils import Translator
from functools import partial

translator = Translator(
    translations=[
        # 全局无主题文案
        './translations/locales.json',
        # 各组件文档主题文案
        *[os.path.join('./translations/topic_locales', path) for path in os.listdir('./translations/topic_locales')],
    ],
    force_check_content_translator=False,
)

t__default = partial(translator.t)
t__access_mgmt = partial(translator.t, locale_topic='access_mgmt')
t__other = partial(translator.t, locale_topic='other')