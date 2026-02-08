import struct
from dataclasses import dataclass, fields
from typing import Annotated, Literal, TypeAlias, get_args, get_origin, get_type_hints

from src.protocol.protocol_types import MsgType

OpCode: TypeAlias = Literal['FIX_VAL', 'FIX_STR', 'VAR_STR']
InstructionType: TypeAlias = list[tuple[OpCode, int, str]]


@dataclass(slots=True)
class MsgBase:
    """消息基类"""

    _INSTRUCTIONS = None
    _FORMAT = ''
    CODE = ''

    def __init_subclass__(cls, **kwargs):
        # 防止 dataclass(slots=True) 重建类时重复执行
        if '_format_initialized' in cls.__dict__:
            return
        # --- compile format ---
        hints = get_type_hints(cls, include_extras=True)

        fmt_parts: list[str] = ['>']
        instructions: InstructionType = []
        for field_name, hint in hints.items():
            print(f'Name: {field_name}, Hint: {hint}, Origin: {get_origin(hint)}')
            if field_name.startswith('_') or field_name == 'CODE':
                continue

            if get_origin(hint) is Annotated:
                metadata = get_args(hint)
                struct_char = metadata[1]

                # 判定操作类型
                op: OpCode
                if struct_char == 'Is':
                    op = 'VAR_STR'
                    size = 4  # 仅长度前缀的大小
                elif 's' in struct_char:
                    op = 'FIX_STR'
                    size = struct.calcsize(struct_char)
                else:
                    op = 'FIX_VAL'
                    size = struct.calcsize(struct_char)

                fmt_parts.append(struct_char)
                instructions.append((op, size, struct_char))

            else:
                raise TypeError(
                    f'Field {field_name} must be annotated with Annotated (such as Int32, UInt16). '
                    f'Got {type(hint)} instead.'
                )

        cls._FORMAT = ''.join(fmt_parts)
        cls._INSTRUCTIONS = instructions
        cls._format_initialized = True

    @classmethod
    def unpack(cls, data: bytes):
        offset = 0
        args = []
        for op, size, fmt in cls._INSTRUCTIONS:
            if op == 'FIX_VAL':
                # 直接解包数值
                val = struct.unpack_from(f'>{fmt}', data, offset)[0]
                args.append(val)
                offset += size
            elif op == 'FIX_STR':
                # 解包固定长度字符串并 strip
                val = struct.unpack_from(f'>{fmt}', data, offset)[0]
                args.append(val.decode('utf-8').rstrip('\x00'))
                offset += size
            elif op == 'VAR_STR':
                # 解包变长字符串：先读 4 字节长度
                length = struct.unpack_from('>I', data, offset)[0]
                offset += size
                val = data[offset: offset + length].decode('utf-8')
                args.append(val)
                offset += length
        return cls(*args)  # type: ignore[call-arg]

    def pack(self) -> bytes:
        """根据类定义的字段顺序和 _INSTRUCTIONS 动态打包"""
        result = bytearray()
        result.extend(struct.pack(f'>{len(self.CODE)}s', self.CODE))
        # 获取 dataclass 定义的所有字段的值 (按定义顺序)
        data_fields = [f for f in fields(self) if not f.name.startswith('_') and f.name != 'CODE']

        # 将指令与字段值一一对应进行处理
        for (op, size, fmt), field_def in zip(self._INSTRUCTIONS, data_fields):
            val = getattr(self, field_def.name)

            if op == 'FIX_VAL':
                # 处理数值 (I, H, B 等)
                result.extend(struct.pack(f'>{fmt}', val))

            elif op == 'FIX_STR':
                # 处理固定长度字符串，确保编码为 bytes 并填充 / 截断
                s_bytes = val.encode('utf-8')
                # struct.pack 会自动根据 fmt ( 如 "7s") 处理截断和补 \x00
                result.extend(struct.pack(f'>{fmt}', s_bytes))

            elif op == 'VAR_STR':
                # 处理变长字符串 (Synergy 风格: Length + Data)
                s_bytes = val.encode('utf-8')
                length = len(s_bytes)
                # 先打入 4 字节长度，再打入实际内容
                result.extend(struct.pack('>I', length))
                result.extend(s_bytes)

        return bytes(result)


class Registry:
    _MAPPING: dict[MsgType, MsgBase] = {}

    @classmethod
    def register(cls, msg_code: MsgType):
        def wrapper(subclass):
            cls._MAPPING[msg_code] = subclass
            subclass.CODE = msg_code
            return subclass

        return wrapper

    @classmethod
    def get_class(cls, msg_code: MsgType) -> MsgBase:
        return cls._MAPPING.get(msg_code)
