import time
import asyncio
import logging
import functools
from typing import Dict, Union, Callable
from bleak import BleakClient
from bleak.exc import BleakDeviceNotFoundError, BleakDBusError, BleakError
from .datatypes import Characteristic, Configuration, ConnectionState, NotifData


class ActiveConnectionException(Exception): ...


class ActiveConnection:
    def __init__(self, adr: str, name: str,  config: Configuration, halt_event: asyncio.Event, output_queue: asyncio.Queue, callback: Callable) -> None:
        self.log = logging.getLogger('log')
        
        self.adr = adr
        self.name = name
        self.halt_event = halt_event
        self.config = config
        self.output_queue = output_queue
        self.data_received_callback = callback
        
        self.state = ConnectionState.CONNECTING
        self.did_disconnect = False
        self.initial_connection_time = None

    async def run(self) -> None:
        # Reset initial parameters
        self.state = ConnectionState.CONNECTING
        self.did_disconnect = False
        self.initial_connection_time = None
        self.last_notif = {c.uuid: None for c in self.config.characteristics}  # type: Dict[str, Union[None, int]]
        self.con = BleakClient(
            self.adr,
            timeout=self.config.connect_timeout,
            disconnected_callback=self._disconnected_callback,
            winrt={"use_cached_services": False}
        )
        
        try:
            # Ensure there was no disconnect before this connection got a chance to run:
            if self.did_disconnect:
                raise ActiveConnectionException()

            # Connect:
            await self._connect(self.con)
            self.initial_connection_time = time.monotonic_ns()
            self.state = ConnectionState.CONNECTED

            while not self.halt_event.is_set():
                # Check disconnect flag (set by disconnect callback or manual disconnect)
                if self.did_disconnect:
                    self.log.warning(f'Connection to {self.name} lost!')
                    raise ActiveConnectionException()

                await self._check_for_timeout()
                await asyncio.sleep(0.2)
        except TimeoutError:
            self.state = ConnectionState.TIMEOUT
        except ActiveConnectionException:
            self.state = ConnectionState.DISCONNECTED
        except Exception as e:
            self.log.error(f'Connection to {self.name} encountered an exception: {e}')
            self.did_disconnect = True
            self.state = ConnectionState.DISCONNECTED
        else:
            await self._do_disconnect()
            self.state = ConnectionState.DISCONNECTED

    async def _connect(self, con: BleakClient) -> None:
        # Note: According to the docs, Bleak generates exceptions if connecting fails under linux,
        # while only returning false on other platforms.
        # This should handle all cases.
        try:
            await asyncio.wait_for(con.connect(), timeout=self.config.connect_timeout)
        except asyncio.TimeoutError:
            self.log.warning(f'Failed to connect to {self.name}: Timeout')
            raise TimeoutError()
        except asyncio.CancelledError:
            self.log.warning(f'Failed to connect to {self.name}: Cancelled')
            raise ActiveConnectionException()
        except BleakDeviceNotFoundError:
            self.log.warning(f'Failed to connect to {self.name}: Device not found')
            raise ActiveConnectionException()
        except BleakDBusError:
            self.log.warning(f'Failed to connect to {self.name}: DBus Error')
            raise ActiveConnectionException()
        except OSError:
            self.log.warning(f'Failed to connect to {self.name}: OSError')
            raise ActiveConnectionException()
        except BleakError as e:
            self.log.warning(f'Failed to connect to {self.name}: {e}')
            raise ActiveConnectionException()
        else:
            self.log.info(f'Established connection to {self.name}')

        for char, data in self.config.ctrl_characteristics:
            await con.write_gatt_char(char, data)

        # Enable notifications for all characteristics:
        for char in self.config.characteristics:
            # Generate a wrapper around the callback function to pass characteristic along.
            # Bleak does not seem to offer a documented interface on how the 'dev' int
            # passed to the callback can be used to identify which characteristic caused the
            # notification
            callback_wrapper = functools.partial(self._notif_callback, char=char)
            await con.start_notify(char.uuid, callback_wrapper)
        self.log.debug(f'Enabled notifications for all characteristics for {self.name}')

    async def _check_for_timeout(self) -> None:
        for char in self.config.characteristics:
            if char.timeout is not None:
                last_notif = self.last_notif[char.uuid]

                if last_notif is not None:
                    # Check if normal timeout expired
                    timeout = char.timeout
                    has_been = (time.monotonic_ns() - last_notif)/1e9

                    if has_been > timeout:
                        self.log.warning(f'{self.name}: Timeout for characteristic {char.name} expired, disconnecting..')
                        self.state = ConnectionState.TIMEOUT
                        await self._do_disconnect()
                        raise ActiveConnectionException()

                elif self.config.initial_characteristic_timeout is not None:
                    if self.initial_connection_time is None:
                        raise Exception("Implementation error")

                    # Check if initial timeout expired
                    timeout = char.timeout + self.config.initial_characteristic_timeout
                    has_been = (time.monotonic_ns() - self.initial_connection_time) / 1e9

                    if has_been > timeout:
                        self.log.warning(f'{self.name}: Never received a notification for {char.name}, disconnecting...')
                        self.state = ConnectionState.TIMEOUT
                        await self._do_disconnect()

    def _disconnected_callback(self, _) -> None:
        self.did_disconnect = True

    def _notif_callback(self, dev: int, data: bytearray, char: Characteristic) -> None:
        _ = dev

        self.last_notif[char.uuid] = time.monotonic_ns()

        try:
            # Decode and package data:
            decoded_data = char.decoder(data)
            result = NotifData(self.adr, self.name, char, decoded_data)
            
            # Notify Stream class if callback function is set
            if self.data_received_callback:
                self.data_received_callback(self.adr, self.name, result.data)
            
            # Put data into file output queue
            try:
                self.output_queue.put_nowait(result)
            except asyncio.QueueFull:
                self.self.log.error(f"{self.name} failed to put data into queue")
                
        except Exception as e:
            self.log.error(f"Decoder for {char.name} raised an exception: {e}")
    
    async def _do_disconnect(self) -> None:
        if self.con is not None:
            try:
                did_disconnect = await asyncio.wait_for(self.con.disconnect(), timeout=5)
                if did_disconnect:
                    self.log.info(f'Disconnected from {self.name}')
                else:
                    self.log.warning(f'Failed to disconnect from {self.name}: Bleak Error')
            except BleakDBusError:
                self.log.warning(f'Failed to disconnect from {self.name}: DBus Error')
            except BleakError as e:
                self.log.warning(f'Failed to disconnect from {self.name}: {e}')
            except asyncio.TimeoutError:
                self.log.warning(f'Failed to disconnect from {self.name}: Timeout')
            except OSError:
                self.log.warning(f'Failed to disconnect from {self.name}: OSError')
            finally:
                self.did_disconnect = True

    def active_time_str(self) -> str:
        if self.initial_connection_time is None:
            return "xx:xx:xx"
        else:
            active_s = (time.monotonic_ns() - self.initial_connection_time) / 1e9
            h = active_s // (3600)
            active_s %= (3600)
            min = active_s // 60
            active_s %= 60
            s = active_s // 1
            return "%02i:%02i:%02i" % (h, min, s)
