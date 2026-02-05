from .ecode_map import hid_to_ecode
from .hid_map import hid_to_name, name_to_hid
from .vk_map import hid_to_vk


class HID:
    def __init__(self, name: str | None = None, code: int | None = None):

        if name is not None and code is None:
            code = name_to_hid(name)

        if code is not None and name is None:
            name = hid_to_name(code)

        self.name = name
        self.code = code

    def to_vk(self):
        return hid_to_vk(self.code)

    def to_ecode(self):
        return hid_to_ecode(self.code)

    @classmethod
    def from_name(cls, name: str, **kwargs):
        return cls(name=name, **kwargs)

    @classmethod
    def from_code(cls, code: int, **kwargs):
        return cls(code=code, **kwargs)
