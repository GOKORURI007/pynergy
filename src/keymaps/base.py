from pynput.keyboard import Key

try:
    import evdev
except ImportError:
    evdev = None
    ECODE_TO_HID_BTN = {}
    ECODE_TO_HID_KEY = {}

if evdev:
    from evdev import ecodes as e

    ECODE_TO_HID_BTN = {
        # --- Mouse (BTN_LEFT=272, etc.) ---
        e.BTN_LEFT: 0x01,
        e.BTN_RIGHT: 0x02,
        e.BTN_MIDDLE: 0x03,
        e.BTN_SIDE: 0x04,  # X1 / Back
        e.BTN_EXTRA: 0x05,  # X2 / Forward
    }

    HID_TO_ECODE_BTN = {v: k for k, v in ECODE_TO_HID_BTN.items()}

    ECODE_TO_HID_KEY = {
        # --- Modifiers ---
        e.KEY_LEFTCTRL: 0xE0,
        e.KEY_LEFTSHIFT: 0xE1,
        e.KEY_LEFTALT: 0xE2,
        e.KEY_LEFTMETA: 0xE3,  # GUI / Win / Super
        e.KEY_RIGHTCTRL: 0xE4,
        e.KEY_RIGHTSHIFT: 0xE5,
        e.KEY_RIGHTALT: 0xE6,
        e.KEY_RIGHTMETA: 0xE7,
        # --- Modify & Control ---
        e.KEY_INSERT: 0x49,
        e.KEY_HOME: 0x4A,
        e.KEY_PAGEUP: 0x4B,
        e.KEY_DELETE: 0x4C,
        e.KEY_END: 0x4D,
        e.KEY_PAGEDOWN: 0x4E,
        e.KEY_SYSRQ: 0x46,  # PrintScreen
        e.KEY_SCROLLLOCK: 0x47,
        e.KEY_PAUSE: 0x48,
        # --- Basic Control ---
        e.KEY_BACKSPACE: 0x2A,
        e.KEY_TAB: 0x2B,
        e.KEY_ENTER: 0x28,
        e.KEY_ESC: 0x29,
        e.KEY_SPACE: 0x2C,
        e.KEY_LEFT: 0x50,
        e.KEY_UP: 0x52,
        e.KEY_RIGHT: 0x4F,
        e.KEY_DOWN: 0x51,
        e.KEY_COMPOSE: 0x76,  # Menu / App
        # --- Special Character ---
        e.KEY_MINUS: 0x2D,
        e.KEY_EQUAL: 0x2E,
        e.KEY_LEFTBRACE: 0x2F,
        e.KEY_RIGHTBRACE: 0x30,
        e.KEY_BACKSLASH: 0x31,
        e.KEY_SEMICOLON: 0x33,
        e.KEY_APOSTROPHE: 0x34,
        e.KEY_GRAVE: 0x35,
        e.KEY_COMMA: 0x36,
        e.KEY_DOT: 0x37,
        e.KEY_SLASH: 0x38,
        e.KEY_CAPSLOCK: 0x39,
        e.KEY_NUMLOCK: 0x53,
        # --- NumPad ---
        e.KEY_KP1: 0x59,
        e.KEY_KP2: 0x5A,
        e.KEY_KP3: 0x5B,
        e.KEY_KP4: 0x5C,
        e.KEY_KP5: 0x5D,
        e.KEY_KP6: 0x5E,
        e.KEY_KP7: 0x5F,
        e.KEY_KP8: 0x60,
        e.KEY_KP9: 0x61,
        e.KEY_KP0: 0x62,
        e.KEY_KPDOT: 0x63,
        e.KEY_KPSLASH: 0x54,
        e.KEY_KPASTERISK: 0x55,
        e.KEY_KPMINUS: 0x56,
        e.KEY_KPPLUS: 0x57,
        e.KEY_KPENTER: 0x58,
        # --- Alphabet (KEY_A=30 -> 0x04) ---
        # Linux evdev 的字母分布不像 VK 那样连续，建议显式映射或使用 e.KEY_A 引用
        **{getattr(e, f'KEY_{c}'): (ord(c) - ord('A') + 0x04) for c in
           'ABCDEFGHIJKLMNOPQRSTUVWXYZ'},
        # --- Digits (KEY_1=2 -> 0x1E) ---
        **{getattr(e, f'KEY_{i}'): (0x1E + i - 1) for i in range(1, 10)},
        e.KEY_0: 0x27,
        # --- F1~12 ---
        **{getattr(e, f'KEY_F{i}'): (0x3A + i - 1) for i in range(1, 13)},
    }

VK_TO_HID_BTN = {
    # --- Mouse ---
    'left': 0x01,  # left btn
    'right': 0x02,  # right btn
    'middle': 0x03,  # middle btn
    # custom
    'x1': 0x04,  # x1 btn
    'x2': 0x05,  # x2 btn
}

