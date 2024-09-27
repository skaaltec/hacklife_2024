import enum


@enum.unique
class ConnectionState(enum.Enum):
    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTED = 2
    TIMEOUT = 3

    def __str__(self):
        return super().__str__().split('.')[1]