import asyncio
from typing import Union
from dataclasses import dataclass
from ..activeconnection import ActiveConnection
from .connectionstate import ConnectionState
from .seendevice import SeenDevice, SeenDeviceState


@dataclass
class ManagedConnection:
    device: SeenDevice
    active_connection: Union[None, ActiveConnection]
    last_connection_attempt: Union[int, None]
    task: Union[None, asyncio.Task]

    def state(self) -> ConnectionState:
        if self.active_connection is None:
            return ConnectionState.DISCONNECTED
        else:
            return self.active_connection.state

    def ready_to_connect(self) -> bool:
        if self.state() == ConnectionState.DISCONNECTED or self.state() == ConnectionState.TIMEOUT:
            if self.device.state == SeenDeviceState.RECENTLY_SEEN:
                return True
        return False

    # 'Less than' comparison for managed connections.
    # Used to find connection that has not attempted to connect for
    # the longest time.
    def __lt__(self, other):
        if self.last_connection_attempt is None:
            return True
        elif other.last_connection_attempt is None:
            return False
        else:
            return self.last_connection_attempt < other.last_connection_attempt