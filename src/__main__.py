import sys
from typing import Optional

import click
from loguru import logger

from src.client.connection import SynergyClient, get_screen_size


@click.command()
@click.option(
    '--server',
    '-s',
    default='192.168.123.154',
    help='Deskflow 服务器 IP 地址',
)
@click.option(
    '--port',
    '-p',
    default=24800,
    help='端口号 (默认: 24800)',
)
@click.option(
    '--coords-mode',
    type=click.Choice(['relative', 'absolute']),
    default='relative',
    help='坐标模式: relative=相对位移, absolute=绝对坐标',
)
@click.option(
    '--screen-width',
    type=int,
    default=None,
    help='屏幕宽度 (用于相对位移计算, 默认: 自动获取)',
)
@click.option(
    '--screen-height',
    type=int,
    default=None,
    help='屏幕高度 (用于相对位移计算, 默认: 自动获取)',
)
@click.option(
    '--client-name',
    '-n',
    default='Pynergy',
    help='客户端名称 (默认: Pynergy)',
)
@click.option(
    '--verbose',
    '-v',
    count=True,
    help='详细输出 (可多次使用增加详细程度)',
)
def main(
    server: str,
    port: int,
    coords_mode: str,
    screen_width: Optional[int],
    screen_height: Optional[int],
    client_name: str,
    verbose: int,
) -> None:
    """Pynergy - Deskflow 客户端

    连接 Deskflow 服务器并将输入事件注入系统。
    """

    if screen_width is None or screen_height is None:
        screen_width, screen_height = get_screen_size()
        logger.info(f'自动获取屏幕尺寸: {screen_width}x{screen_height}')

    logger.info(f'启动客户端，服务器: {server}:{port}, 客户端名称: {client_name}')

    try:
        client = SynergyClient(
            server=server,
            port=port,
            coords_mode=coords_mode,
            screen_width=screen_width,
            screen_height=screen_height,
            client_name=client_name,
        )
        client.run()
    except KeyboardInterrupt:
        logger.info('收到中断信号，正在退出...')
    except Exception as e:
        logger.error(f'客户端错误: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
