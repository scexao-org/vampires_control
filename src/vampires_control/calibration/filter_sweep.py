import logging
import os
import time
from pathlib import Path

import click
import numpy as np
import pandas as pd
import tqdm.auto as tqdm
from scxconf.pyrokeys import VAMPIRES

from swmain.network.pyroclient import connect
from swmain.redis import get_values

from ..acquisition.manager import VCAMManager

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


class FilterSweeper:
    """
    FilterSweeper
    """

    FILTERS = [
        "Open",
        "625-50",
        "675-50",
        "725-50",
        "750-50",
        "775-50",
    ]
    NB_FILTERS = ["Halpha", "SII"]

    def __init__(self, debug=False):
        self.cameras = {
            1: connect("VCAM1"),
            2: connect("VCAM2"),
        }
        self.managers = {
            1: VCAMManager(1),
            2: VCAMManager(2),
        }
        self.filt = connect(VAMPIRES.FILT)
        # self.diff_filt = connect(VAMPIRES.DIFF)
        self.debug = debug
        if self.debug:
            # filthy, disgusting
            logger.setLevel(logging.DEBUG)
            logger.handlers[0].setLevel(logging.DEBUG)
        self.conf_data = pd.read_csv(
            conf_dir / "data" / "conf_vampires_qwp_filter_data.csv"
        )

    def move_filter(self, filt, wait=False):
        if self.debug:
            logger.debug(f"MOVING FILTER TO {filt}")
            return

        self.filt.move_configuration(filt)
        if wait:
            self.wait_for_qwp_pos(filt)

    def run(self, time_per_cube=5, parity=False, wait=False):
        logger.info("Starting filter sweep")
        filts = self.FILTERS
        if parity:
            filts = list(reversed(filts))

        for filt in tqdm.tqdm(filts, total=len(self.FILTERS), desc="Filters"):
            self.pause_cameras()
            self.move_filter(filt, wait=wait)
            self.resume_cameras()
            time.sleep(time_per_cube)
        self.pause_cameras()

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

    def wait_for_qwp_pos(self, filt):
        indices = self.conf_data["filter"] == filt
        conf_row = self.conf_data.loc[indices]

        qwp1_pos = float(conf_row["qwp1"].iloc[0])
        qwp2_pos = float(conf_row["qwp2"].iloc[0])
        while True:
            last_qwp1, last_qwp2 = get_values(("U_QWP1", "U_QWP2")).values()
            if np.abs(last_qwp1 - qwp1_pos) < 1 and np.abs(last_qwp2 - qwp2_pos) < 1:
                break
            time.sleep(0.5)


@click.command("filter_sweep")
@click.option("-t", "--time", type=float, default=5, prompt="Time (s) per position")
@click.option(
    "-w/-nw", "--wait/--no-wait", default=True, prompt="Wait for QWPs to settle"
)
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
def main(time, wait=False, debug=False):
    manager = FilterSweeper(debug=debug)
    manager.run(time_per_cube=time, wait=wait)


if __name__ == "__main__":
    main()
