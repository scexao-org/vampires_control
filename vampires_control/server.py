from docopt import docopt
import json
import socketserver
from socketserver import BaseRequestHandler

from .state import VAMPIRES
from .devices.devices import (
    beamsplitter,
    differential_filter,
    focus,
    qwp_1,
    qwp_2,
    pupil_wheel,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 47653

argformat = """
Usage:
    (get | g) <KEYWORD>
    (set | s) <KEYWORD> <VALUE>
    (status|st)
    (beamsplitter | bs) <position> [-w | --wait]
    (beamsplitter | bs) (status|st)
    (beamsplitter | bs) (wheel|w) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]
    (diffwheel | diff | df) <position> [-w | --wait]
    (diffwheel | diff | df) (status|st)
    (diffwheel | diff | df) (wheel|w) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]
    (pupil | p) <position> [-w | --wait]
    (pupil | p) (status|st)
    (pupil | p) (wheel|w) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]
    (pupil | p) (x|y) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]
    (focus | f) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]
    (qwp | q) (1|2) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]

Options:
    -h --help   Display this message
    -w --wait   For actions which move a motor, block until position is reached
"""


class VAMPIRESHandler(BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print(f"{self.client_address[0]} received: {self.data}")

        command = str(self.data, "ascii")
        tokens = command.split()
        # see if wait flag is set
        wait = "-w" in tokens or "--wait" in tokens
        if tokens[0] == "get" or tokens[0] == "g":
            value = VAMPIRES[tokens[1]]
            self.request.sendall(bytes(str(value), "ascii"))
        elif tokens[0] == "set" or tokens[0] == "s":
            VAMPIRES[tokens[1]] = tokens[2]
            value = VAMPIRES[tokens[1]]
            self.request.sendall(bytes(str(value), "ascii"))
        elif tokens[0] == "status" or tokens[0] == "st":
            # TODO this should probably go into the device classes
            bs_idx = VAMPIRES["beamsplitter"]
            bs_st = VAMPIRES["beamsplitter_status"]
            bs_angle = VAMPIRES["beamsplitter_angle"]
            bs = f"beamsplitter: ({bs_idx}) {bs_st} {{t={bs_angle} {beamsplitter.beamsplitter_wheel.unit}}}"

            df_idx = VAMPIRES["diffwheel"]
            df_st = VAMPIRES["diffwheel_status"]
            df_angle = VAMPIRES["diffwheel_angle"]
            df = f"diff. filter: ({df_idx}) {df_st} {{t={df_angle} {differential_filter.diffwheel.unit}}}"

            p_idx = VAMPIRES["pupil_wheel"]
            p_st = VAMPIRES["pupil_wheel_status"]
            p_angle = VAMPIRES["pupil_wheel_angle"]
            p_x = VAMPIRES["pupil_wheel_x"]
            p_y = VAMPIRES["pupil_wheel_y"]
            p = f"pupil wheel: ({p_idx}) {p_st} {{t={p_angle} {pupil_wheel.pupil_wheel.unit}, x={p_x} {pupil_wheel.pupil_stage_x.unit}, y={p_y} {pupil_wheel.pupil_stage_y.unit}}}"

            f_st = VAMPIRES["focus_stage"]
            f = f"focus stage: {f_st} {focus.unit}"

            qwp1_angle = VAMPIRES["qwp_1"]
            qwp2_angle = VAMPIRES["qwp_2"]
            q = f"qwp: {{t1={qwp1_angle} {qwp_1.unit}, t2={qwp2_angle} {qwp_2.unit}}}"

            out = "\n".join([bs, df, p, f, q])
            self.request.sendall(bytes(out, "ascii"))
        elif tokens[0] == "beamsplitter" or tokens[0] == "bs":
            if len(tokens) == 1 or tokens[1] == "status" or tokens[1] == "st":
                idx = VAMPIRES["beamsplitter"]
                status = VAMPIRES["beamsplitter_status"]
                angle = VAMPIRES["beamsplitter_angle"]
                out = f"({idx}) {status} {{t={angle} {beamsplitter.beamsplitter_wheel.unit}}}"
                self.request.sendall(bytes(out, "ascii"))
            elif tokens[1] == "wheel" or tokens[1] == "w":
                if len(tokens) == 2 or tokens[2] == "status" or tokens[2] == "st":
                    value = beamsplitter.beamsplitter_wheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "home" or tokens[2] == "h":
                    beamsplitter.beamsplitter_wheel.home(wait=wait)
                elif tokens[2] == "reset" or tokens[2] == "r":
                    self.request.sendall(
                        bytes(
                            "resetting is disabled for safety during testing", "ascii"
                        )
                    )
                elif tokens[2] == "stop" or tokens[2] == "s":
                    beamsplitter.beamsplitter_wheel.stop()
                    value = beamsplitter.beamsplitter_wheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "goto" or tokens[2] == "g":
                    angle = float(tokens[3])
                    beamsplitter.beamsplitter_wheel.move_absolute(angle, wait=wait)
                    value = beamsplitter.beamsplitter_wheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "nudge" or tokens[2] == "n":
                    angle = float(tokens[3])
                    beamsplitter.beamsplitter_wheel.move_relative(angle, wait=wait)
                    value = beamsplitter.beamsplitter_wheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                else:
                    self.request.sendall(
                        bytes("ERROR: invalid command received", "ascii")
                    )
            else:
                try:
                    posn = int(tokens[1])
                    beamsplitter.move_position(posn, wait=wait)
                    status = VAMPIRES["beamsplitter_status"]
                    angle = VAMPIRES["beamsplitter_angle"]
                    out = f"({posn}) {status} {{{angle} {beamsplitter.beamsplitter_wheel.unit}}}"
                    self.request.sendall(bytes(out, "ascii"))
                except:
                    self.request.sendall(
                        bytes("ERROR: invalid command received", "ascii")
                    )
        elif tokens[0] == "diffwheel" or tokens[0] == "diff" or tokens[0] == "df":
            if len(tokens) == 1 or tokens[1] == "status" or tokens[1] == "st":
                idx = VAMPIRES["diffwheel"]
                status = VAMPIRES["diffwheel_status"]
                angle = VAMPIRES["diffwheel_angle"]
                out = f"({idx}) {status} {{t={angle} {differential_filter.diffwheel.unit}}}"
                self.request.sendall(bytes(out, "ascii"))
            elif tokens[1] == "wheel" or tokens[1] == "w":
                if len(tokens) == 2 or tokens[2] == "status" or tokens[2] == "st":
                    value = differential_filter.diffwheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "home" or tokens[2] == "h":
                    differential_filter.diffwheel.home(wait=wait)
                elif tokens[2] == "reset" or tokens[2] == "r":
                    self.request.sendall(
                        bytes(
                            "resetting is disabled for safety during testing", "ascii"
                        )
                    )
                elif tokens[2] == "stop" or tokens[2] == "s":
                    differential_filter.diffwheel.stop()
                    value = differential_filter.diffwheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "goto" or tokens[2] == "g":
                    angle = float(tokens[3])
                    differential_filter.diffwheel.move_absolute(angle, wait=wait)
                    value = differential_filter.diffwheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "nudge" or tokens[2] == "n":
                    angle = float(tokens[3])
                    differential_filter.diffwheel.move_relative(angle, wait=wait)
                    value = differential_filter.diffwheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                else:
                    self.request.sendall(
                        bytes("ERROR: invalid command received", "ascii")
                    )
            else:
                try:
                    posn = int(tokens[1])
                    differential_filter.move_position(posn, wait=wait)
                    status = VAMPIRES["diffwheel_status"]
                    angle = VAMPIRES["diffwheel_angle"]
                    out = f"({posn}) {status} {{t={angle} {differential_filter.diffwheel.unit}}}"
                    self.request.sendall(bytes(out, "ascii"))
                except:
                    self.request.sendall(
                        bytes("ERROR: invalid command received", "ascii")
                    )
        elif tokens[0] == "pupil" or tokens[0] == "p":
            if len(tokens) == 1 or tokens[1] == "status" or tokens[1] == "st":
                idx = VAMPIRES["pupil_wheel"]
                status = VAMPIRES["pupil_wheel_status"]
                angle = VAMPIRES["pupil_wheel_angle"]
                x = VAMPIRES["pupil_wheel_x"]
                y = VAMPIRES["pupil_wheel_y"]
                out = f"({idx}) {status} {{t={angle} {pupil_wheel.pupil_wheel.unit}, x={x} {pupil_wheel.pupil_stage_x.unit}, y={y} {pupil_wheel.pupil_stage_y.unit}}}"
                self.request.sendall(bytes(out, "ascii"))
            elif tokens[1] == "wheel" or tokens[1] == "w":
                if len(tokens) == 2 or tokens[2] == "status" or tokens[2] == "st":
                    value = pupil_wheel.pupil_wheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "home" or tokens[2] == "h":
                    pupil_wheel.pupil_wheel.home(wait=wait)
                elif tokens[2] == "reset" or tokens[2] == "r":
                    self.request.sendall(
                        bytes(
                            "resetting is disabled for safety during testing", "ascii"
                        )
                    )
                elif tokens[2] == "stop" or tokens[2] == "s":
                    pupil_wheel.pupil_wheel.stop()
                    value = pupil_wheel.pupil_wheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "goto" or tokens[2] == "g":
                    angle = float(tokens[3])
                    pupil_wheel.pupil_wheel.move_absolute(angle, wait=wait)
                    value = pupil_wheel.pupil_wheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "nudge" or tokens[2] == "n":
                    angle = float(tokens[3])
                    pupil_wheel.pupil_wheel.move_relative(angle, wait=wait)
                    value = pupil_wheel.pupil_wheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                else:
                    self.request.sendall(
                        bytes("ERROR: invalid command received", "ascii")
                    )
            elif tokens[1] == "x":
                if len(tokens) == 2 or tokens[2] == "status" or tokens[2] == "st":
                    value = pupil_wheel.pupil_stage_x.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "home" or tokens[2] == "h":
                    pupil_wheel.pupil_stage_x.home(wait=wait)
                elif tokens[2] == "reset" or tokens[2] == "r":
                    self.request.sendall(
                        bytes(
                            "resetting is disabled for safety during testing", "ascii"
                        )
                    )
                elif tokens[2] == "stop" or tokens[2] == "s":
                    pupil_wheel.pupil_stage_x.stop()
                    value = pupil_wheel.pupil_stage_x.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "goto" or tokens[2] == "g":
                    position = int(tokens[3])
                    pupil_wheel.pupil_stage_x.move_absolute(position, wait=wait)
                    value = pupil_wheel.pupil_stage_x.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "nudge" or tokens[2] == "n":
                    position = int(tokens[3])
                    pupil_wheel.pupil_stage_x.move_relative(position, wait=wait)
                    value = pupil_wheel.pupil_stage_x.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                else:
                    self.request.sendall(
                        bytes("ERROR: invalid command received", "ascii")
                    )
            elif tokens[1] == "y":
                if len(tokens) == 2 or tokens[2] == "status" or tokens[2] == "st":
                    value = pupil_wheel.pupil_stage_y.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "home" or tokens[2] == "h":
                    pupil_wheel.pupil_stage_y.home(wait=wait)
                elif tokens[2] == "reset" or tokens[2] == "r":
                    self.request.sendall(
                        bytes(
                            "resetting is disabled for safety during testing", "ascii"
                        )
                    )
                elif tokens[2] == "stop" or tokens[2] == "s":
                    pupil_wheel.pupil_stage_y.stop()
                    value = pupil_wheel.pupil_stage_y.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "goto" or tokens[2] == "g":
                    position = int(tokens[3])
                    pupil_wheel.pupil_stage_y.move_absolute(position, wait=wait)
                    value = pupil_wheel.pupil_stage_y.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "nudge" or tokens[2] == "n":
                    position = int(tokens[3])
                    pupil_wheel.pupil_stage_y.move_relative(position, wait=wait)
                    value = pupil_wheel.pupil_stage_y.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                else:
                    self.request.sendall(
                        bytes("ERROR: invalid command received", "ascii")
                    )
            else:
                try:
                    posn = int(tokens[1])
                    pupil_wheel.move_position(posn, wait=wait)
                    status = VAMPIRES["pupil_wheel_status"]
                    angle = VAMPIRES["pupil_wheel_angle"]
                    x = VAMPIRES["pupil_wheel_x"]
                    y = VAMPIRES["pupil_wheel_y"]
                    out = f"({idx}) {status} {{t={angle} {pupil_wheel.pupil_wheel.unit}, x={x} {pupil_wheel.pupil_stage_x.unit}, y={y} {pupil_wheel.pupil_stage_y.unit}}}"
                    self.request.sendall(bytes(out, "ascii"))
                except:
                    self.request.sendall(
                        bytes("ERROR: invalid command received", "ascii")
                    )
        elif tokens[0] == "focus" or tokens[0] == "f":
            if len(tokens) == 1 or tokens[1] == "status" or tokens[1] == "st":
                value = focus.true_position()
                self.request.sendall(bytes(str(value), "ascii"))
            elif tokens[1] == "home" or tokens[1] == "h":
                focus.home(wait=wait)
            elif tokens[1] == "reset" or tokens[1] == "r":
                self.request.sendall(
                    bytes("resetting is disabled for safety during testing", "ascii")
                )
            elif tokens[1] == "stop" or tokens[1] == "s":
                focus.stop()
                value = focus.true_position()
                self.request.sendall(bytes(str(value), "ascii"))
            elif tokens[1] == "goto" or tokens[1] == "g":
                position = float(tokens[2])
                focus.move_absolute(position, wait=wait)
                value = focus.true_position()
                self.request.sendall(bytes(str(value), "ascii"))
            elif tokens[1] == "nudge" or tokens[1] == "n":
                position = float(tokens[2])
                focus.move_relative(position, wait=wait)
                value = focus.true_position()
                self.request.sendall(bytes(str(value), "ascii"))
            else:
                self.request.sendall(bytes("ERROR: invalid command received", "ascii"))
        elif tokens[0] == "qwp" or tokens[0] == "q":
            if tokens[1] == "1":
                qwp = qwp_1
            elif tokens[1] == "2":
                qwp = qwp_2
            else:
                self.request.sendall(bytes("ERROR: invalid command received", "ascii"))
            if len(tokens) == 1 or tokens[1] == "status" or tokens[1] == "st":
                value = qwp.true_position()
                self.request.sendall(bytes(str(value), "ascii"))
            elif tokens[1] == "home" or tokens[1] == "h":
                qwp.home(wait=wait)
            elif tokens[1] == "reset" or tokens[1] == "r":
                self.request.sendall(
                    bytes("resetting is disabled for safety during testing", "ascii")
                )
            elif tokens[1] == "stop" or tokens[1] == "s":
                qwp.stop()
                value = qwp.true_position()
                self.request.sendall(bytes(str(value), "ascii"))
            elif tokens[1] == "goto" or tokens[1] == "g":
                angle = float(tokens[2])
                qwp.move_absolute(angle, wait=wait)
                value = qwp.true_position()
                self.request.sendall(bytes(str(value), "ascii"))
            elif tokens[1] == "nudge" or tokens[1] == "n":
                angle = float(tokens[2])
                qwp.move_relative(angle, wait=wait)
                value = qwp.true_position()
                self.request.sendall(bytes(str(value), "ascii"))
            else:
                self.request.sendall(bytes("ERROR: invalid command received", "ascii"))
        else:
            pass
