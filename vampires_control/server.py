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
    (get|g) <KEYWORD>
    (set|s) <KEYWORD> <VALUE>
    (beamsplitter|bs) <position> [-w | --wait]
    (beamsplitter|bs) (status|st)
    (beamsplitter|bs) (wheel|w) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]
    (diffwheel|diff|df) <position> [-w | --wait]
    (diffwheel|diff|df) (status|st)
    (diffwheel|diff|df) (wheel|w) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]
    (pupil|p) <position> [-w | --wait]
    (pupil|p) (status|st)
    (pupil|p) (wheel|w) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]
    (pupil|p) (x|y) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]
    (focus|f) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]
    (qwp|q) (1|2) (status|home|reset|goto|nudge|stop) [<arg>] [-w | --wait]

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
        if tokens[0] == "get" or tokens[0] == "g":
            value = VAMPIRES[tokens[1]]
            self.request.sendall(bytes(str(value), "ascii"))
        elif tokens[0] == "set" or tokens[0] == "s":
            VAMPIRES[tokens[1]] = tokens[2]
            value = VAMPIRES[tokens[1]]
            self.request.sendall(bytes(str(value), "ascii"))
        elif tokens[0] == "beamsplitter" or tokens[0] == "bs":
            if len(tokens) == 1 or tokens[1] == "status" or tokens[1] == "st":
                idx = VAMPIRES["beamsplitter"]
                posn = VAMPIRES["beamsplitter_status"]
                angle = VAMPIRES["beamsplitter_angle"]
                out = f"({idx}) {posn} {{t={angle} {beamsplitter.beamsplitter_wheel.unit}}}"
                self.request.sendall(bytes(out, "ascii"))
            elif tokens[1] == "wheel" or tokens[1] == "w":
                if len(tokens) == 2 or tokens[2] == "status" or tokens[2] == "st":
                    value = beamsplitter.beamsplitter_wheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "home" or tokens[2] == "h":
                    beamsplitter.beamsplitter_wheel.home()
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
                    beamsplitter.beamsplitter_wheel.move_absolute(angle)
                    value = beamsplitter.beamsplitter_wheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                elif tokens[2] == "nudge" or tokens[2] == "n":
                    angle = float(tokens[3])
                    beamsplitter.beamsplitter_wheel.move_relative(angle)
                    value = beamsplitter.beamsplitter_wheel.true_position()
                    self.request.sendall(bytes(str(value), "ascii"))
                else:
                    self.request.sendall(
                        bytes("ERROR: invalid command received", "ascii")
                    )
            else:
                try:
                    posn = int(tokens[1])
                    beamsplitter.move_position(posn)
                    posn = VAMPIRES["beamsplitter_status"]
                    angle = VAMPIRES["beamsplitter_angle"]
                    out = f"({posn}) {posn} {{{angle} {beamsplitter.beamsplitter_wheel.unit}}}"
                    self.request.sendall(bytes(out, "ascii"))
                except:
                    self.request.sendall(
                        bytes("ERROR: invalid command received", "ascii")
                    )

        elif tokens[0] == "status" or tokens[0] == "st":
            # TODO this should probably go into the device classes
            bs_idx = VAMPIRES["beamsplitter"]
            bs_posn = VAMPIRES["beamsplitter_status"]
            bs_angle = VAMPIRES["beamsplitter_angle"]
            bs = f"beamsplitter: ({bs_idx}) {bs_posn} {{t={bs_angle} {beamsplitter.beamsplitter_wheel.unit}}}"

            df_idx = VAMPIRES["diffwheel"]
            df_posn = VAMPIRES["diffwheel_status"]
            df_angle = VAMPIRES["diffwheel_angle"]
            df = f"diff. filter: ({df_idx}) {df_posn} {{t={df_angle} {differential_filter.diffwheel.unit}}}"

            p_idx = VAMPIRES["pupil_wheel"]
            p_posn = VAMPIRES["pupil_wheel_status"]
            p_angle = VAMPIRES["pupil_wheel_angle"]
            p_x = VAMPIRES["pupil_wheel_x"]
            p_y = VAMPIRES["pupil_wheel_y"]
            p = f"pupil wheel: ({p_idx}) {p_posn} {{t={p_angle} {pupil_wheel.pupil_wheel.unit}, x={p_x} {pupil_wheel.pupil_stage_x.unit}, y={p_y} {pupil_wheel.pupil_stage_y.unit}}}"

            f_posn = VAMPIRES["focus_stage"]
            f = f"focus stage: {f_posn} {focus.unit}"

            qwp1_angle = VAMPIRES["qwp_1"]
            qwp2_angle = VAMPIRES["qwp_2"]
            q = f"qwp: {{t1={qwp1_angle} {qwp_1.unit}, t2={qwp2_angle} {qwp_2.unit}}}"

            out = "\n".join([bs, df, p, f, q])
            self.request.sendall(bytes(out, "ascii"))

        # elif tokens[0] == "diffwheel" or tokens[0] == "diff" or tokens[0] == "df":
        #     pass
        # elif tokens[0] == "pupil" or tokens[0] == "p":
        #     pass
        # elif tokens[0] == "focus" or tokens[0] == "f":
        #     pass
        # elif tokens[0] == "qwp" or tokens[0] == "q":
        #     pass
        # else:
        #     pass
