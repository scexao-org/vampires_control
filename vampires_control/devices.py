import serial


DEVICE_MAP = {
    "beamsplitter_wheel": "",
    "differential_filter_wheel": "",
    "absolute_focus_stage": "",
}

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
