import logging
from dataclasses import dataclass
from typing import List, Dict, Tuple
from .characteristic import Characteristic


@dataclass
class Configuration:
    # Device settings:
    device_aliases: Dict[str, str]
    name_regexes: List[str]
    characteristics: List[Characteristic]

    # Configuration commands:
    ctrl_characteristics: List[Tuple[str, bytearray]]

    # Connection parameters:
    max_active_connections: int
    max_simultaneous_connection_attempts: int
    connect_timeout: float

    # Scanner parameters:
    scan_duration: float
    scan_timeout: float
    scan_cooldown: float
    seen_timeout: float
    initial_characteristic_timeout: float
    manager_interval: float

    # Output settings:
    buffer_size: int
    output_csv: bool
    output_folder: str

    def normalise(self, hex:str):
        """Produce consistent hex formatting to make comparisons easier"""
        return hex.replace('0x', '').strip().upper()

    def validate_and_normalise(self):
        """
        Validates the configuration provided by the user.
        Converts bluetooth addresses and characteristic UUIDs into a standard
        format.
        """

        # Get logger:
        log = logging.getLogger('log')

        # Normalise connect device addresses in list of aliases:
        self.device_aliases = {self.normalise(adr): alias for adr, alias in self.device_aliases.items()}

        # Normalise characteristic UUIDs:
        for char in self.characteristics:
            char.uuid = self.normalise(char.uuid)
        self.ctrl_characteristics = [(self.normalise(char[0]), char[1]) for char in self.ctrl_characteristics]
        
        # Check for duplicate aliases:
        # (Can cause problems, as they are used as a file name)
        seen_aliases = []
        for alias in self.device_aliases.values():
            if alias in seen_aliases:
                log.error('Duplicate device alias "{alias}"')
                exit(-1)
            seen_aliases.append(alias)

        # Check for duplicate characteristic names:
        # (Can cause problems, as they are used as a file name)
        seen_names = []
        for char in self.characteristics:
            if char.name in seen_names:
                log.error(f'Duplicate characteristic UUID "{char.name}"')
                exit(-1)
            seen_names.append(char.name)

        # Check for duplicate characteristic UUIDs:
        seen_uuids = []
        for char in self.characteristics:
            if char.uuid in seen_uuids:
                log.error(f'Duplicate characteristic UUID "{char.uuid}"')
                exit(-1)
            seen_uuids.append(char.uuid)

    def get_characteristic(self, uuid: str) -> Characteristic:
        for c in self.characteristics:
            if c.uuid == self.normalise(uuid):
                return c
        raise KeyError()
