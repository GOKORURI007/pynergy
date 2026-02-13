import socket
from enum import Enum
from typing import Protocol

from ..device import VirtualDevice
from ..protocol import MsgBase


class ClientState(Enum):
    """客户端状态枚举"""

    DISCONNECTED = 0
    CONNECTING = 1
    HANDSHAKE = 2
    CONNECTED = 3
    ACTIVE = 4


class ClientProtocol(Protocol):
    server: str
    port: int
    name: str

    sock: socket.socket | None
    state: ClientState
    _device: VirtualDevice | None
    running: bool
    last_x: int | None
    last_y: int | None
    pressed_keys: set[int]

    sock: socket.socket
    screen_width: int
    screen_height: int

    @property
    def device(self) -> VirtualDevice: ...

    def connect(self) -> None: ...

    def run(self) -> None: ...

    def sync_modifiers(self, modifiers: int) -> None: ...

    def release_all_keys(self) -> None: ...

    def abs_to_rel(self, x: int, y: int) -> tuple[int, int]: ...

    def write_mouse_abs(self, x: int, y: int) -> None: ...


class HandlerMethod(Protocol):
    def __call__(self, msg: MsgBase) -> None: ...
