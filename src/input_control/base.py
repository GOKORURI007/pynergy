from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Point:
    x: int
    y: int


class BackendCapabilities:
    """声明后端能力，用于运行时检查"""

    def __init__(
        self,
        absolute_move: bool = False,
        relative_move: bool = True,
        scroll: bool = True,
        keyboard: bool = True,
    ):
        self.absolute_move = absolute_move
        self.relative_move = relative_move
        self.scroll = scroll
        self.keyboard = keyboard


class BaseBackend(ABC):
    def __init__(self, config: dict):
        self.config = config
        self._caps = BackendCapabilities()

    @property
    def capabilities(self) -> BackendCapabilities:
        return self._caps

    @abstractmethod
    def initialize(self) -> None:
        """初始化连接/句柄"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """释放资源"""
        pass


class MouseBackend(BaseBackend):
    @abstractmethod
    def move_to(self, pos: Point, screen_id: Optional[int] = None) -> None:
        """绝对定位。screen_id 用于多显示器指定"""
        raise NotImplementedError('Absolute positioning not supported')

    @abstractmethod
    def move_rel(self, dx: int, dy: int) -> None:
        """相对移动"""
        pass

    @abstractmethod
    def btn_press(self, button) -> None:
        """duration_ms > 0 时模拟按住"""
        pass

    @abstractmethod
    def btn_down(self, button) -> None:
        """duration_ms > 0 时模拟按住"""
        pass

    @abstractmethod
    def scroll(self, dx: int, dy: int) -> None:
        pass


class KeyboardBackend(BaseBackend):
    @abstractmethod
    def press(self, key: str, modifiers: List[int] = None) -> None:
        """key: 标准化名称如 'a', 'enter', 'f1'"""
        pass

    @abstractmethod
    def release(self, key: str) -> None:
        pass
