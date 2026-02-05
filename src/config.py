"""
项目全局配置文件。
"""

from pathlib import Path
from typing import Literal

LogLevel = Literal['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']

# 日志名称
LOGGER_NAME: str = 'Pynergy'
# 日志文件夹
LOG_DIR: Path = Path.cwd() / 'logs'
# 日志文件名
LOG_FILE: str = 'pynergy.log'
# 文件输出日志级别
LOG_LEVEL_FILE: LogLevel = 'INFO'
# 标准输出日志级别
LOG_LEVEL_STDOUT: LogLevel = 'DEBUG'

# src/config.py 文件末尾
try:
    # 尝试从本地配置文件中导入并覆盖
    from .local_config import *  # noqa: F403
except ImportError:
    # 如果 a.py 不存在，则什么也不做
    pass