VK_TO_HID_KEY = {
    # --- Modifiers ---
    Key.ctrl.value.vk: 0xE0,  # Control
    Key.ctrl_l.value.vk: 0xE0,  # Left Control
    Key.ctrl_r.value.vk: 0xE4,  # Right Control
    Key.shift.value.vk: 0xE1,  # Shift -> HID distinguishes L/R
    Key.shift_l.value.vk: 0xE1,  # Left Shift
    Key.shift_r.value.vk: 0xE5,  # Right Shift
    Key.alt.value.vk: 0xE2,  # Alt
    Key.alt_l.value.vk: 0xE2,  # Left Alt
    Key.alt_r.value.vk: 0xE6,  # Right Alt
    Key.cmd.value.vk: 0xE3,  # Left GUI (Win) / Super / cmd
    Key.cmd_l.value.vk: 0xE3,  # Left GUI (Win) / Super / cmd
    Key.cmd_r.value.vk: 0xE7,  # Right GUI (Win) / Super / cmd
    # --- Modify & Control ---
    Key.insert.value.vk: 0x49,  # Insert
    Key.home.value.vk: 0x4A,  # Home
    Key.page_up.value.vk: 0x4B,  # PageUp
    Key.delete.value.vk: 0x4C,  # Delete Forward
    Key.end.value.vk: 0x4D,  # End
    Key.page_down.value.vk: 0x4E,  # PageDown
    Key.print_screen.value.vk: 0x46,  # PrintScreen
    Key.scroll_lock.value.vk: 0x47,  # Scroll Lock
    Key.pause.value.vk: 0x48,  # Pause/Break (PB)
    # --- Basic Control ---
    Key.backspace.value.vk: 0x2A,  # Backspace
    Key.tab.value.vk: 0x2B,  # Tab
    Key.enter.value.vk: 0x28,  # Enter
    Key.esc.value.vk: 0x29,  # Escape
    Key.space.value.vk: 0x2C,  # Space
    Key.left.value.vk: 0x50,  # Left Arrow
    Key.up.value.vk: 0x52,  # Up Arrow
    Key.right.value.vk: 0x4F,  # Right Arrow
    Key.down.value.vk: 0x51,  # Down Arrow
    Key.menu.value.vk: 0x76,  # Menu
    # --- Special Character ---
    0xBD: 0x2D,  # KEY_MINUS -
    0xBB: 0x2E,  # KEY_EQUAL =
    0xDB: 0x2F,  # KEY_LEFTBRACE [
    0xDD: 0x30,  # KEY_RIGHTBRACE ]
    0xDC: 0x31,  # KEY_BACKSLASH \
    0xBA: 0x33,  # KEY_SEMICOLON ;
    0xDE: 0x34,  # KEY_APOSTROPHE '
    0xC0: 0x35,  # KEY_GRAVE ~
    0xBC: 0x36,  # KEY_COMMA ,
    0xBE: 0x37,  # KEY_DOT .
    0xBF: 0x38,  # KEY_SLASH /
    0x14: 0x39,  # KEY_CAPSLOCK
    0x90: 0x53,  # KEY_NUMLOCK
    # --- NumPad ---
    # Numpad 1-9: VK 0x61-0x69 -> HID 0x59-0x61
    **{vk: (vk - 0x61 + 0x59) for vk in range(0x61, 0x6A)},
    0x60: 0x62,  # Numpad 0: VK 0x60 -> HID 0x62
    0x6E: 0x63,  # Numpad . (Decimal): VK 0x6E -> HID 0x63
    0x6F: 0x54,  # Numpad / (Divide): VK 0x6F -> HID 0x54
    0x6A: 0x55,  # Numpad * (Multiply): VK 0x6A -> HID 0x55
    0x6D: 0x56,  # Numpad - (Subtract): VK 0x6D -> HID 0x56
    0x6B: 0x57,  # Numpad + (Add): VK 0x6B -> HID 0x57
    # Note: The keypad Enter is usually also 0x0D on Windows VK,
    # but in HID it has a separate ID 0x58 (Keypad ENTER).
    # map 0x58 if pynput can distinguish expansion keys.
    # --- Alphabet ---
    # A-Z (VK 0x41 - 0x5A) -> HID 0x04 - 0x1D
    **{vk: (vk - 0x41 + 0x04) for vk in range(0x41, 0x5B)},
    # --- digits ---
    # 1-0 (VK 0x31 - 0x39, 0x30) -> HID 0x1E - 0x27
    **{vk: (vk - 0x31 + 0x1E) for vk in range(0x31, 0x3A)},
    0x30: 0x27,
    # --- F1~12 ---
    **{(0x70 + i): (0x3A + i) for i in range(12)},
}
