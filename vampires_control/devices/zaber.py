import json
import logging
import numpy as np
import re
from serial import Serial
from time import sleep

from ..state import VAMPIRES

formatter = "%(asctime)s|%(levelname)s|%(name)s - %(message)s"
logging.basicConfig(
    level=logging.DEBUG, format=formatter, handlers=[logging.StreamHandler()]
)


def data_to_bits(data: int):
    # Convert negative numbers...
    if data < 0:
        data = 256**4 + data

    # d6 is the last bit (data must be larger than 256^3 to have a value here)
    d6 = np.floor(data / 256**3)
    data -= 256**3 * d6

    # d5 is the next largest bit... d5 = (0:256)*256^2
    d5 = np.floor(data / 256**2)
    if d5 > 256:
        d5 = 256

    # d4 is the second smallest bit... d4 = (0:256)*256
    data -= 256**2 * d5
    d4 = np.floor(data / 256)
    if d4 > 256:
        d4 = 256

    # d3 is the smallest bit, values are 0:256
    d3 = np.floor(np.mod(data, 256))
    if d3 > 256:
        d3 = 256

    return [d3, d4, d5, d6]


def bits_to_data(d3, d4, d5, d6):
    # TODO this is just bitshifting
    data = d6 * 256**3 + d5 * 256**2 + d4 * 256 + d3
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

    # def home(self, wait=False):
    #     cmd = f"1OR\r\n".encode()
    #     self.logger.debug(f"HOME command: {cmd}")
    #     with Serial(**self.serial_config) as serial:
    #         serial.write(cmd)
    #         if wait:
    #             # continously poll until position has been reached
    #             current = np.inf
    #             while np.abs(current) >= 0.1:
    #                 current = self.true_position()
    #                 sleep(0.5)

    # def reset(self):
    #     cmd = f"1RS\r\n".encode()
    #     self.logger.debug(f"RESET command: {cmd}")
    #     with Serial(**self.serial_config) as serial:
    #         serial.write(cmd)

    # def move_absolute(self, value, wait=False):
    #     bits = data_to_bits(value)
    #     cmd = f"1PA {value}\r\n".encode()
    #     self.logger.debug(f"MOVE ABSOLUTE command: {cmd}")
    #     with Serial(**self.serial_config) as serial:
    #         serial.write(cmd)
    #         if self.keyword is not None:
    #             VAMPIRES[self.keyword] = value
    #         if wait:
    #             # continously poll until position has been reached
    #             current = np.inf
    #             while np.abs(current - value) >= 0.1:
    #                 current = self.true_position()
    #                 sleep(0.5)

    # def move_relative(self, value, wait=False):
    #     cmd = f"1PR {value}\r\n".encode()
    #     self.logger.debug(f"MOVE RELATIVE command: {cmd}")
    #     with Serial(**self.serial_config) as serial:
    #         initial = self.true_position()
    #         serial.write(cmd)
    #         if self.keyword is not None:
    #             VAMPIRES[self.keyword] = initial + value
    #         if wait:
    #             # continously poll until position has been reached
    #             current = np.inf
    #             while np.abs(current - initial) >= np.abs(value) - 0.1:
    #                 current = self.true_position()
    #                 sleep(0.5)

    def true_position(self):
        cmd = [self.index, 60]
        self.logger.debug(f"TRUE POSITION command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.write(cmd)
            retval = serial.read(6).decode("utf-8")
            self.logger.debug(f"returned value: {retval}")
        # cut off leading command
        # value = float(retval[3:])
        if self.keyword is not None:
            VAMPIRES[self.keyword] = value
        return value

    # def stop(self):
    #     cmd = f"1ST\r\n".encode()
    #     self.logger.debug(f"STOP command: {cmd}")
    #     with Serial(**self.serial_config) as serial:
    #         serial.write(cmd)
    #     # call true position to update status
    #     self.true_position()
