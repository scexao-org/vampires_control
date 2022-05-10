import json
import logging
import re

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

from argparse import ArgumentParser


def handle_message(message):
        tokens = message.strip().split()
        # see if wait flag is set
        wait = "-w" in tokens or "--wait" in tokens
        update = "-u" in tokens or "--update" in tokens
        if tokens[0] == "get" or tokens[0] == "g":
            value = VAMPIRES[tokens[1]]
            return str(value)
        elif tokens[0] == "set" or tokens[0] == "s":
            VAMPIRES[tokens[1]] = tokens[2]
            value = VAMPIRES[tokens[1]]
            return str(value)
        elif tokens[0] == "status" or tokens[0] == "st":
            bs = beamsplitter.status(update=update)
            df = differential_filter.status(update=update)
            p = pupil_wheel.status(update=update)

            if update:
                f_st = focus.true_position()
            else:
                f_st = VAMPIRES["focus_stage"]
            f = f"[{'focus':^12s}]   : {' ' * 20} {{z={f_st} {focus.unit}}}"

            if update:
                qwp1_angle = qwp_1.true_position()
                qwp2_angle = qwp_2.true_position()
            else:
                qwp1_angle = VAMPIRES["qwp_1"]
                qwp2_angle = VAMPIRES["qwp_2"]
            q = f"[{'qwp':^12s}]   : {' ' * 20} {{t1={qwp1_angle} {qwp_1.unit}, t2={qwp2_angle} {qwp_2.unit}}}"

            out = "\n".join([bs, df, p, f, q])
            return out
        elif tokens[0] == "beamsplitter" or tokens[0] == "bs":
            if len(tokens) == 1 or tokens[1] == "status" or tokens[1] == "st":
                idx = VAMPIRES["beamsplitter"]
                status = VAMPIRES["beamsplitter_status"]
                angle = VAMPIRES["beamsplitter_angle"]
                out = f"({idx}) {status} {{t={angle} {beamsplitter.beamsplitter_wheel.unit}}}"
                return out
            elif tokens[1] == "wheel" or tokens[1] == "w":
                if len(tokens) == 2:
                    return beamsplitter.beamsplitter_wheel.help_message()
                elif tokens[2] == "status" or tokens[2] == "st":
                    value = beamsplitter.beamsplitter_wheel.true_position()
                    return str(value)
                elif tokens[2] == "home" or tokens[2] == "h":
                    beamsplitter.beamsplitter_wheel.home(wait=wait)
                elif tokens[2] == "reset" or tokens[2] == "r":
                    return "resetting is disabled for safety during testing"
                elif tokens[2] == "stop" or tokens[2] == "s":
                    beamsplitter.beamsplitter_wheel.stop()
                    value = beamsplitter.beamsplitter_wheel.true_position()
                    return str(value)
                elif tokens[2] == "goto" or tokens[2] == "g":
                    angle = float(tokens[3])
                    beamsplitter.beamsplitter_wheel.move_absolute(angle, wait=wait)
                    value = beamsplitter.beamsplitter_wheel.true_position()
                    return str(value)
                elif tokens[2] == "nudge" or tokens[2] == "n":
                    angle = float(tokens[3])
                    beamsplitter.beamsplitter_wheel.move_relative(angle, wait=wait)
                    value = beamsplitter.beamsplitter_wheel.true_position()
                    return str(value)
                else:
                    return "ERROR: invalid command received"
            else:
                try:
                    posn = int(tokens[1])
                    beamsplitter.move_position(posn, wait=wait)
                    status = VAMPIRES["beamsplitter_status"]
                    angle = VAMPIRES["beamsplitter_angle"]
                    out = f"({posn}) {status} {{{angle} {beamsplitter.beamsplitter_wheel.unit}}}"
                    return out
                except ValueError:
                    return "ERROR: invalid command received"
        elif tokens[0] == "diffwheel" or tokens[0] == "diff" or tokens[0] == "df":
            if len(tokens) == 1:
                return differential_filter.diffwheel.help_message()
            elif tokens[1] == "status" or tokens[1] == "st":
                idx = VAMPIRES["diffwheel"]
                status = VAMPIRES["diffwheel_status"]
                angle = VAMPIRES["diffwheel_angle"]
                out = f"({idx}) {status} {{t={angle} {differential_filter.diffwheel.unit}}}"
                return out
            elif tokens[1] == "wheel" or tokens[1] == "w":
                if len(tokens) == 2 or tokens[2] == "status" or tokens[2] == "st":
                    value = differential_filter.diffwheel.true_position()
                    return str(value)
                elif tokens[2] == "home" or tokens[2] == "h":
                    differential_filter.diffwheel.home(wait=wait)
                elif tokens[2] == "reset" or tokens[2] == "r":
                    return "resetting is disabled for safety during testing"
                elif tokens[2] == "stop" or tokens[2] == "s":
                    differential_filter.diffwheel.stop()
                    value = differential_filter.diffwheel.true_position()
                    return str(value)
                elif tokens[2] == "goto" or tokens[2] == "g":
                    angle = float(tokens[3])
                    differential_filter.diffwheel.move_absolute(angle, wait=wait)
                    value = differential_filter.diffwheel.true_position()
                    return str(value)
                elif tokens[2] == "nudge" or tokens[2] == "n":
                    angle = float(tokens[3])
                    differential_filter.diffwheel.move_relative(angle, wait=wait)
                    value = differential_filter.diffwheel.true_position()
                    return str(value)
                else:
                    return "ERROR: invalid command received"
            else:
                try:
                    posn = int(tokens[1])
                    differential_filter.move_position(posn, wait=wait)
                    status = VAMPIRES["diffwheel_status"]
                    angle = VAMPIRES["diffwheel_angle"]
                    out = f"({posn}) {status} {{t={angle} {differential_filter.diffwheel.unit}}}"
                    return out
                except ValueError:
                    return "ERROR: invalid command received"
        elif tokens[0] == "pupil" or tokens[0] == "p":
            if len(tokens) == 1 or "-h" in tokens or "--help" in tokens:
                return pupil_wheel.help_message()
            elif tokens[1] == "status" or tokens[1] == "st":
                return pupil_wheel.status(update=update)
            elif tokens[1] == "wheel" or tokens[1] == "w":
                if len(tokens) == 2:
                    return pupil_wheel.pupil_wheel.help_message()
                elif tokens[2] == "status" or tokens[2] == "st":
                    value = pupil_wheel.pupil_wheel.true_position()
                    return str(value)
                elif tokens[2] == "home" or tokens[2] == "h":
                    pupil_wheel.pupil_wheel.home(wait=wait)
                elif tokens[2] == "reset" or tokens[2] == "r":
                    return "resetting is disabled for safety during testing"
                elif tokens[2] == "stop" or tokens[2] == "s":
                    pupil_wheel.pupil_wheel.stop()
                    value = pupil_wheel.pupil_wheel.true_position()
                    return str(value)
                elif tokens[2] == "goto" or tokens[2] == "g":
                    angle = float(tokens[3])
                    pupil_wheel.pupil_wheel.move_absolute(angle, wait=wait)
                    value = pupil_wheel.pupil_wheel.true_position()
                    return str(value)
                elif tokens[2] == "nudge" or tokens[2] == "n":
                    angle = float(tokens[3])
                    pupil_wheel.pupil_wheel.move_relative(angle, wait=wait)
                    value = pupil_wheel.pupil_wheel.true_position()
                    return str(value)
                else:
                    return "ERROR: invalid command received"
            elif tokens[1] == "x":
                if len(tokens) == 2:
                    return pupil_wheel.pupil_stage_x.help_message()
                elif tokens[2] == "status" or tokens[2] == "st":
                    value = pupil_wheel.pupil_stage_x.true_position()
                    return str(value)
                elif tokens[2] == "home" or tokens[2] == "h":
                    pupil_wheel.pupil_stage_x.home(wait=wait)
                elif tokens[2] == "reset" or tokens[2] == "r":
                    return "resetting is disabled for safety during testing"
                elif tokens[2] == "stop" or tokens[2] == "s":
                    pupil_wheel.pupil_stage_x.stop()
                    value = pupil_wheel.pupil_stage_x.true_position()
                    return str(value)
                elif tokens[2] == "goto" or tokens[2] == "g":
                    position = int(tokens[3])
                    pupil_wheel.pupil_stage_x.move_absolute(position, wait=wait)
                    value = pupil_wheel.pupil_stage_x.true_position()
                    return str(value)
                elif tokens[2] == "nudge" or tokens[2] == "n":
                    position = int(tokens[3])
                    pupil_wheel.pupil_stage_x.move_relative(position, wait=wait)
                    value = pupil_wheel.pupil_stage_x.true_position()
                    return str(value)
                else:
                    return "ERROR: invalid command received"
            elif tokens[1] == "y":
                if len(tokens) == 2:
                    return pupil_wheel.pupil_stage_x.help_message()
                elif tokens[2] == "status" or tokens[2] == "st":
                    value = pupil_wheel.pupil_stage_y.true_position()
                    return str(value)
                elif tokens[2] == "home" or tokens[2] == "h":
                    pupil_wheel.pupil_stage_y.home(wait=wait)
                elif tokens[2] == "reset" or tokens[2] == "r":
                    return "resetting is disabled for safety during testing"
                elif tokens[2] == "stop" or tokens[2] == "s":
                    pupil_wheel.pupil_stage_y.stop()
                    value = pupil_wheel.pupil_stage_y.true_position()
                    return str(value)
                elif tokens[2] == "goto" or tokens[2] == "g":
                    position = int(tokens[3])
                    pupil_wheel.pupil_stage_y.move_absolute(position, wait=wait)
                    value = pupil_wheel.pupil_stage_y.true_position()
                    return str(value)
                elif tokens[2] == "nudge" or tokens[2] == "n":
                    position = int(tokens[3])
                    pupil_wheel.pupil_stage_y.move_relative(position, wait=wait)
                    value = pupil_wheel.pupil_stage_y.true_position()
                    return str(value)
                else:
                    return "ERROR: invalid command received"
            else:
                try:
                    posn = int(tokens[1])
                    pupil_wheel.move_position(posn, wait=wait)
                    print(pupil_wheel.status())
                    return pupil_wheel.status(update=update)
                except ValueError:
                    return "ERROR: invalid command received"
        elif tokens[0] == "focus" or tokens[0] == "f":
            if len(tokens) == 1:
                return focus.help_message()
            elif tokens[1] == "status" or tokens[1] == "st":
                value = focus.true_position()
                return str(value)
            elif tokens[1] == "home" or tokens[1] == "h":
                focus.home(wait=wait)
            elif tokens[1] == "reset" or tokens[1] == "r":
                return "resetting is disabled for safety during testing"
            elif tokens[1] == "stop" or tokens[1] == "s":
                focus.stop()
                value = focus.true_position()
                return str(value)
            elif tokens[1] == "goto" or tokens[1] == "g":
                position = float(tokens[2])
                focus.move_absolute(position, wait=wait)
                value = focus.true_position()
                return str(value)
            elif tokens[1] == "nudge" or tokens[1] == "n":
                position = float(tokens[2])
                focus.move_relative(position, wait=wait)
                value = focus.true_position()
                return str(value)
            else:
                return "ERROR: invalid command received"
        elif tokens[0] == "qwp" or tokens[0] == "q":
            if tokens[1] == "1":
                qwp = qwp_1
            elif tokens[1] == "2":
                qwp = qwp_2
            else:
                return qwp_1.help_message()
            if len(tokens) < 3:
                return qwp_1.help_message()
            elif tokens[2] == "status" or tokens[2] == "st":
                value = qwp.true_position()
                return str(value)
            elif tokens[2] == "home" or tokens[2] == "h":
                qwp.home(wait=wait)
            elif tokens[2] == "reset" or tokens[2] == "r":
                return "resetting is disabled for safety during testing"
            elif tokens[2] == "stop" or tokens[2] == "s":
                qwp.stop()
                value = qwp.true_position()
                return str(value)
            elif tokens[2] == "goto" or tokens[2] == "g":
                angle = float(tokens[3])
                qwp.move_absolute(angle, wait=wait)
                value = qwp.true_position()
                return str(value)
            elif tokens[2] == "nudge" or tokens[2] == "n":
                angle = float(tokens[3])
                qwp.move_relative(angle, wait=wait)
                value = qwp.true_position()
                return str(value)
            else:
                return "ERROR: invalid command received"
        else:
            return "ERROR: invalid command received"
