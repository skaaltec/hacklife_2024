import re
import time
import asyncio
import logging
from typing import Dict
from bleak import BleakScanner
from .datatypes import Configuration, SeenDevice, SeenDeviceState


class Scanner:
    def __init__(self, config: Configuration, halt_event: asyncio.Event):
        self.config = config
        self.halt_event = halt_event
        self.log= logging.getLogger('log')
        self.name_regexes = [re.compile(r) for r in config.name_regexes]
        self.seen_devices = {}  # type: Dict[str, SeenDevice]

    async def scan_for_devices(self):
        # Start scan and wait for it to finish
        self.log.info("Scanning nearby motion trackers...")
        await self.run()
        # Update scanned devices
        self.scanned_devices = [device for device in self.seen_devices.values() if device.state==SeenDeviceState.RECENTLY_SEEN]
        self.log.info(f"Scanned motion trackers: {[f'{d.get_id()}({d.adr})' for d in self.scanned_devices]}")
        
    async def run(self):
        time_start = time.time()
        try:
            while not self.halt_event.is_set() and (time.time()-time_start < self.config.scan_duration):
                try:
                    # Discover devices
                    devices_and_adv_data = await BleakScanner.discover(timeout=self.config.scan_timeout, return_adv=True)
                    # Update list of seen devices:
                    t = time.monotonic_ns()
                    self._update_seen_devices(devices_and_adv_data, t)
                    # Cooldown
                    await asyncio.sleep(self.config.scan_cooldown)
                except asyncio.TimeoutError:
                    self.log.warning('Scanner timed out')
                except RuntimeError as e:
                    self.log.warning(f'Scanner did not complete scan')
                    break
        except Exception as e:
            self.log.error(f'Scanner encountered an exception: {e}')

    def _update_seen_devices(self, devices_and_adv_data: dict, t: int):
        for address in devices_and_adv_data:
            adr = self.config.normalise(address)
            scanned_dev = devices_and_adv_data[address][0]
            scanned_adv = devices_and_adv_data[address][1]
            if adr in self.seen_devices:
                # Known device, update information:
                dev = self.seen_devices[adr]
                dev.last_seen = t
                dev.name = scanned_dev.name
                dev.rssi = scanned_adv.rssi
                dev.state = SeenDeviceState.RECENTLY_SEEN
            else:
                # Unknown device, check if name matches:
                for regex in self.name_regexes:
                    if(scanned_dev.name is None):
                        continue
                    if re.match(regex, scanned_dev.name):
                        # It does, add the new device:
                        new_dev = SeenDevice(
                            adr=adr,
                            alias=self.config.device_aliases.get(adr, None),
                            state=SeenDeviceState.RECENTLY_SEEN,
                            name=scanned_dev.name,
                            last_seen=t,
                            rssi=scanned_adv.rssi,
                        )
                        self.seen_devices[adr] = new_dev
                        self.log.info(f"New device found: {new_dev.get_id()}({new_dev.adr})")
            # Check for seen-recently timeouts:
            for dev in self.seen_devices.values():
                if dev.state == SeenDeviceState.RECENTLY_SEEN:
                    if dev.last_seen is not None:
                        has_been = (time.monotonic_ns() - dev.last_seen)/1e9
                        if has_been > self.config.seen_timeout:
                            dev.state = SeenDeviceState.NOT_SEEN
        