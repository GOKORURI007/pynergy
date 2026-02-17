import gettext
import locale
import os
from pathlib import Path


def _get_translator():
    # 1. 确定语言代码
    # 优先看环境变量，方便 NixOS 下手动切换测试 (如: LANG=en_US pynergy)
    default_lang = locale.getlocale()[0] or 'en_US'
    lang = os.environ.get('LANG', default_lang).split('.')[0]

    # 2. 定位相对于当前文件的 locales 目录
    # 结构: pynergy_client/locales/zh_CN/LC_MESSAGES/pynergy.mo
    locale_dir = Path(__file__).parent.resolve() / 'locales'

    # 3. 加载翻译对象
    # 注意 domain 必须与脚本中的 DOMAIN 一致
    translation = gettext.translation(
        domain='pynergy', localedir=str(locale_dir), languages=[lang], fallback=True
    )
    return translation.gettext


# 单例导出
_ = _get_translator()
