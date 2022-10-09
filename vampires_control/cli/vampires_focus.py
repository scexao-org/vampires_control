#!/usr/bin/env python
from docopt import docopt
from pathlib import Path
import sys
import logging
import time
from logging.handlers import SysLogHandler

from vampires_control.devices.devices import focus

formatter = "%(asctime)s|%(levelname)s|%(name)s - %(message)s"
logging.basicConfig(
    level=logging.DEBUG, format=formatter, handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("vampires_focus")

__doc__ = f"""
Usage:
    vampires_focus (status|target|home|goto|nudge|stop|reset) [<position>] [-h | --help] [-w | --wait]

Options:
    -h --help   Show this screen
    -w --wait   Block command until position has been reached, for applicable commands

Stage commands:
    status          Returns the current position of the focus stage, in {focus.unit}
    target          Returns the target position of the focus stage, in {focus.unit}
    home            Homes the focus stage
    goto  <pos>     Move the focus stage to the given position, in {focus.unit}
    nudge <pos>     Move the focus stage relatively by the given distance, in {focus.unit}
    stop            Stop the focus stage
    reset           Reset the focus stage
"""

# setp 4. action
def main():
    args = docopt(__doc__)
    if len(sys.argv) == 1:
        print(args)
    elif args["status"]:
        print(focus.true_position())
    elif args["target"]:
        print(focus.target_position())
    elif args["home"]:
        focus.home(wait=args["--wait"])
    elif args["goto"]:
        pos = float(args["<position>"])
        focus.move_absolute(pos, wait=args["--wait"])
    elif args["nudge"]:
        rel_pos = float(args["<position>"])
        focus.move_relative(rel_pos, wait=args["--wait"])
    elif args["stop"]:
        focus.stop()
    elif args["reset"]:
        focus.reset()
    else:
        print(args)

if __name__ == "__main__":
    main()