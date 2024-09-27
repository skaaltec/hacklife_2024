from dataclasses import dataclass
from typing import Callable, List, Any, Union


@dataclass
class Characteristic:
    name: str
    uuid: str
    timeout: Union[None, float]
    decoder: Callable[[bytearray], List[List[Any]]]
    column_headers: List[str]