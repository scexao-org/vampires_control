import json
import serial

with open("/etc/vampires-control/device_addresses.json") as fh:
    DEVICE_MAP = json.load(fh)


class VAMPIRESDevice:
    def __init__(self, name, address=None, unit=""):
        self.name = name
        if address is None:
            self.address = DEVICE_MAP[self.name]
        else:
            self.address = address

        self.unit = unit
        self.position = None

    def status(self):
        pass

    def home(self):
        pass

    def reset(self):
        pass

    def move_absolute(self, value):
        pass

    def move_relative(self, value):
        pass

    def target_position(self, value):
        pass

    def true_position(self, value):
        pass
