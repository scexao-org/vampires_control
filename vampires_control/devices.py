import json
import logging
import numpy as np
import re
from serial import Serial
from time import sleep

from .state import VAMPIRES

formatter = "%(asctime)s|%(levelname)s|%(name)s - %(message)s"
logging.basicConfig(
    level=logging.DEBUG, format=formatter, handlers=[logging.StreamHandler()]
)

with open("/etc/vampires-control/device_addresses.json") as fh:
    DEVICE_MAP = json.load(fh)


class ConexDevice:
    def __init__(self, name, address=None, keyword=None, unit="", **serial_kwargs):
        self.name = name
        if address is None:
            self.address = DEVICE_MAP[self.name]
        else:
            self.address = address

        self.keyword = keyword
        self.unit = unit
        self.position = None

        self.serial_config = {
            "port": f"/dev/serial/by-id/{self.address}",
            "baudrate": 921600,
            "timeout": 0.5,
            **serial_kwargs,
        }
        self.logger = logging.getLogger(self.name)

    def status(self):
        pass

    def home(self, wait=False):
        cmd = f"1OR\r\n".encode()
        self.logger.debug(f"HOME command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.write(cmd)
            if wait:
                # continously poll until position has been reached
                current = np.inf
                while np.abs(current) >= 0.1:
                    current = self.true_position()
                    sleep(0.5)

    def reset(self):
        cmd = f"1RS\r\n".encode()
        self.logger.debug(f"RESET command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.write(cmd)

    def move_absolute(self, value, wait=False):
        cmd = f"1PA {value}\r\n".encode()
        self.logger.debug(f"MOVE ABSOLUTE command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.write(cmd)
            if self.keyword is not None:
                VAMPIRES[self.keyword] = value
            if wait:
                # continously poll until position has been reached
                current = np.inf
                while np.abs(current - value) >= 0.1:
                    current = self.true_position()
                    sleep(0.5)

    def move_relative(self, value, wait=False):
        cmd = f"1PR {value}\r\n".encode()
        self.logger.debug(f"MOVE RELATIVE command: {cmd}")
        with Serial(**self.serial_config) as serial:
            initial = self.true_position()
            serial.write(cmd)
            if self.keyword is not None:
                VAMPIRES[self.keyword] = initial + value
            if wait:
                # continously poll until position has been reached
                current = np.inf
                while np.abs(current - initial) >= np.abs(value) - 0.1:
                    current = self.true_position()
                    sleep(0.5)

    def target_position(self):
        cmd = f"1TH?\r\n".encode()
        self.logger.debug(f"TARGET POSITION command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.write(cmd)
            retval = serial.read(1024).decode("utf-8")
            self.logger.debug(f"returned value: {retval}")
        # cut off leading command
        return float(retval[3:])

    def true_position(self):
        cmd = f"1TP?\r\n".encode()
        self.logger.debug(f"TRUE POSITION command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.write(cmd)
            retval = serial.read(1024).decode("utf-8")
            self.logger.debug(f"returned value: {retval}")
        # cut off leading command
        value = float(retval[3:])
        if self.keyword is not None:
            VAMPIRES[self.keyword] = value
        return value

    def stop(self):
        cmd = f"1ST\r\n".encode()
        self.logger.debug(f"STOP command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.write(cmd)
        # call true position to update status
        self.true_position()
