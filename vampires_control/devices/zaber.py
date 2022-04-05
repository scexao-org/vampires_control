import json
import logging
from math import floor
import numpy as np
import re
from serial import Serial
from time import sleep
import sys
import struct

from ..state import VAMPIRES

formatter = "%(asctime)s|%(levelname)s|%(name)s - %(message)s"
logging.basicConfig(
    level=logging.DEBUG, format=formatter, handlers=[logging.StreamHandler()]
)


def data_to_bytes(data: int):
    return struct.pack("<Q", data)


def bytes_to_data(bytes):
    data = 0
    power = 0
    for bit in bytes:
        data += bit * 256**power
        power += 1
    return data


class ZaberDevice:
    def __init__(self, name, address, index, keyword=None, unit="", **serial_kwargs):
        self.name = name
        self.address = address
        self.index = index

        self.keyword = keyword
        self.unit = unit
        self.position = None

        self.serial_config = {
            "port": f"/dev/serial/by-id/{self.address}",
            "baudrate": 9600,
            "timeout": 0.5,
            **serial_kwargs,
        }
        self.logger = logging.getLogger(self.name)

    def home(self, wait=False):
        cmd = bytearray([self.index, 1, 0, 0, 0, 0])
        self.logger.debug(f"HOME command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.flush()
            serial.write(cmd)
            if wait:
                # continously poll until position has been reached
                current = np.inf
                while np.abs(current) >= 0.1:
                    current = self.true_position()
                    sleep(0.5)

    def reset(self):
        cmd = bytearray([self.index, 0, 0, 0, 0, 0])
        self.logger.debug(f"RESET command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.write(cmd)

    def move_absolute(self, value: int, wait=False):
        cmd = bytearray([self.index, 20, *data_to_bytes(value)])
        self.logger.debug(f"MOVE ABSOLUTE command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.flush()
            serial.write(cmd)
            if self.keyword is not None:
                VAMPIRES[self.keyword] = value
            if wait:
                # continously poll until position has been reached
                current = np.inf
                while np.abs(current - value) >= 100:
                    current = self.true_position()
                    sleep(0.5)

    def move_relative(self, value: int, wait=False):
        cmd = bytearray([self.index, 21, *data_to_bytes(value)])
        self.logger.debug(f"MOVE RELATIVE command: {cmd}")
        with Serial(**self.serial_config) as serial:
            initial = self.true_position()
            serial.flush()
            serial.write(cmd)
            if self.keyword is not None:
                VAMPIRES[self.keyword] = initial + value
            if wait:
                # continously poll until position has been reached
                current = np.inf
                while np.abs(current - initial) >= np.abs(value) - 100:
                    current = self.true_position()
                    print(np.abs(current - initial))
                    sleep(0.5)

    def true_position(self):
        cmd = bytearray([self.index, 60, 0, 0, 0, 0])
        self.logger.debug(f"TRUE POSITION command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.flush()
            serial.write(cmd)
            retbytes = "".join([line.decode("latin-1") for line in serial.readlines()])
            retval = [ord(b) for b in retbytes]
            self.logger.debug(f"returned value: {retval}")
        # cut off leading command
        value = bytes_to_data(retval[2:])
        if self.keyword is not None:
            VAMPIRES[self.keyword] = value
        return value

    def stop(self):
        cmd = bytearray([self.index, 23, 0, 0, 0, 0])
        self.logger.debug(f"STOP command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.write(cmd)
        # call true position to update status
        self.true_position()
