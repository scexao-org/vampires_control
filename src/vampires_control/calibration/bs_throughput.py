import logging
import os
import time
from pathlib import Path

import click
import numpy as np
import tqdm.auto as tqdm
from scxconf.pyrokeys import SCEXAO, VAMPIRES
from swmain.network.pyroclient import connect

from vampires_control.acquisition.manager import VCAMManager

conf_dir = Path(os.getenv("CONF_DIR", f"{os.getenv('HOME')}/src/vampires_control/conf/"))

# set up logging
formatter = logging.Formatter("%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class BSCalManager:
    """
    BSCalManager

    Measures flux to both cameras for a beamsplitter. To remove polarization-dependent effects
    this measures the flux with a linear polarizer at many angles from 0 to 180 deg.

    This is designed to be run using flat frames in the "Open" filter, so prepare the SCExAO source
    with the integrating sphere

        sc2 $ src_select ski
        sc2 $ intsphere
        sc2 $ vampires_filter open
    """

    LP_POSNS = np.linspace(0, 180, 37)

    def __init__(self, bs: str = "PBS", parity: bool = False, debug=False):
        # store properties
        self.debug = debug
        self.parity = parity
        if self.debug:
            # filthy, disgusting
            logger.setLevel(logging.DEBUG)
            logger.handlers[0].setLevel(logging.DEBUG)
        # connect
        self.bs_wheel = connect(VAMPIRES.BS)
        self.focus = connect(VAMPIRES.FOCUS)
        self.polarizer = connect(SCEXAO.POL)
        # check bs and match to config
        self.bs_idx = self.bs_wheel.get_config_index_from_name(bs)

        # camera setup (skip cam 2 if open)
        if bs.lower() != "open":
            self.cameras = {1: connect("VCAM1"), 2: connect("VCAM2")}
            self.managers = {1: VCAMManager(1), 2: VCAMManager(2)}
        else:
            self.cameras = {1: connect("VCAM1")}
            self.managers = {1: VCAMManager(1)}
            # hack: if "open" we want to use the 3rd BS position
            self.bs_idx = 3

    def prepare(self):
        if self.debug:
            logger.debug("PREPARING VAMPIRES")
        configurations = self.bs_wheel.get_configurations()
        for config in configurations:
            if config["idx"] == self.bs_idx:
                name = config["name"]
                break
        if self.debug:
            logger.debug(f"Play pretend: MOVING BS TO {self.bs_idx}: {name}")
            return
        logger.info(f"Moving beamsplitter to {self.bs_idx}: {name}")
        self.bs_wheel.move_configuration_idx(self.bs_idx)
        if name.lower == "open":
            self.focus.move_configuration("single")
        else:
            self.focus.move_configuration("standard")

    def run(self, confirm=False, time_per_cube=5):
        logger.info("Beginning BS calibration")
        # prepare cameras
        self.prepare()

        if confirm:
            click.confirm("Adjust camera settings and confirm when ready", default=True, err=True)

        logger.info("Starting LP loop")
        angles = self.LP_POSNS
        if self.parity:
            angles = angles[::-1]
        pbar = tqdm.tqdm(angles, desc="LP positions")
        try:
            for lp_ang in pbar:
                pbar.write(f"Pol: {lp_ang:.02f}°")
                self.pause_cameras()
                self.move_lp(lp_ang)
                self.resume_cameras()
                time.sleep(time_per_cube)
        finally:
            self.pause_cameras()
        logger.info("Calibration complete, don't forget to take darks!")

    def move_lp(self, angle):
        if self.debug:
            logger.debug(f"MOVING LP TO {angle}")
            return
        assumed_offset = 90  # deg
        actual_angle = (angle + assumed_offset) % 360
        self.polarizer.move_absolute(actual_angle)
        time.sleep(0.5)
        for cam in self.cameras.values():
            cam.set_keyword("X_POLARP", actual_angle)

    def pause_cameras(self):
        if self.debug:
            logger.debug("PLAY PRETEND MODE: turn VAMPIRES off")
            return
        for mgr in self.managers.values():
            mgr.pause_acquisition()

    def resume_cameras(self):
        if self.debug:
            logger.debug("PLAY PRETEND MODE: turn VAMPIRES on")
            return
        for mgr in self.managers.values():
            mgr.start_acquisition()


@click.command("bs_calib")
@click.argument("bs", type=click.Choice(["PBS", "NPBS", "Open"], case_sensitive=False))
@click.option("-t", "--time", type=float, default=5, prompt="Time (s) per position")
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
@click.option("-p/-np", "--parity/--no-parity", default=False, help="Parity flip the angles")
def main(time, bs: str, debug=False, parity: bool = False):
    manager = BSCalManager(bs=bs, debug=debug, parity=parity)
    manager.run(time_per_cube=time)


if __name__ == "__main__":
    main()
