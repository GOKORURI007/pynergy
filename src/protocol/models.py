from dataclasses import dataclass


@dataclass(slots=True)
class HelloMsg:
    protocol_name: str
    major: int
    minor: int


@dataclass(slots=True)
class HelloBackMsg:
    protocol_name: str
    major: int
    minor: int
    name: str


@dataclass(slots=True)
class CCLPMsg:
    """Clipboard grab notification"""
    identifier: str
    sequence: int


@dataclass(slots=True)
class CCloseMsg:
    """Close connection command"""


@dataclass(slots=True)
class CINNMsg:
    """Enter screen command"""
    entry_x: int
    entry_y: int
    sequence_number: int
    mod_key_mask: int


@dataclass(slots=True)
class CIAKMsg:
    """Screen information acknowledgment"""


@dataclass(slots=True)
class CALVMsg:
    """Keep-alive message"""


@dataclass(slots=True)
class COUTMsg:
    """Leave screen command"""


@dataclass(slots=True)
class CNOPMsg:
    """No operation command"""


@dataclass(slots=True)
class CROPMsg:
    """Reset options command"""


@dataclass(slots=True)
class CSECMsg:
    """Screensaver state change"""
    state: bool


@dataclass(slots=True)
class DKDNMsg:
    """Key press event"""
    key_id: int
    mod_key_mask: int
    key_button: int


@dataclass(slots=True)
class DKDLMsg:
    """Key press with language code"""
    key_id: int
    mod_key_mask: int
    key_button: int
    language_code: str


@dataclass(slots=True)
class DKRPMsg:
    """Key auto-repeat event"""
    key_id: int
    mod_key_mask: int
    repeat_count: int
    key_button: int
    language_code: str


@dataclass(slots=True)
class DKUPMsg:
    """Key release event"""
    key_id: int
    mod_key_mask: int
    repeat_count: int
    key_button: int


@dataclass(slots=True)
class DMDNMsg:
    """Mouse press event"""
    button: int


@dataclass(slots=True)
class DMMVMsg:
    """Mouse move event"""
    x: int
    y: int


@dataclass(slots=True)
class DMRMMsg:
    """Relative mouse movement"""
    x_delta: int
    y_delta: int


@dataclass(slots=True)
class DMUPMsg:
    """Mouse release event"""
    button: int


@dataclass(slots=True)
class DMWMMsg:
    """Mouse wheel scroll event"""
    x_delta: int
    y_delta: int


@dataclass(slots=True)
class DCLPMsg:
    """Clipboard data transfer"""
    identifier: int
    sequence: int
    flag: bool
    data: str


@dataclass(slots=True)
class DINFMsg:
    """Client screen information"""
    left_edge_coord: int
    top_edge_coord: int
    screen_width: int
    screen_height: int
    warp_zone: int  # obsolete
    mouse_x: int
    mouse_y: int


@dataclass(slots=True)
class DSOPMsg:
    """Set client options"""
    options: dict[str, int]


@dataclass(slots=True)
class DDRGMsg:
    """Drag and drop information"""
    file_counts: int
    file_paths: list[str]


@dataclass(slots=True)
class DFTRMsg:
    """File transfer data"""
    mark: int
    data: str


@dataclass(slots=True)
class LSYNMsg:
    """Language synchronization"""
    lang_list: list[str]


@dataclass(slots=True)
class SECNMsg:
    """Secure input notification (macOS)"""
    app_name: str


@dataclass(slots=True)
class QINFMsg:
    """Query screen information"""


@dataclass(slots=True)
class EBADMsg:
    """Protocol violation"""


@dataclass(slots=True)
class EBSYMsg:
    """Client name already in use"""


@dataclass(slots=True)
class EICVMsg:
    """Incompatible protocol versions"""


@dataclass(slots=True)
class EUNKMsg:
    """Unknown client name"""
