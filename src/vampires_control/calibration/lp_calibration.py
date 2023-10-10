import logging
import os
import time
from pathlib import Path

import click
import numpy as np
import pandas as pd
import tqdm.auto as tqdm
from scxconf.pyrokeys import SCEXAO, VAMPIRES

from swmain.network.pyroclient import connect
from swmain.redis import get_values

from ..acquisition.manager import VCAMManager

conf_dir = Path(
    os.getenv("CONF_DIR", f"{os.getenv('HOME')}/src/vampires_control/conf/")
)

# set up logging
formatter = logging.Formatter(
    "%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class LPCalManager:
    """
    LPCalManager
    """

    LP_POSNS = np.linspace(0, 180, 16)
    STANDARD_FILTERS = (
        "Open",
        "625-50",
        "675-50",
        "725-50",
        "750-50",
        "775-50",
    )
    NB_FILTERS = ("Halpha", "SII")

    def __init__(
        self,
        mode: str = "standard",
        use_flc: bool = False,
        debug=False,
    ):
        # store properties
        self.mode = mode
        self.filters = self.ask_for_filters()
        self.use_flc = use_flc
        self.debug = debug
        if self.debug:
            # filthy, disgusting
            logger.setLevel(logging.DEBUG)
            logger.handlers[0].setLevel(logging.DEBUG)
        self.conf_data = pd.read_csv(
            conf_dir / "data" / "conf_vampires_qwp_filter_data.csv"
        )

        # camera setup
        self.cameras = {
            1: connect("VCAM1"),
            2: connect("VCAM2"),
        }
        self.managers = {
            1: VCAMManager(1),
            2: VCAMManager(2),
        }

        # connect
        self.filt = connect(VAMPIRES.FILT)
        self.diff_filt = connect(VAMPIRES.DIFF)

        if self.use_flc:
            self.flc = connect(VAMPIRES.FLC)

        self.polarizer = connect(SCEXAO.POL)

    def ask_for_filters(self):
        if self.mode == "standard":
            choices = self.STANDARD_FILTERS
        elif self.mode == "NB":
            choices = self.NB_FILTERS
        elif self.mode == "MBI":
            return ("Open",)

        filts = click.prompt(
            "Which filter(s) would you like to test",
            type=click.Choice(["all", *choices], case_sensitive=False),
            default="all",
        )
        if filts == "all":
            return choices
        else:
            return (filts,)

    def prepare(self):
        if self.debug:
            logger.debug("PREPARING VAMPIRES")
            if self.mode in ("MBI", "NB"):
                logger.debug("PREPARING VAMPIRES:FILTER")
            return

        # prepare vampires
        mbi = "Dichroics" if self.mode == "MBI" else "Mirror"
        # prep_pdi.callback(flc=self.flc, mbi=mbi)
        if self.mode in ("MBI", "NB"):
            self.filt.move_configuration("Open")

    def run(self, confirm=False, **kwargs):
        logger.info("Beginning DRR calibration")
        self.prepare()

        parity = False
        for filt in tqdm.tqdm(self.filters, desc="Filter"):
            self.move_filters(filt)
            self.wait_for_qwp_pos(filt)
            # prepare cameras
            if confirm and not click.confirm(
                "Adjust camera settings and confirm when ready, no to skip to next filter",
                default=True,
            ):
                continue
            self.iterate_one_filter(parity=parity, **kwargs)
            # every other sequence flip the IMR angle order to minimize travel
            parity = not parity

    def iterate_one_filter(self, time_per_cube=1, parity=False):
        logger.info("Starting LP loop")
        N = len(self.LP_POSNS)
        angles = self.LP_POSNS
        if parity:
            angles = reversed(self.LP_POSNS)
        pbar = tqdm.tqdm(angles, total=N, desc="Generator")
        for lp_ang in pbar:
            pbar.write(f"Pol: {lp_ang:.02f}°")
            self.pause_cameras()
            self.move_lp(lp_ang)
            self.resume_cameras()
            time.sleep(time_per_cube)
        self.pause_cameras()

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

    def move_filters(self, filt):
        logger.info(f"Moving filter to {filt}")
        if self.debug:
            return
        if filt in self.STANDARD_FILTERS:
            self.filt.move_configuration(filt)
        elif filt in self.NB_FILTERS:
            if filt == "Halpha":
                self.diff_filt.move_configuration_idx(3)
            elif filt == "SII":
                self.diff_filt.move_configuration_idx(3)

    def wait_for_qwp_pos(self, filt):
        if self.debug or self.use_qwp:
            return
        indices = self.conf_data["filter"] == filt
        conf_row = self.conf_data.loc[indices]

        qwp1_pos = float(conf_row["qwp1"].iloc[0])
        qwp2_pos = float(conf_row["qwp2"].iloc[0])
        while True:
            last_qwp1, last_qwp2 = get_values(("U_QWP1", "U_QWP2")).values()
            if (
                np.abs(last_qwp1 - qwp1_pos) < 0.1
                and np.abs(last_qwp2 - qwp2_pos) < 0.1
            ):
                break
            time.sleep(0.5)

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


@click.command("lp_calib")
@click.option(
    "-m",
    "--mode",
    default="standard",
    type=click.Choice(["standard", "MBI", "NB"], case_sensitive=False),
    prompt="Select calibration mode",
)
@click.option("-t", "--time", type=float, default=5, prompt="Time (s) per position")
@click.option("-f/-nf", "--flc/--no-flc", default=False, prompt="Use FLC")
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
def main(time, mode: str, flc: bool = False, debug=False):
    manager = LPCalManager(mode=mode, use_flc=flc, debug=debug)
    manager.run(time_per_cube=time)


if __name__ == "__main__":
    main()
