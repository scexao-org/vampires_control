import json

from ..state import VAMPIRES
from .conex import ConexDevice

__all__ = ["beamsplitter", "focus", "differential_filter", "qwp_1", "qwp_2", "focus"]

with open("/etc/vampires-control/device_addresses.json") as fh:
    DEVICE_MAP = json.load(fh)


class VAMPIRESBeamsplitter:
    def __init__(
        self,
        name="beamsplitter",
        conf_file="/etc/vampires-control/conf_beamsplitter.json",
    ):
        self.name = name
        self.beamsplitter_wheel = ConexDevice(
            "beamsplitter_wheel",
            DEVICE_MAP["beamsplitter_wheel"],
            keyword="beamsplitter_wheel_angle",
            unit="deg",
        )
        self.conf_file = conf_file
        with open(self.conf_file) as fh:
            self.positions = json.load(fh)

    def move_position(self, position: int, wait=False):
        idx = position - 1  # idx starts at 0
        values = self.positions[idx]
        self.beamsplitter_wheel.move_absolute(values["angle"], wait=wait)
        VAMPIRES["beamsplitter_wheel"] = values["number"]

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
        conf_file="/etc/vampires-control/conf_differential_filter.json",
    ):
        self.name = name
        self.diffwheel = ConexDevice(
            "differential_filter_wheel",
            DEVICE_MAP["differential_filter_wheel"],
            keyword="differential_filter_wheel_angle",
            unit="deg",
        )
        self.conf_file = conf_file
        with open(self.conf_file) as fh:
            self.positions = json.load(fh)

    def move_position(self, position: int, wait=False):
        idx = position - 1  # idx starts at 0
        values = self.positions[idx]
        self.diffwheel.move_absolute(values["angle"], wait=wait)
        VAMPIRES["differential_filter"] = values["number"]

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


beamsplitter = VAMPIRESBeamsplitter()
differential_filter = VAMPIRESDifferentialFilter()
qwp_1 = ConexDevice("qwp_1", DEVICE_MAP["qwp_1"], keyword="qwp_1_angle", unit="deg")
qwp_2 = ConexDevice("qwp_2", DEVICE_MAP["qwp_2"], keyword="qwp_2_angle", unit="deg")
focus = ConexDevice(
    "focus_stage", DEVICE_MAP["focus_stage"], keyword="focus_stage", unit="mm"
)
