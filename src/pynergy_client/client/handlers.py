import asyncio
import time
from functools import wraps
from typing import TYPE_CHECKING

from loguru import logger

from .. import config
from ..device import BaseDeviceContext, BaseKeyboardVirtualDevice, BaseMouseVirtualDevice

if TYPE_CHECKING:
    from .client import PynergyClient

from ..keymaps import hid_to_ecode, synergy_to_hid
from ..pynergy_protocol import (
    CEnterMsg,
    CInfoAckMsg,
    CKeepAliveMsg,
    DInfoMsg,
    DKeyDownLangMsg,
    DKeyDownMsg,
    DKeyRepeatMsg,
    DKeyUpMsg,
    DLanguageSynchronisationMsg,
    DMouseDownMsg,
    DMouseMoveMsg,
    DMouseRelMoveMsg,
    DMouseUpMsg,
    DMouseWheelMsg,
    EIncompatibleMsg,
    MsgBase,
)
from .protocols import ClientState


def device_check(func):
    @wraps(func)
    async def wrapper(self, msg, client):
        # 1. 状态检查 (这里的 self 指的是调用者，即 Handler 或 Client 的实例)
        if client.state != ClientState.ACTIVE:
            logger.warning(f'忽略消息 {msg}，当前状态: {client.state}')
            return None

        # 2. 执行核心业务逻辑
        result = await func(self, msg, client)

        # 3. 统一设备同步
        self.mouse.syn()
        self.keyboard.syn()

        return result

    return wrapper


