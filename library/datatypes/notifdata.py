from dataclasses import dataclass
from typing import Any, List
from .characteristic import Characteristic


@dataclass
class NotifData:
    device_adr: str
    device_name_repr: str
    characteristic: Characteristic
    data: List[List[Any]]