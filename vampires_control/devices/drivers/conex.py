import json
import logging
import numpy as np
import re
from serial import Serial
from time import sleep

from ...state import VAMPIRES


class ConexDevice:
    def __init__(
        self,
        name,
        address,
        keyword=None,
        unit="",
        shorthands=None,
        argname=None,
        **serial_kwargs,
    ):
        self.name = name
        self.address = address

        self.keyword = keyword
        self.unit = unit
        self.shorthands = shorthands if shorthands is not None else []
        self.argname = argname
        self.position = None

        self.serial = Serial(
            port=f"/dev/serial/by-id/{self.address}",
            baudrate=921600,
            timeout=0.5,
            **serial_kwargs,
        )
        self.logger = logging.getLogger(self.name)

    def home(self, wait=False):
        cmd = b"1OR\r\n"
        self.logger.debug(f"HOME command: {cmd}")
        self.serial.write(cmd)
        if wait:
            # continously poll until position has been reached
            current = np.inf
            while np.abs(current) >= 0.1:
                current = self.true_position()
                sleep(0.5)

    def reset(self):
        cmd = b"1RS\r\n"
        self.logger.debug(f"RESET command: {cmd}")
        self.serial.write(cmd)

    def move_absolute(self, value, wait=False):
        cmd = f"1PA {value}\r\n".encode()
        self.logger.debug(f"MOVE ABSOLUTE command: {cmd}")
        self.serial.write(cmd)
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
        initial = self.true_position()
        self.serial.write(cmd)
        if self.keyword is not None:
            VAMPIRES[self.keyword] = initial + value
        if wait:
            # continously poll until position has been reached
            current = np.inf
            while np.abs(current - initial) >= np.abs(value) - 0.1:
                current = self.true_position()
                sleep(0.5)

    def target_position(self):
        cmd = b"1TH?\r\n"
        self.logger.debug(f"TARGET POSITION command: {cmd}")
        self.serial.write(cmd)
        retval = self.serial.read(1024).decode("utf-8").split("\r\n", 1)[0]
        self.logger.debug(f"returned value: {retval}")
        # cut off leading command
        return float(retval[3:])

    def true_position(self):
        cmd = b"1TP?\r\n"
        self.logger.debug(f"TRUE POSITION command: {cmd}")
        self.serial.write(cmd)
        retval = self.serial.read(1024).decode("utf-8").split("\r\n", 1)[0]
        self.logger.debug(f"returned value: {retval}")
        # cut off leading command
        value = float(retval[3:])
        if self.keyword is not None:
            VAMPIRES[self.keyword] = value
        return value

    def stop(self):
        cmd = b"1ST\r\n"
        self.logger.debug(f"STOP command: {cmd}")
        self.serial.write(cmd)
        # call true position to update status
        self.true_position()

    def help_message(self):
        cmds = [self.name, *self.shorthands]
        helpstr = f"""
{','.join(cmds)}

Commands:
    {self.name} ([st]atus|[h]ome|[r]eset|[g]oto|[n]udge) [<{self.argname}>]  [-w | --wait]

Options:
    -h --help   Display this message
    -w --wait   Block until motion is completed, if applicable
        """
        return helpstr
