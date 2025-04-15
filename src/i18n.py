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
t__access = partial(translator.t, locale_topic='access')
t__dashboard = partial(translator.t, locale_topic='dashboard')
t__person = partial(translator.t, locale_topic='person')
t__notification = partial(translator.t, locale_topic='notification')
t__task = partial(translator.t, locale_topic='task')
t__setting = partial(translator.t, locale_topic='setting')
t__other = partial(translator.t, locale_topic='other')