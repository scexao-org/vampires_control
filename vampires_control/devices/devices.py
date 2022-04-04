import json
from serial import Serial

from ..state import VAMPIRES
from .conex import ConexDevice

__all__ = [
    "beamsplitter",
    "focus",
    "differential_filter",
    "qwp_1",
    "qwp_2",
    "pupil_wheel",
]

with open("/etc/vampires-control/device_addresses.json") as fh:
    DEVICE_MAP = json.load(fh)

with open("/etc/vampires-control/conf_qwp.json") as fh:
    QWP_OFFSETS = json.load(fh)


class VAMPIRESBeamsplitter:
    def __init__(
        self,
        name="beamsplitter",
        conf_file="/etc/vampires-control/conf_beamsplitter.json",
    ):
        self.name = name
        self.beamsplitter_wheel = ConexDevice(
            "beamsplitter",
            DEVICE_MAP["beamsplitter"],
            keyword="beamsplitter_angle",
            unit="deg",
        )
        self.conf_file = conf_file
        with open(self.conf_file) as fh:
            self.positions = json.load(fh)

    def move_position(self, position: int, wait=False):
        idx = position - 1  # idx starts at 0
        values = self.positions["positions"][idx]
        self.beamsplitter_wheel.move_absolute(values["angle"], wait=wait)
        VAMPIRES["beamsplitter"] = values["number"]
        VAMPIRES["beamsplitter_status"] = values["name"]

    def write(self, file=None):
        if file is None:
            file = self.conf_file
        with open(file, "w") as fh:
            json.dump(self.positions)

    def update(self, file=None):
        if file is None:
            file = self.conf_file
        with open(file) as fh:
            self.positions = json.load(fh)


class VAMPIRESDifferentialFilter:
    def __init__(
        self,
        name="diffwheel",
        conf_file="/etc/vampires-control/conf_diffwheel.json",
    ):
        self.name = name
        self.diffwheel = ConexDevice(
            "diffwheel",
            DEVICE_MAP["diffwheel"],
            keyword="diffwheel_angle",
            unit="deg",
        )
        self.conf_file = conf_file
        with open(self.conf_file) as fh:
            self.positions = json.load(fh)

    def move_position(self, position: int, wait=False):
        idx = position - 1  # idx starts at 0
        values = self.positions["positions"][idx]
        self.diffwheel.move_absolute(values["angle"], wait=wait)
        VAMPIRES["diffwheel"] = values["number"]
        VAMPIRES["diffwheel_cam1"] = values["cam1"]
        VAMPIRES["diffwheel_cam2"] = values["cam2"]
        VAMPIRES["diffwheel_status"] = f"{values['cam1']} / {values['cam2']}"

    def write(self, file=None):
        if file is None:
            file = self.conf_file
        with open(file, "w") as fh:
            json.dump(self.positions)

    def update(self, file=None):
        if file is None:
            file = self.conf_file
        with open(file) as fh:
            self.positions = json.load(fh)


class VAMPIRESPupilWheel:
    def __init__(
        self,
        name="pupil_wheel",
        conf_file="/etc/vampires-control/conf_pupil_wheel.json",
    ):
        self.name = name
        self.pupil_wheel = ConexDevice(
            "pupil_wheel",
            DEVICE_MAP["pupil_wheel"],
            keyword="pupil_wheel_angle",
            unit="deg",
        )
        self.conf_file = conf_file
        with open(self.conf_file) as fh:
            self.positions = json.load(fh)

    def move_position(self, position: int, wait=False):
        idx = position - 1  # idx starts at 0
        values = self.positions["positions"][idx]
        self.pupil_wheel.move_absolute(values["angle"], wait=wait)
        VAMPIRES["pupil_wheel"] = values["number"]
        VAMPIRES["pupil_wheel_status"] = values["name"]

    def write(self, file=None):
        if file is None:
            file = self.conf_file
        with open(file, "w") as fh:
            json.dump(self.positions)

    def update(self, file=None):
        if file is None:
            file = self.conf_file
        with open(file) as fh:
            self.positions = json.load(fh)


class VAMPIRESQWP(ConexDevice):
    def __init__(self, *args, offset=0, **kwargs):
        self.offset = offset
        return super().__init__(*args, **kwargs)

    def target_position(self):
        val = super().target_position()
        return val + self.offset

    def true_position(self):
        cmd = f"1TP?\r\n".encode()
        self.logger.debug(f"TRUE POSITION command: {cmd}")
        with Serial(**self.serial_config) as serial:
            serial.write(cmd)
            retval = serial.read(1024).decode("utf-8")
            self.logger.debug(f"returned value: {retval}")
        # cut off leading command
        value = float(retval[3:])
        value += self.offset
        if self.keyword is not None:
            VAMPIRES[self.keyword] = value
        return value

    def move_absolute(self, value: float, **kwargs):
        real_value = value - self.offset
        return super().move_absolute(real_value, **kwargs)


beamsplitter = VAMPIRESBeamsplitter()
differential_filter = VAMPIRESDifferentialFilter()
pupil_wheel = VAMPIRESPupilWheel()
qwp_1 = VAMPIRESQWP(
    "qwp_1",
    DEVICE_MAP["qwp_1"],
    offset=QWP_OFFSETS["qwp_1_offset"],
    keyword="qwp_1",
    unit="deg",
)
qwp_2 = VAMPIRESQWP(
    "qwp_2",
    DEVICE_MAP["qwp_2"],
    offset=QWP_OFFSETS["qwp_2_offset"],
    keyword="qwp_2",
    unit="deg",
)
focus = ConexDevice(
    "focus_stage", DEVICE_MAP["focus_stage"], keyword="focus_stage", unit="mm"
)
