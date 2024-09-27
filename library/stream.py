import math
import asyncio
import logging
import numpy as np
from typing import Dict
from bleak import BLEDevice
from collections import deque
from PySide6.QtCore import QObject, Signal
from .consumermanager import ConsumerManager
from .connectionmanager import ConnectionManager
from .csvlogger import CSVLogger
from .datatypes import Configuration


class Stream(QObject):
    """This class is used to handle the data stream from the IMU devices"""
    new_data = Signal(str, arguments=['device_name'])
    
    def __init__(self, config: Configuration, halt_event: asyncio.Event, output_queues: Dict[str, deque]): 
        super().__init__()
        self.log = logging.getLogger('log')
        
        self.config = config
        self.halt_event = halt_event
        self.output_queues = output_queues
        
        self.devices = {}   # type: Dict[str, BLEDevice]
        self.consumer_manager = None
        self.connection_manager = None
        self.consumer_manager_task = None
        self.connection_manager_task = None
        
        acc_fs = 4
        gyro_fs = 1000
        gyro_scaling = 2**-15 * 1.13 * math.pi / 180 * gyro_fs
        acc_scaling = 2**-15 * 9.81 * acc_fs
        self.scaling_factors = np.array([
            1,                  # System timestamp [s]
            1e-3,               # IMU timestamp [s]
            gyro_scaling,       # gyro_x [rad/s]
            gyro_scaling,       # gyro_y [rad/s]
            gyro_scaling,       # gyro_z [rad/s]
            acc_scaling,        # acc_x [m/s^2]
            acc_scaling,        # acc_y [m/s^2]
            acc_scaling,        # acc_z [m/s^2]
            1, 1, 1, 1,         # q_x, q_y, q_z, q_w
            1, 1, 1             # mag_x, mag_y, mag_z
        ])

    def setup_stream(self, checked_devices, data_path=None):
        self.log.info("Setting up IMU data stream")
        self.consumer_manager = ConsumerManager(self.config, self.halt_event)
        
        if self.config.output_csv:
            self.log.info("Streaming data to CSV")
            consumer = CSVLogger(self.config, self.halt_event, data_path=data_path)
            self.consumer_manager.add_consumer(consumer)
            
        for device_name in checked_devices:          
            # Set up device and add to list
            device = checked_devices[device_name][0]
            self.output_queues[device_name] = deque(maxlen=self.config.buffer_size)
            self.devices[device_name] = device
            self.log.info(f"Added device to stream: {device_name}")
        
        # Create connection manager object to handle all active connections
        self.connection_manager = ConnectionManager(self.config, self.halt_event, self.devices, self.consumer_manager.input_queue, self.handle_new_data)
        self.connection_manager.connect_state.connect(lambda d, s: checked_devices[d][1].on() if s else checked_devices[d][1].off())

    def start(self, checked_devices, data_path=None):
        # Setup the stream object with consumers and devices
        self.setup_stream(checked_devices, data_path=data_path)
        
        # Start the connection and consumer manager tasks
        self.consumer_manager_task = asyncio.create_task(self.consumer_manager.run(), name='Consumer Manager Task')
        self.connection_manager_task = asyncio.create_task(self.connection_manager.run(), name='Connection Manager Task')

    async def stop(self):
        # Wait for all running tasks
        if self.consumer_manager_task or self.connection_manager_task:
            await asyncio.gather(self.consumer_manager_task, self.connection_manager_task)
            self.log.info("IMU data stream stopped")
        self.consumer_manager_task = None
        self.connection_manager_task = None
        
        # Reset attributes
        self.devices = {}
        self.consumer_manager = None
        self.connection_manager = None

    def handle_new_data(self, adr, name, data):
        # Pass new data to the data processor
        if name in self.output_queues:
            try:
                # Apply unit conversions to the elements in each tuple
                data = np.asarray(data) * self.scaling_factors
                
                # Place data in the appropriate output queue
                self.output_queues[name].append(data)
                self.new_data.emit(name)
                
            except Exception as e:
                self.log.error(f"Error handling incoming data: {e}")
        else:
            logging.warning(f"No buffer initialized for device {name} ({adr})")