class PynergyHandler:
    """专门负责处理解析后的业务逻辑"""

    def __init__(
        self,
        cfg: config.Config,
        context: BaseDeviceContext,
        mouse_device: BaseMouseVirtualDevice,
        keyboard_device: BaseKeyboardVirtualDevice,
    ):
        self.ctx = context
        self.mouse = mouse_device
        self.keyboard = keyboard_device
        self.abs_mouse_move = cfg.abs_mouse_move
        self.interval = cfg.mouse_move_threshold / 1000
        self.mouse_pos_sync_freq = cfg.mouse_pos_sync_freq

        self._flush_task: asyncio.TimerHandle | None = None
        self._last_mouse_time = 0
        self._move_count = 0
        self._pending_pos = None

    @staticmethod
    async def default_handler(msg, client=None):
        logger.warning(f'Ignored message: {msg.CODE}')

    @staticmethod
    async def on_hello(msg: MsgBase, client=None):
        logger.debug(f'Handle {msg}')
        logger.warning(f'Handler {msg.CODE} is unimplement')

    @staticmethod
    async def on_helloback(msg: MsgBase, client=None):
        logger.debug(f'Handle {msg}')
        logger.warning(f'Handler {msg.CODE} is unimplement')

    @staticmethod
    async def on_cclp(msg: MsgBase, client=None):
        logger.debug(f'Handle {msg}')
        logger.warning(f'Handler {msg.CODE} is unimplement')

    @staticmethod
    async def on_cbye(msg: MsgBase, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        logger.info('收到关闭连接消息')
        client.running = False

    async def on_cinn(self, msg: CEnterMsg, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        logger.info(f'进入屏幕，位置: ({msg.entry_x}, {msg.entry_y})')
        self.mouse.move_absolute(msg.entry_x, msg.entry_y)
        self.ctx.logical_pos = (msg.entry_x, msg.entry_y)
        client.state = ClientState.ACTIVE

        modifiers = msg.mod_key_mask
        self.keyboard.sync_modifiers(modifiers)

    @staticmethod
    async def on_ciak(msg: MsgBase, client=None):
        logger.debug(f'Handle {msg}')

    @staticmethod
    async def on_calv(msg: CKeepAliveMsg, client: 'PynergyClient'):
        logger.trace(f'Handle {msg}')
        await client.send_message(msg.pack_for_socket())

    async def on_cout(self, msg: MsgBase, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        client.state = ClientState.CONNECTED
        self.keyboard.release_all_key()
        self.mouse.release_all_button()

    @staticmethod
    async def on_cnop(msg: MsgBase, client=None):
        logger.debug(f'Handle {msg}')
        logger.warning(f'Handler {msg.CODE} is unimplement')

    @staticmethod
    async def on_crop(msg: MsgBase, client=None):
        logger.debug(f'Handle {msg}')
        logger.warning(f'Handler {msg.CODE} is unimplement')

    @staticmethod
    async def on_csec(msg: MsgBase, client=None):
        logger.debug(f'Handle {msg}')
        logger.warning(f'Handler {msg.CODE} is unimplement')

    @device_check
    async def on_dkdn(self, msg: DKeyDownMsg, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        key_code = msg.key_button
        self.keyboard.send_key(hid_to_ecode(synergy_to_hid(key_code)), True)

    @device_check
    async def on_dkdl(self, msg: DKeyDownLangMsg, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        key_code = msg.key_button
        self.keyboard.send_key(hid_to_ecode(synergy_to_hid(key_code)), True)

    @device_check
    async def on_dkrp(self, msg: DKeyRepeatMsg, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')

        key_code = msg.key_button
        if key_code not in self.keyboard.pressed_keys:
            self.keyboard.send_key(hid_to_ecode(synergy_to_hid(key_code)), True)

    @device_check
    async def on_dkup(self, msg: DKeyUpMsg, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        key_code = msg.key_button
        self.keyboard.send_key(hid_to_ecode(synergy_to_hid(key_code)), False)

    @device_check
    async def on_dmdn(self, msg: DMouseDownMsg, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        button = msg.button
        self.mouse.send_button(hid_to_ecode(synergy_to_hid((button << 8) + 0xAA)), True)

    # @device_check
    async def on_dmmv(self, msg: DMouseMoveMsg, client: 'PynergyClient'):
        logger.trace(f'Handle {msg}')
        now = time.perf_counter()

        # 1. 取消现有的补齐定时器（因为有了新移动）
        if self._flush_task:
            self._flush_task.cancel()
            self._flush_task = None

        if now - self._last_mouse_time < self.interval:
            self._pending_pos = (msg.x, msg.y)
            # 启动延迟补齐：如果后续没动作，50ms 后强行刷入这一帧
            self._flush_task = asyncio.get_event_loop().call_later(
                0.05, lambda: asyncio.create_task(self._flush_pending_move())
            )
            return

        if self.abs_mouse_move:
            self.mouse.move_absolute(msg.x, msg.y)
            self.mouse.syn()
            self._last_mouse_time = time.perf_counter()
            self._pending_pos = None
        else:
            self._move_count += 1
            if self._move_count >= self.mouse_pos_sync_freq:
                self.mouse.move_absolute(msg.x, msg.y)
                self.mouse.syn()
                self._move_count = 0
                return
            dx, dy = self.ctx.calculate_relative_move(msg.x, msg.y)
            if dx != 0 or dy != 0:
                self.mouse.move_relative(dx, dy)
                self.mouse.syn()

    async def _flush_pending_move(self):
        """延迟补齐逻辑：强制刷入最后一帧"""
        if self._pending_pos:
            x, y = self._pending_pos
            logger.trace(f'Flushing pending move to {x}, {y}')
            self.mouse.move_absolute(x, y)
            self.mouse.syn()
            self._last_mouse_time = time.perf_counter()
            self._pending_pos = None

    async def on_dmrm(self, msg: DMouseRelMoveMsg, client: 'PynergyClient'):
        logger.trace(f'Handle {msg}')
        self.mouse.move_relative(msg.dx, msg.dy)
        self.mouse.syn()

    @device_check
    async def on_dmup(self, msg: DMouseUpMsg, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        button = msg.button
        self.mouse.send_button(hid_to_ecode(synergy_to_hid((button << 8) + 0xAA)), False)

    @device_check
    async def on_dmwm(self, msg: DMouseWheelMsg, client: 'PynergyClient'):
        logger.trace(f'Handle {msg}')

        x, y = msg.x_delta, msg.y_delta
        if y != 0:
            self.mouse.wheel_relative(1 if y > 0 else -1)
        if x != 0:
            self.mouse.wheel_relative(1 if x > 0 else -1)

    @device_check
    async def on_dclp(self, msg: MsgBase, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')

    @staticmethod
    async def on_dinf(msg: MsgBase, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}, 发送 CIAK')
        await client.send_message(CInfoAckMsg().pack_for_socket())

    @staticmethod
    async def on_dsop(msg: MsgBase, client=None):
        logger.debug(f'Handle {msg}')
        logger.warning(f'Handler {msg.CODE} is unimplement')

    @staticmethod
    async def on_ddrg(msg: MsgBase, client=None):
        logger.debug(f'Handle {msg}')
        logger.warning(f'Handler {msg.CODE} is unimplement')

    @staticmethod
    async def on_dftr(msg: MsgBase, client=None):
        logger.debug(f'Handle {msg}')
        logger.warning(f'Handler {msg.CODE} is unimplement')

    @staticmethod
    async def on_lsyn(msg: DLanguageSynchronisationMsg, client=None):
        logger.debug(f'Handle {msg}')

    @staticmethod
    async def on_secn(msg: MsgBase, client=None):
        logger.debug(f'Handle {msg}')

    async def on_qinf(self, msg: MsgBase, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}，发送 DINF')
        try:
            self.ctx.update_screen_info()
            self.ctx.sync_logical_to_real()
        except Exception as e:
            logger.warning(f'Failed to get mouse position: {e}')
        dinf_msg = DInfoMsg(
            0,
            0,
            self.ctx.screen_size[0],
            self.ctx.screen_size[1],
            0,
            self.ctx.logical_pos[0],
            self.ctx.logical_pos[1],
        )
        assert client.writer is not None
        await client.send_message(dinf_msg.pack_for_socket())

    @staticmethod
    async def on_ebad(msg: MsgBase, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        await client.stop()

    @staticmethod
    async def on_ebsy(msg: MsgBase, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        await client.stop()

    @staticmethod
    async def on_eicv(msg: EIncompatibleMsg, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        logger.error(f'版本不兼容错误: {msg.major}.{msg.minor}')
        await client.stop()

    @staticmethod
    async def on_eunk(msg: MsgBase, client: 'PynergyClient'):
        logger.debug(f'Handle {msg}')
        await client.stop()
