#!/usr/bin/env python
from docopt import docopt
from pathlib import Path
import sys
import logging
import time
from logging.handlers import SysLogHandler

from vampires_control.devices.devices import qwp_1, qwp_2

formatter = "%(asctime)s|%(levelname)s|%(name)s - %(message)s"
logging.basicConfig(
    level=logging.DEBUG, format=formatter, handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("vampires_qwp")

__doc__ = f"""
Usage:
    vampires_qwp (1|2) (status|target|home|goto|nudge|stop|reset) [<angle>] [-h | --help] [-w | --wait]

Options:
    -h --help   Show this screen
    -w --wait   Block command until position has been reached, for applicable commands

Rotator commands:
    status          Returns the current angle of the selected QWP rotator, in {qwp_1.unit}
    target          Returns the target angle of the selected QWP rotator, in {qwp_1.unit}
    home            Homes the selected QWP rotator
    goto  <angle>   Rotate the selected QWP to the given angle, in {qwp_1.unit}
    nudge <angle>   Rotate the selected QWP relatively by the given angle, in {qwp_1.unit}
    stop            Stop the selected QWP rotator
    reset           Reset the selected QWP rotator
"""

# setp 4. action
def main():
    args = docopt(__doc__)
    if len(sys.argv) == 1:
        print(args)

    qwp = qwp_1 if args["1"] else qwp_2
    if args["status"]:
        print(qwp.true_position())
    elif args["target"]:
        print(qwp.target_position())
    elif args["home"]:
        qwp.home(wait=args["--wait"])
    elif args["goto"]:
        angle = float(args["<angle>"])
        qwp.move_absolute(angle, wait=args["--wait"])
    elif args["nudge"]:
        rel_angle = float(args["<angle>"])
        qwp.move_relative(rel_angle, wait=args["--wait"])
    elif args["stop"]:
        qwp.stop()
    elif args["reset"]:
        qwp.reset()
    else:
        print(args)


if __name__ == "__main__":
    main()
