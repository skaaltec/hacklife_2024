import enum
from typing import Union
from dataclasses import dataclass


@enum.unique
class SeenDeviceState(enum.Enum):
    NOT_SEEN = 0
    RECENTLY_SEEN = 1

    def __str__(self):
        return super().__str__().split('.')[1].replace('_', ' ')


@dataclass
class SeenDevice:
    adr: str
    alias: Union[str, None]
    state: SeenDeviceState
    name: Union[str, None]
    last_seen: Union[int, None]
    rssi: Union[int, None]

    def get_id(self) -> str:
        if self.alias is not None:
            return self.alias
        elif self.name is not None:
            return self.name
        else:
            return self.adr