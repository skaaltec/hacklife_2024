"""
Decoder functions used to convert the raw bytearray received
from characteristic notifications into actual data.

Should return a list of data rows.
Data rows in turn a list of data, usually numbers.

Each data row should be of the same length as the column_headers
set for the characteristic in config.py where this decoder is used.

An example:
Each PPG data-point consists of a package index and an actual reading.
The column headers are defined as follows:

    column_headers=['index', 'ppg red']

The decode_ppg  function, assuming the package index is 1 and
the readings are [10, 20, 30], will return the following list:

    [[1, 10],
     [1, 20],
     [1, 30]]
"""
from typing import Any, List
import time
import struct

def decode_data(data:bytearray) -> List[List[Any]]:
    # Decode
    local_time = time.time()
    parser_imu = struct.Struct('<I6h')
    parser_mag = struct.Struct('<I3h')
    parser_quat = struct.Struct('<I4e')
    parser_text_preamble = struct.Struct('<I')

    d = []
    while len(data) > 0:
        line = [0]*15 # 6 imu, 4 quat, 3 mag, 1 timestamp, 1 local_time
        line[0] = local_time

        sample_type = data[0]
        data = data[1:]
        if sample_type == 0:
            sample_len = parser_imu.size
            sample = parser_imu.unpack(data[:sample_len])
            line[1:8] = sample
        elif sample_type == 1:
            sample_len = parser_quat.size
            sample = parser_quat.unpack(data[:sample_len])
            line[1] = sample[0]
            line[8:12] = sample[1:]
        elif sample_type == 2:
            sample_len = parser_mag.size
            sample = parser_mag.unpack(data[:sample_len])
            line[1] = sample[0]
            line[12:] = sample[1:]
        elif sample_type == 66:
            sample_len = data[0]
            string = data[1:1+sample_len].decode('utf-8')
        d.append(line)
        data = data[sample_len:]

    return d