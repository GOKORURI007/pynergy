import asyncio
import json
import sys
from dataclasses import fields, replace
from pathlib import Path
from typing import Annotated, get_args

import typer
from loguru import logger
from platformdirs import user_config_path

from .client.client import PynergyClient
from .client.dispatcher import MessageDispatcher
from .client.handlers import PynergyHandler
from .config import Available_Backends, Config, LogLevel
from .i18n import _
from .pynergy_protocol import PynergyParser
from .utils import init_backend, init_logger

app = typer.Typer(help=_('Pynergy Client'), add_completion=True)


def get_backend_help_text(device_type: str):
    options = ', '.join(get_args(Available_Backends))

    return _('{device_type} backend. Available: {options}').format(
        device_type=device_type, options=options
    )


@app.command()
def main(
    config: Annotated[
        Path, typer.Option(help=_('Path to the configuration file'))
    ] = user_config_path(appname='pynergy', ensure_exists=True) / 'client-config.json',
    server: Annotated[str | None, typer.Option(help=_('Deskflow/Others server IP address'))] = None,
    port: Annotated[int | None, typer.Option(help=_('Port number'))] = None,
    client_name: Annotated[str | None, typer.Option(help=_('Client name'))] = None,
    mouse_backend: Annotated[
        Available_Backends | None, typer.Option(help=_(get_backend_help_text('Mouse')))
    ] = None,
    keyboard_backend: Annotated[
        Available_Backends | None, typer.Option(help=_(get_backend_help_text('Keyboard')))
    ] = None,
    screen_width: Annotated[int | None, typer.Option(help=_('Screen width'))] = None,
    screen_height: Annotated[int | None, typer.Option(help=_('Screen height'))] = None,
    abs_mouse_move: Annotated[
        bool | None, typer.Option(help=_('Whether to use absolute displacement'))
    ] = None,
    mouse_move_threshold: Annotated[
        int | None, typer.Option(help=_('Unit: ms, balances smoothness and performance'))
    ] = None,
    mouse_pos_sync_freq: Annotated[
        int | None,
        typer.Option(help=_('Sync frequency, sync with system real position every n moves')),
    ] = None,
    logger_name: Annotated[str | None, typer.Option(help=_('Logger name'))] = None,
    log_dir: Annotated[str | None, typer.Option(help=_('Log directory location'))] = None,
    log_file: Annotated[str | None, typer.Option(help=_('Log file name'))] = None,
    log_level_file: Annotated[LogLevel | None, typer.Option(help=_('File log level'))] = None,
    log_level_stdout: Annotated[LogLevel | None, typer.Option(help=_('Console log level'))] = None,
):
    """
    启动 Pynergy 客户端，支持通过命令行参数覆盖 JSON 配置。
    优先级为 cli > config_file > default
    """

    # 1. 加载 JSON 配置文件
    if not config.exists():
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text('{}', encoding='utf-8')

    try:
        with open(config, 'r', encoding='utf-8') as f:
            json_dict = json.load(f)
    except json.JSONDecodeError:
        json_dict = {}

    # 2. 实例化基础配置 (过滤无效字段)
    valid_fields = {f.name for f in fields(Config)}
    filtered_json = {k: v for k, v in json_dict.items() if k in valid_fields}
    cfg = Config(**filtered_json)

    # 3. 收集 CLI 传入的参数 (即 locals() 中不为 None 的部分 )
    # 排除掉非 Config 字段的参数，如 config_file
    cli_args = locals()
    overrides = {k: cli_args[k] for k in valid_fields if k in cli_args and cli_args[k] is not None}

    # 执行覆盖
    cfg = replace(cfg, **overrides)

    # 4. 运行应用
    try:
        asyncio.run(run_app(cfg))
    except KeyboardInterrupt:
        typer.echo('\n已停止服务')


async def run_app(cfg: Config):
    init_logger(cfg)
    logger.info(f'日志记录器已初始化: {cfg.log_dir}/{cfg.log_file}')

    device_ctx, mouse, keyboard = init_backend(cfg)
    assert device_ctx and mouse and keyboard
    if not cfg.screen_width or not cfg.screen_height:
        device_ctx.update_screen_info()
        logger.info(f'自动获取屏幕尺寸: {device_ctx.screen_size[0]}x{device_ctx.screen_size[1]}')

    handler = PynergyHandler(cfg, device_ctx, mouse, keyboard)
    dispatcher = MessageDispatcher(handler)
    parser = PynergyParser()
    client = PynergyClient(
        server=cfg.server,
        port=cfg.port,
        client_name=cfg.client_name,
        parser=parser,
        dispatcher=dispatcher,
    )

    # 1. 启动 Worker
    # 它会一直运行，等待队列里的消息
    worker_task = asyncio.create_task(dispatcher.worker(0))

    # 2. 启动 Client 监听
    client.listen_task = asyncio.create_task(client.run())

    try:
        await client.listen_task
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        logger.info('收到中断信号，正在退出...')
    except Exception as e:
        logger.error(f'客户端错误: {e}')
        sys.exit(1)
    finally:
        # 3. 停止所有任务
        await client.stop()
        worker_task.cancel()
