import time
import asyncio
from abc import ABC, abstractmethod
from typing import Union


class Consumer(ABC):
    """Basic interface for a data consumer"""
    
    def __init__(self) -> None:
        self.halt_event = asyncio.Event
        self.input_queue = asyncio.Queue()
        self.last_full_queue_warning = None  # type: Union[int, None]

    @abstractmethod
    async def run(self) -> None: ...

    def should_queue_warn(self) -> bool:
        warn_timeout_ns = 60e9
        if self.last_full_queue_warning is None:
            return True
        else:
            return self.last_full_queue_warning + warn_timeout_ns < time.monotonic_ns()