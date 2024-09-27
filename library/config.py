from .decoders import decode_data
from .datatypes import Characteristic, Configuration

conf = Configuration(
    # ======================= Devices ============================
    # Device nicknames:
    # An (optional) alias to identify a given address by.
    # Used for status logging, and file names.
    # If provided, it has to be unique.
    device_aliases={
        "FB:4A:66:AC:08:01": "SmartVNS0",
        "C2:4D:BE:83:07:01": "SmartVNS1",
        "FB:D8:39:2A:59:09": "SmartVNS2",
        "C0:59:1E:36:C4:B2": "SmartVNS3",
        "E6:D8:E2:62:1C:8C": "SmartVNS4",
        "CC:E8:96:1F:54:5C": "SmartVNS5",
        "DE:F7:3D:30:68:DA": "SmartVNS6",
        "CF:79:18:65:C2:D9": "SmartVNS7",
        "E8:35:69:09:DC:C2": "SmartVNS8",
        "E2:07:E6:57:16:27": "SmartVNS9",
    },
    # Connect via device name:
    # A list of regexes. If a device's name matches any of the
    # regexes below, StreamLog will attempt to connect to it:
    name_regexes=[r"SmartVNS$"],
    # Characteristics:
    # The list of characteristics that StreamLog should subscribe to.
    characteristics=[
        Characteristic(
            name='data',
            uuid='CE60014D-AE91-11E1-4495-9FC5DD4AFF08',
            timeout=None,
            decoder=decode_data,
            column_headers=['sys_time', 'timestamp', 
                            'gyro_x', 'gyro_y', 'gyro_z', 
                            'acc_x', 'acc_y', 'acc_z', 
                            'q_x', 'q_y', 'q_z', 'q_w', 
                            'mag_x', 'mag_y', 'mag_z']
        ),
    ],
    ctrl_characteristics=[
        (
            "CE60014D-AE91-11E1-4496-9FC5DD4AFF01", 
            b'\x08\x0b*\x08\n\x06\x10\x04\x18\x02 x'
        ), # imu cfg
        (
            "CE60014D-AE91-11E1-4496-9FC5DD4AFF01", 
            b'\x08\x0c*\x04\x12\x02\x08\n'
        ), # mag config
    ],
    # ================ Connection Parameters =====================
    # Maximum number of simultaneously active connections:
    max_active_connections=3,
    # Maximum time in seconds that the a connection can take before
    # being aborted:
    connect_timeout=15,
    # Maximum number of simultaneous connection attempts:
    # Anything higher than one sometimes causes instability.
    max_simultaneous_connection_attempts=3,
    # Initial Characteristic Timeout:
    # An additional amount of time (in seconds) allowed in addition to the
    # characteristic timeout for the first notification.
    initial_characteristic_timeout=10,
    # Manager Interval:
    # Time in seconds between connection manager attempting to
    # create new connections
    manager_interval=0.1,
    # ================== Scanner Parameters ======================
    # Time, in seconds, a scan should last::
    scan_duration=5,
    # Time, in seconds, a Bleak discovery scan should last:
    # Increasing this may help if devices are not being discovered:
    scan_timeout=5,
    # Time, in seconds, to pause between scans:
    scan_cooldown=0.1,
    # Last-seen timeout:
    # StreamLog will only attempt to connect to a device if it has been
    # recently seen by the scanner. This is the time (in seconds) that a
    # device will be marked as 'recently seen' after being seen.
    seen_timeout=5,
    # ================== Consumer Settings ======================
    # Output buffer size in number of sameples:
    buffer_size=1500,
    # Enable/disable logging of data to CSV files:
    output_csv=True,
    # CSV output folder name:
    output_folder="output"
)

conf.validate_and_normalise()