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
        self.client.connect(
            "scexao2",
            username="scexao",
            disabled_algorithms={"pubkeys": ("rsa-sha2-256", "rsa-sha2-512")},
        )

    def move_src_fiber(self, x):
        if self.debug:
            logger.debug(f"MOVING FIBER TO {x}")
            return

        cmdx = f"src_fib x goto {x}"
        logger.debug(cmdx)
        self.client.exec_command(cmdx)

    def run(self, time_per_cube=1, step=2e-3, r=0.166):
        logger.info("Connecting SSH client")
        self.client.connect(
            "scexao2",
            username="scexao",
            disabled_algorithms={"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]},
        )

        logger.info("Starting fiber positioning loop")

        posns_x = 7.7 + np.arange(-r, r + step / 2, step)
        try:
            for xpos in tqdm.tqdm(posns_x):
                self.pause_cameras()
                self.move_src_fiber(xpos)
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
            self.camera.pause_acquisition()

    def resume_cameras(self):
        if self.debug:
            logger.debug("PLAY PRETEND MODE: turn VAMPIRES on")
        else:
            self.camera.start_acquisition()


@click.command("iwa_scan")
@click.option("-t", "--time", type=float, default=1, prompt="Time (s) per position")
@click.option("-s", "--step", type=float, default=2e-3, prompt="Step size in mm")
@click.option(
    "-r", "--radius", type=float, default=0.166, prompt="Radius of fiber circle in mm"
)
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
def main(time, step, radius, debug=False):
    manager = IWAScanner(debug=debug)
    manager.run(time_per_cube=time, step=step, r=radius)


if __name__ == "__main__":
    main()
