#!/usr/bin/env python
from docopt import docopt
import os

from vampires_control.devices.devices import (
    beamsplitter,
    differential_filter,
    focus,
    pupil_wheel,
)

NOMINAL_FOCUS = 16


__doc__ = f"""
Returns VAMPIRES to its nominal bench state.

1. Returns beamsplitter to polarizing cube
2. Returns differential wheel to Open/Open
3. Moves pupil wheel to "EmptySlot"
4. Moves focus to {NOMINAL_FOCUS} mm
5. Removes any focal plane masks

Usage:
    vampires_nominal [-h | --help]

Options:
    -h --help      Display this help message
"""


def main():
    args = docopt(__doc__)
    # 1. Return beamsplitter to 50/50 polarizing
    beamsplitter.move_position(2)
    # 2. Differential filter wheel is open
    differential_filter.move_position(2)
    # 3. Pupil wheel to Empty slot
    pupil_wheel.move_position(1)
    # 4. Return focus to 16 mm
    focus.move_absolute(NOMINAL_FOCUS)
    # 5. Remove focal plane mask
    fieldstop_nominal = 5
    # have to hard-code path because PATH doesn't include
    # Instrument-Control-Main scripts over SSH
    cmd_path = "/home/scexao/bin/devices/vampires_fieldstop"
    os.system(f"ssh scexao@scexao2 '{cmd_path} {fieldstop_nominal}'")


if __name__ == "__main__":
    main()
