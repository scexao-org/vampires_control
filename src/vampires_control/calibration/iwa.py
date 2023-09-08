import logging
import os
import subprocess
import time
from pathlib import Path

import click
import numpy as np
import pandas as pd
import tqdm.auto as tqdm
from scxconf.pyrokeys import VAMPIRES

from swmain.network.pyroclient import connect
from swmain.redis import get_values
from vampires_control.acquisition.acquire import (pause_acquisition,
                                                  resume_acquisition)

# set up logging
formatter = logging.Formatter(
    "%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("filter_sweep")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


conf_dir = Path(
    os.getenv("CONF_DIR", f"{os.getenv('HOME')}/src/vampires_control/conf/")
)


base_cmd = ["ssh", "scexao2", "src_fib"]


class IWAScanner:
    """
    IWAScanner
    """

    def __init__(self, debug=False):
        self.cameras = {
            1: connect("VCAM1"),
            2: connect("VCAM2"),
        }
        self.fieldstop = connect(VAMPIRES.FIELDSTOP)
        self.debug = debug
        if self.debug:
            # filthy, disgusting
            logger.setLevel(logging.DEBUG)
            logger.handlers[0].setLevel(logging.DEBUG)

    def move_src_fiber(self, x, y):
        if self.debug:
            logger.debug(f"MOVING FIBER TO {x}, {y}")
            return

        cmdx = base_cmd + ["x", "goto", str(x)]
        logger.debug(cmdx)
        subprocess.run(cmdx, capture_output=True)

        cmdy = base_cmd + ["y", "goto", str(y)]
        logger.debug(cmdy)
        subprocess.run(cmdy, capture_output=True)

    def run(self, time_per_cube=1, n=10, r=0.12):
        logger.info("Starting fiber positioning loop")

        posns_x = 7.7 + np.linspace(-r, r, n)
        posns_y = 23.15 + np.linspace(-r, r, n)
        grid_x, grid_y = np.meshgrid(posns_x, posns_y)
        radii = np.hypot(grid_x - 7.7, grid_y - 23.15)
        mask = radii < r
        x_left = grid_x[mask]
        y_left = grid_y[mask]
        try:
            for xpos, ypos in tqdm.tqdm(
                zip(x_left.ravel(), y_left.ravel()), total=mask.sum()
            ):
                self.pause_cameras()
                self.move_src_fiber(xpos, ypos)
                time.sleep(1)
                self.resume_cameras()
                time.sleep(time_per_cube)
        finally:
            self.pause_cameras()

    def pause_cameras(self):
        if self.debug:
            logger.debug("PLAY PRETEND MODE: turn VAMPIRES off")
        else:
            # self.vamp_trig.disable()
            pause_acquisition()

    def resume_cameras(self):
        if self.debug:
            logger.debug("PLAY PRETEND MODE: turn VAMPIRES on")
        else:
            resume_acquisition()


@click.command("iwa_scan")
@click.option("-t", "--time", type=float, default=5, prompt="Time (s) per position")
@click.option(
    "-n", "--num-pos", type=int, default=11, prompt="Number of stops per axis"
)
@click.option(
    "-r", "--radius", type=float, default=0.12, prompt="Radius of fiber circle in mm"
)
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
def main(time, num_pos, radius, debug=False):
    manager = IWAScanner(debug=debug)
    manager.run(time_per_cube=time, n=num_pos, r=radius)


if __name__ == "__main__":
    main()
