import time
import logging
import asyncio
from typing import Dict, Union, Callable
from PySide6.QtCore import QObject, Signal
from .activeconnection import ActiveConnection
from .datatypes import Configuration, ManagedConnection, SeenDevice, ConnectionState


class ConnectionManager(QObject):
    # Global state signal
    connect_state = Signal(str, bool, arguments=['device_name', 'state'])
    
    def __init__(self, config: Configuration, halt_event: asyncio.Event, devices: Dict[str, SeenDevice], output_queue: asyncio.Queue, callback: Callable):
        super().__init__()
        self.log = logging.getLogger('log')
        self.config = config
        self.halt_event = halt_event
        self.devices = devices
        self.output_queue = output_queue
        self.callback = callback
        self.connections = {}  # type: Dict[str, ManagedConnection]

    async def run(self):
        self.log.info(f'Connection manager started')
        self.setup_connections()
        try:
            while not self.halt_event.is_set():
                self.manage_connections()
                await asyncio.sleep(self.config.manager_interval)
        except Exception as e:
            self.log.error(f'Connection manager encountered an exception: {e}')
            self.halt_event.set()
        finally:
            await asyncio.gather(*[c.task for c in self.connections.values() if c.task is not None])
            self.log.info('Connection manager shut down')

    def setup_connections(self):
        # Pickup new devices/updates
        for device in self.devices.values():
            if device.adr not in self.connections:
                con = ManagedConnection(
                    device=device,
                    active_connection=None,
                    last_connection_attempt=None,
                    task=None)
                self.connections[device.adr] = con

    def manage_connections(self):
        # Count active and connecting connections and manage connection status
        active_connection_count = 0
        connecting_connection_count = 0
        for con in self.connections.values():
            if con.task is None: continue
            device_name = con.device.get_id()
            if con.task.done():
                match con.state():
                    case ConnectionState.DISCONNECTED:
                        self.log.warning(f"Device {device_name} disconnected, attempting reconnect...")
                        self.connect_state.emit(device_name, False)
                    case ConnectionState.TIMEOUT:
                        self.connect_state.emit(device_name, False)
                        pass
            else:
                match con.state():
                    case ConnectionState.CONNECTED:
                        self.connect_state.emit(device_name, True)
                        active_connection_count += 1
                    case ConnectionState.CONNECTING:
                        active_connection_count += 1
                        connecting_connection_count += 1

        # If there is space for more connections, spawn one
        if active_connection_count < self.config.max_active_connections:
            if connecting_connection_count < self.config.max_simultaneous_connection_attempts:
                # First, find all possible connections
                possible_connections = [c for c in self.connections.values() if c.ready_to_connect()]
                if len(possible_connections) > 0:
                    # Prioritise connections that have never been connected, or whose
                    # last connection attempt lies further back
                    possible_connections.sort()
                    next_con = possible_connections[0]

                    # Attempt to connect to the next device
                    adr = next_con.device.adr
                    device_name = next_con.device.get_id()
                    self.log.info(f'Connecting to {device_name}...')
                    if next_con.active_connection is None:
                        next_con.active_connection = ActiveConnection(adr, device_name, self.config, self.halt_event, self.output_queue,self.callback)
                    next_con.last_connection_attempt = time.monotonic_ns()
                    task = asyncio.create_task(next_con.active_connection.run(), name=device_name)
                    next_con.task = task
