import logging
import time

import click
import numpy as np
import pandas as pd
import tqdm.auto as tqdm
from paramiko import AutoAddPolicy, SSHClient
from scxconf.pyrokeys import VAMPIRES

from swmain.network.pyroclient import connect
from swmain.redis import get_values

from ..acquisition.manager import VCAMManager

# set up logging
formatter = logging.Formatter(
    "%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("iwa_sweep")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

base_cmd = ["ssh", "scexao2", "src_fib"]


class IWAScanner:
    FIBX_ZP = 7.7
    FIBY_ZP = 23.15

    """
    IWAScanner

    This tool uses the calibration source fiber to scan across the focal plane
    allowing measurement of the inner working angle (IWA) of a focal plane mask.

    In general, this will simply step the fiber, pause for acquisition, and repeat.
    By default this class only uses VCAM1.
    """

    def __init__(self, debug=False, plot=False):
        self.camera = VCAMManager(1)
        self.fieldstop = connect(VAMPIRES.FIELDSTOP)
        self.debug = debug
        if self.debug:
            # filthy, disgusting
            logger.setLevel(logging.DEBUG)
            logger.handlers[0].setLevel(logging.DEBUG)
        # prepare SSH client to sc2 for fiber
        # TODO add pyro class for source fiber to device_control
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.client.load_system_host_keys()
        logger.info("Connecting SSH client")
        self.client.connect(
            "scexao2",
            username="scexao",
            disabled_algorithms={"pubkeys": ("rsa-sha2-256", "rsa-sha2-512")},
        )

    def move_src_fiberx(self, x):
        if self.debug:
            logger.debug(f"MOVING FIBER TO x={x}")
            return

        cmdx = f"src_fib x goto {x}"
        logger.debug(cmdx)
        self.client.exec_command(cmdx)
        time.sleep(1)

    def move_src_fibery(self, y):
        if self.debug:
            logger.debug(f"MOVING FIBER TO y={y}")
            return

        cmdy = f"src_fib y goto {y}"
        logger.debug(cmdy)
        self.client.exec_command(cmdy)
        time.sleep(1)

    def run(self, time_per_cube=0.5, step=2e-3, r=0.15):
        logger.info("Starting fiber positioning loop")

        posns_x = self.FIBX_ZP + np.arange(-r, r + step / 2, step)
        # posns_y = self.FIBY_ZP + np.array((0,))
        posns_y = self.FIBY_ZP + np.array((-step, 0, step))
        posns = []
        parity_flip = False
        try:
            for xpos in tqdm.tqdm(posns_x, desc="x"):
                self.pause_cameras()
                self.move_src_fiberx(xpos)

                ys = posns_y[::-1] if parity_flip else posns_y
                for ypos in tqdm.tqdm(ys, desc="y", leave=False):
                    self.pause_cameras()
                    self.move_src_fibery(ypos)
                    posns.append((xpos, ypos))
                    self.resume_cameras()
                    time.sleep(time_per_cube)
                parity_flip = not parity_flip
        finally:
            self.pause_cameras()

        return np.array(posns)

    def pause_cameras(self):
        if self.debug:
            logger.debug("PLAY PRETEND MODE: turn VAMPIRES off")
            return
        self.camera.pause_acquisition()

    def resume_cameras(self):
        if self.debug:
            logger.debug("PLAY PRETEND MODE: turn VAMPIRES on")
            return
        self.camera.start_acquisition()


@click.command("iwa_scan")
@click.option("-t", "--time", type=float, default=1, prompt="Time (s) per position")
@click.option("-s", "--step", type=float, default=2e-3, prompt="Step size in mm")
@click.option(
    "-r", "--radius", type=float, default=0.2, prompt="Radius of fiber circle in mm"
)
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
def main(time, step, radius, debug=False):
    manager = IWAScanner(debug=debug)
    manager.run(time_per_cube=time, step=step, r=radius)


if __name__ == "__main__":
    main()
