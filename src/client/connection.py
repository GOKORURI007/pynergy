"""
主客户端模块

实现 Deskflow 客户端主逻辑，包括网络连接、消息处理循环和命令行参数解析。
"""

import socket

from evdev import ecodes
from loguru import logger

from src.utils import get_screen_size

from ..device import VirtualDevice
from ..protocol import HelloBackMsg, HelloMsg, MsgID, SynergyParser
from .states import ClientState


class SynergyClient:
    """Deskflow 客户端类

    负责连接服务器、接收消息并将输入事件注入系统。
    """

    def __init__(
        self,
        server: str,
        port: int = 24800,
        coords_mode: str = 'relative',
        screen_width: int | None = None,
        screen_height: int | None = None,
        client_name: str = 'Pynergy',
        device: VirtualDevice | None = None,
    ):
        """初始化客户端

        Args:
            server: 服务器 IP 地址
            port: 端口号 (默认: 24800)
            coords_mode: 坐标模式 ('relative' 或 'absolute')
            screen_width: 屏幕宽度 (可选，默认自动获取)
            screen_height: 屏幕高度 (可选，默认自动获取)
            client_name: 客户端名称
            device: 虚拟设备实例 (可选，默认自动创建)
        """
        self._server = server
        self._port = port
        self._coords_mode = coords_mode
        self._client_name = client_name

        if screen_width is None or screen_height is None:
            screen_width, screen_height = get_screen_size()
        self._screen_width = screen_width
        self._screen_height = screen_height

        self._device = device
        self.parser = SynergyParser()
        self._sock: socket.socket | None = None
        self._running = False
        self._state = ClientState.DISCONNECTED
        self._last_x: int | None = None
        self._last_y: int | None = None
        self._pressed_keys: set[int] = set()

    @property
    def device(self) -> VirtualDevice:
        """获取虚拟设备"""
        if self._device is None:
            self._device = VirtualDevice()
        return self._device

    def connect(self) -> None:
        """连接 Deskflow 服务器并进行握手"""
        self._state = ClientState.CONNECTING
        logger.info(f'正在连接到 {self._server}:{self._port}...')
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self._server, self._port))

        self._state = ClientState.HANDSHAKE
        logger.debug('等待服务器 Hello 消息...')
        data: bytes = self._sock.recv(1024)
        self.parser.feed(data)
        msg: HelloMsg | None = self.parser.next_handshake_msg(MsgID.Hello)
        logger.debug(f'服务器协议: {msg.protocol_name} {msg.major}.{msg.minor}')

        logger.info(f'发送 HelloBack，客户端名称: {self._client_name}')
        back_msg: HelloBackMsg = HelloBackMsg(
            msg.protocol_name, msg.major, msg.minor, self._client_name
        )
        self._sock.sendall(back_msg.pack_for_socket())

        self._state = ClientState.CONNECTED
        logger.success('握手完成，进入 Connected 状态')

    def run(self) -> None:
        """运行主事件循环"""
        if self._sock is None:
            self.connect()
        assert self._sock is not None

        self._running = True
        logger.info('开始处理消息...')

        try:
            while self._running:
                data = self._sock.recv(4096)
                if not data:
                    break
                self.parser.feed(data)
                while True:
                    msg = self.parser.next_msg()
                    if msg is None:
                        break
                    logger.debug(f'收到消息: {msg}')
                # self._handle_message(msg_type, params)
        except (ConnectionResetError, BrokenPipeError) as e:
            logger.error(f'连接断开: {e}')
        except Exception as e:
            logger.error(f'处理消息时出错: {e}')
            raise
        finally:
            self.close()

    def _handle_message(self, msg_type: MsgID, params: dict) -> None:
        """处理消息

        Args:
            msg_type: 消息类型
            params: 消息参数
        """
        if msg_type == MsgID.QINF:
            logger.info('收到 QINF 查询屏幕信息，发送 DINF')
            dinf = self._protocol.build_dinf(
                0,
                0,
                self._screen_width,
                self._screen_height,
                0,
                0,
            )
            assert self._sock is not None
            self._sock.send(dinf)
            return

        elif msg_type == MsgID.CINN:
            logger.info(f'进入屏幕，位置: ({params["x"]}, {params["y"]})')
            self._state = ClientState.ACTIVE
            modifiers = params.get('modifiers', 0)
            self._sync_modifiers(modifiers)
            self._last_x = None
            self._last_y = None
            return

        elif msg_type == MsgID.COUT:
            logger.info('离开屏幕')
            self._state = ClientState.CONNECTED
            self._release_all_keys()
            return

        elif msg_type == MsgID.CALV:
            logger.debug('收到心跳，响应 CALV')
            assert self._sock is not None
            self._sock.send(self._protocol.build_calv())
            return

        elif msg_type == MsgID.CBYE:
            logger.info('收到关闭连接消息')
            self._running = False
            return

        elif msg_type == MsgID.EICV:
            reason = params.get('reason', 0)
            logger.error(f'版本不兼容错误: {reason}')
            self._running = False
            return

        elif msg_type == MsgID.EBSY:
            logger.error('服务器忙')
            self._running = False
            return

        if self._state != ClientState.ACTIVE:
            logger.debug(f'忽略消息 {msg_type}，当前状态: {self._state}')
            return

        device = self.device

        if msg_type == MsgID.DMMV:
            x, y = params['x'], params['y']
            if self._coords_mode == 'relative':
                dx, dy = self._abs_to_rel(x, y)
                if dx != 0 or dy != 0:
                    device.write_mouse_move(dx, dy)
            else:
                self._write_mouse_abs(x, y)

        elif msg_type == MsgID.DMRM:
            dx, dy = params['dx'], params['dy']
            if dx != 0 or dy != 0:
                device.write_mouse_move(dx, dy)

        elif msg_type == MsgID.DKDN:
            key_code = params['key_code']
            self._pressed_keys.add(key_code)
            device.write_key(key_code, True)

        elif msg_type == MsgID.DKUP:
            key_code = params['key_code']
            self._pressed_keys.discard(key_code)
            device.write_key(key_code, False)

        elif msg_type == MsgID.DMDN:
            button = params['button']
            device.write_key(button, True)

        elif msg_type == MsgID.DMUP:
            button = params['button']
            device.write_key(button, False)

        elif msg_type == MsgID.DMWM:
            x = params.get('x', 0)
            y = params.get('y', 0)
            if y != 0:
                device.write(ecodes.EV_REL, ecodes.REL_WHEEL, y)
            if x != 0:
                device.write(ecodes.EV_REL, ecodes.REL_HWHEEL, x)

        elif msg_type == MsgID.DKRP:
            key_code = params['key_code']
            if key_code not in self._pressed_keys:
                self._pressed_keys.add(key_code)
                device.write_key(key_code, True)

        device.syn()

    def _sync_modifiers(self, modifiers: int) -> None:
        """同步修饰键状态

        Args:
            modifiers: 修饰键位掩码
        """
        pass

    def _release_all_keys(self) -> None:
        """释放所有按下的键"""
        device = self.device
        for key_code in list(self._pressed_keys):
            device.write_key(key_code, False)
            self._pressed_keys.discard(key_code)
        device.syn()

    def _abs_to_rel(self, x: int, y: int) -> tuple[int, int]:
        """将 Synergy 绝对坐标转换为相对位移

        Args:
            x: 0-65535 范围的绝对坐标
            y: 0-65535 范围的绝对坐标

        Returns:
            (dx, dy) 相对位移
        """
        if self._last_x is None or self._last_y is None:
            self._last_x, self._last_y = x, y
            return 0, 0

        dx = int((x - self._last_x) * (self._screen_width / 65535))
        dy = int((y - self._last_y) * (self._screen_height / 65535))

        self._last_x, self._last_y = x, y
        return dx, dy

    def _write_mouse_abs(self, x: int, y: int) -> None:
        """写入绝对坐标

        Args:
            x: X 坐标 (0-65535)
            y: Y 坐标 (0-65535)
        """
        device = self.device
        device.write(ecodes.EV_ABS, ecodes.ABS_X, x)
        device.write(ecodes.EV_ABS, ecodes.ABS_Y, y)

    def close(self) -> None:
        """关闭连接和设备"""
        self._running = False
        self._state = ClientState.DISCONNECTED
        if self._sock:
            self._sock.close()
            self._sock = None
        if self._device:
            self._device.close()
            self._device = None
        logger.info('客户端已关闭')

    def stop(self) -> None:
        """停止客户端"""
        self._running = False
