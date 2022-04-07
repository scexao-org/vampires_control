import json
from serial import Serial

from ..state import VAMPIRES
from .conex import ConexDevice
from .zaber import ZaberDevice

__all__ = [
    "beamsplitter",
    "focus",
    "differential_filter",
    "qwp_1",
    "qwp_2",
    "pupil_wheel",
]

with open("/etc/vampires_control/device_addresses.json") as fh:
    DEVICE_MAP = json.load(fh)

with open("/etc/vampires_control/conf_qwp.json") as fh:
    QWP_OFFSETS = json.load(fh)


class VAMPIRESBeamsplitter:
    def __init__(
        self,
        name="beamsplitter",
        conf_file="/etc/vampires_control/conf_beamsplitter.json",
    ):
        self.name = name
        self.beamsplitter_wheel = ConexDevice(
            "wheel",
            DEVICE_MAP["beamsplitter"],
            keyword="beamsplitter_angle",
            unit="deg",
            shorthands=["w"],
            argname="angle",
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

    def status(self, update=False):
        idx = VAMPIRES["beamsplitter"]
        status = VAMPIRES["beamsplitter_status"]
        if update:
            angle = self.beamsplitter_wheel.true_position()
        else:
            angle = VAMPIRES["beamsplitter_angle"]
        out = f"[beamsplitter] {idx:>2s}: {status:<20s} {{t={angle} {self.beamsplitter_wheel.unit}}}"
        return out

    def get_positions(self):
        lines = []
        for position in self.positions["positions"]:
            line = f"{position['number']}: {position['name']}"
            lines.append(line)
        return "\n    ".join(lines)

    def help_message(self):
        postr = ",".join([str(p["number"]) for p in self.positions["positions"]])
        helpstr = f"""
beamsplitter,bs

Commands:
    beamsplitter [-h | --help]
    beamsplitter [st]atus
    beamsplitter {{{postr}}} [-w | --wait]
    beamsplitter [w]heel ([st]atus|[h]ome|[r]eset|[g]oto|[n]udge) [<angle>] [-w | --wait]

Options:
    -h --help   Display this message
    -w --wait   Block until motion is completed, if applicable

Positions:
    {self.get_positions()}
        """
        return helpstr

    def __repr__(self):
        return self.status()


class VAMPIRESDifferentialFilter:
    def __init__(
        self,
        name="diffwheel",
        conf_file="/etc/vampires_control/conf_diffwheel.json",
    ):
        self.name = name
        self.diffwheel = ConexDevice(
            "wheel",
            DEVICE_MAP["diffwheel"],
            keyword="diffwheel_angle",
            unit="deg",
            shorthands=["w"],
            argname="angle",
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

    def status(self, update=False):
        idx = VAMPIRES["diffwheel"]
        status = VAMPIRES["diffwheel_status"]
        if update:
            angle = self.diffwheel.true_position()
        else:
            angle = VAMPIRES["diffwheel_angle"]
        out = f"[{'diffwheel':^12s}] {idx:>2s}: {status:<20s} {{t={angle} {self.diffwheel.unit}}}"
        return out

    def get_positions(self):
        lines = []
        for position in self.positions["positions"]:
            line = f"{position['number']}: {position['name']}"
            lines.append(line)
        return "\n    ".join(lines)

    def help_message(self):
        postr = ",".join([str(p["number"]) for p in self.positions["positions"]])
        helpstr = f"""
diffwheel,diff,df

Commands:
    diffwheel [-h | --help]
    diffwheel [st]atus
    diffwheel {{{postr}}} [-w | --wait]
    diffwheel [w]heel ([st]atus|[h]ome|[r]eset|[g]oto|[n]udge) [<angle>] [-w | --wait]

Options:
    -h --help   Display this message
    -w --wait   Block until motion is completed, if applicable

Positions:
    {self.get_positions()}
        """
        return helpstr

    def __repr__(self):
        return self.status()


class VAMPIRESPupilWheel:
    def __init__(
        self,
        name="pupil_wheel",
        conf_file="/etc/vampires_control/conf_pupil_wheel.json",
    ):
        self.name = name
        self.pupil_wheel = ConexDevice(
            "wheel",
            DEVICE_MAP["pupil_wheel"],
            keyword="pupil_wheel_angle",
            unit="deg",
            shorthands=["w"],
            argname="angle",
        )
        self.pupil_stage_x = ZaberDevice(
            "x",
            address=DEVICE_MAP["zaber_chain"]["address"],
            index=DEVICE_MAP["zaber_chain"]["pupil_stage_x"],
            keyword="pupil_wheel_x",
            unit="stp",
            argname="pos",
        )
        self.pupil_stage_y = ZaberDevice(
            "y",
            address=DEVICE_MAP["zaber_chain"]["address"],
            index=DEVICE_MAP["zaber_chain"]["pupil_stage_y"],
            keyword="pupil_wheel_y",
            unit="stp",
            argname="pos",
        )
        self.conf_file = conf_file
        with open(self.conf_file) as fh:
            self.positions = json.load(fh)

    def move_position(self, position: int, wait=False):
        idx = position - 1  # idx starts at 0
        values = self.positions["positions"][idx]
        self.pupil_wheel.move_absolute(values["angle"], wait=wait)
        print(values["x"])
        self.pupil_stage_x.move_absolute(values["x"], wait=wait)
        print(values["y"])
        self.pupil_stage_y.move_absolute(values["y"], wait=wait)
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

    def status(self, update=False):
        idx = VAMPIRES["pupil_wheel"]
        status = VAMPIRES["pupil_wheel_status"]
        if update:
            angle = self.pupil_wheel.true_position()
            x = self.pupil_stage_x.true_position()
            y = self.pupil_stage_y.true_position()
        else:
            angle = VAMPIRES["pupil_wheel_angle"]
            x = VAMPIRES["pupil_wheel_x"]
            y = VAMPIRES["pupil_wheel_y"]
        out = f"[{'pupil':^12s}] {idx:>2s}: {status:<20s} {{t={angle} {self.pupil_wheel.unit}, x={x} {self.pupil_stage_x.unit}, y={y} {self.pupil_stage_y.unit}}}"
        return out

    def get_positions(self):
        lines = []
        for position in self.positions["positions"]:
            line = f"{position['number']}: {position['name']}"
            lines.append(line)
        return "\n    ".join(lines)

    def help_message(self):
        postr = ",".join([str(p["number"]) for p in self.positions["positions"]])
        helpstr = f"""
pupil,p

Commands:
    pupil [-h | --help]
    pupil [st]atus
    pupil {{{postr}}} [-w | --wait]
    pupil [w]heel ([st]atus|[h]ome|[r]eset|[g]oto|[n]udge) [<angle>]  [-w | --wait]
    pupil (x|y) ([st]atus|[h]ome|[r]eset|[g]oto|[n]udge)  [<pos>] [-w | --wait]

Options:
    -h --help   Display this message
    -w --wait   Block until motion is completed, if applicable

Positions:
    {self.get_positions()}
        """
        return helpstr

    def __repr__(self):
        return self.status()


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

    def help_message(self):
        cmds = [self.name, *self.shorthands]
        helpstr = f"""
qwp,q

Commands:
    qwp,q {{1,2}} ([st]atus|[h]ome|[r]eset|[g]oto|[n]udge) [<angle>]  [-w | --wait]

Options:
    -h --help   Display this message
    -w --wait   Block until motion is completed, if applicable
        """
        return helpstr


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
    "focus",
    DEVICE_MAP["focus_stage"],
    keyword="focus_stage",
    unit="mm",
    shorthands=["f"],
    argname="pos",
)
