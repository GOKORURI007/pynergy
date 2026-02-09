import os
import socket
from typing import List, Optional

from src.input_control.base import BackendCapabilities, KeyboardBackend, MouseBackend, Point


class HyprlandBackend(MouseBackend, KeyboardBackend):
    """通过 Hyprland IPC 控制"""

    def __init__(self, config: dict):
        super().__init__(config)
        self._socket_path: Optional[str] = None
        self._caps = BackendCapabilities(
            absolute_move=True,  # 支持 movecursor
            relative_move=True,
            scroll=True,
            keyboard=True,
        )
        # 按键映射表 Hyprland -> 标准名
        self._key_map = {
            'return': 'return',
            'enter': 'return',
            'ctrl': 'CONTROL_L',
            'alt': 'ALT_L',
            # ... 扩展映射
        }

    def initialize(self):
        runtime = os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')
        sig = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
        if not sig:
            raise NotImplementedError('Hyprland environment not detected')
        self._socket_path = f'{runtime}/hypr/{sig}/.socket.sock'

    def _send_command(self, cmd: str) -> str:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(self._socket_path)
                s.send(cmd.encode())
                return s.recv(4096).decode()
        except Exception as e:
            raise IOError(f'Hyprland IPC error: {e}')

    def move_to(self, pos: Point, screen_id: Optional[int] = None):
        if not self._caps.absolute_move:
            raise NotImplementedError
        # Hyprland 使用全局坐标，无需处理 screen_id 转换
        self._send_command(f'dispatch movecursor {pos.x} {pos.y}')

    def move_rel(self, dx: int, dy: int):
        # Hyprland 没有原生相对 move，通过查询当前位置计算
        # 实际生产代码应缓存位置或解析 hyprctl 输出
        raise NotImplementedError('Hyprland prefers absolute coordinates')

    def btn_press(self, button: int):
        btn_map = {
            MouseButton.LEFT: 'mouse:272',
            MouseButton.RIGHT: 'mouse:273',
            MouseButton.MIDDLE: 'mouse:274',
        }
        hypr_btn = btn_map.get(button, 'mouse:272')
        self._send_command(f'dispatch sendshortcut , {hypr_btn}')  # 模拟按键

    def btn_release(self, button: int):
        btn_map = {
            MouseButton.LEFT: 'mouse:272',
            MouseButton.RIGHT: 'mouse:273',
            MouseButton.MIDDLE: 'mouse:274',
        }
        hypr_btn = btn_map.get(button, 'mouse:272')
        self._send_command(f'dispatch sendshortcut , {hypr_btn}')  # 模拟按键

    def press(self, key: str, modifiers: List[InputModifier] = None):
        mod_str = self._translate_mods(modifiers)
        mapped = self._key_map.get(key.lower(), key)
        self._send_command(f'dispatch sendshortcut {mod_str}, {mapped}')

    def release(self, key: str) -> None:
        pass

    def _translate_mods(self, mods: List[InputModifier]) -> str:
        # Hyprland 格式: SUPER_SHIFT_CTRL
        mapping = {
            InputModifier.CTRL: 'CONTROL',
            InputModifier.ALT: 'ALT',
            InputModifier.SHIFT: 'SHIFT',
            InputModifier.META: 'SUPER',
        }
        return '_'.join(mapping[m] for m in mods) if mods else ''

    def cleanup(self):
        pass  # Unix socket 无需显式关闭

    def btn_down(self, button) -> None:
        pass

    def scroll(self, dx: int, dy: int) -> None:
        pass
