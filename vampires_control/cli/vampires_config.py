#!/usr/bin/env python
from docopt import docopt
from pathlib import Path
import sys
import logging
import time
from logging.handlers import SysLogHandler

from vampires_control.devices.devices import (
    beamsplitter,
    differential_filter,
    focus,
    pupil_wheel,
    qwp_1,
    qwp_2,
)

formatter = "%(asctime)s|%(levelname)s|%(name)s - %(message)s"
logging.basicConfig(
    level=logging.DEBUG, format=formatter, handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("vampires_config")


numbers = [pos["number"] for pos in beamsplitter.positions["positions"]]
descriptions = [pos["name"] for pos in beamsplitter.positions["positions"]]

positions = "\n".join(f"  {i} {d}" for i, d in zip(numbers, descriptions))

__doc__ = f"""
Load or create configurations for VAMPIRES to facilitate quick transitions between its many observing modes. The config files are stored in JSON. There is an additional file mapping names to JSON files as official modes.

Usage:
    vampires_config <name> [-y | --yes] [-w | --wait]
    vampires_config (-l | --load) <file>  [-y | --yes] [-w | --wait]
    vampires_config (-s | --save) <name> [<file>]
    vampires_config (-h | --help)

Options:
    -h --help   Show this screen
    -l --load <file> Load a custom config file
    -s --save <name> [<file>] Save the current state to a config with the given name at the given file location, which will default to the config directory.
    -w --wait   Block command until position has been reached, for applicable commands

Configs:
{positions}
"""

CONFIG_FILENAME_MAP = {}

CONFIG_ACTION_MAP = {
    "name": None,
    "beamsplitter": beamsplitter.move_position,
    "diffwheel": differential_filter.move_position,
    "focus": focus.move_absolute,
    "qwp1": qwp_1.move_absolute,
    "qwp2": qwp_2.move_absolute,
    "pupil": pupil_wheel.move_position,
}

CONFIG_INFO_MAP = {
    "name": None,
    "beamsplitter": beamsplitter.get_position,
    "diffwheel": differential_filter.move_position,
    "focus": focus.move_absolute,
    "qwp1": qwp_1.move_absolute,
    "qwp2": qwp_2.move_absolute,
    "pupil": pupil_wheel.move_position,
}

# setp 4. action
def main():
    args = docopt(__doc__)
    if len(sys.argv) == 1:
        print(args)
    else:
        if args["--save"]:
            pass
        elif args["--load"]:
            filename = args["--load"]
        else:
            filename = CONFIG_FILENAME_MAP[args["<name>"]]


if __name__ == "__main__":
    main()
