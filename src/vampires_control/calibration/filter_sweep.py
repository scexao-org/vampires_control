import logging
import time

import click
import numpy as np
import tqdm.auto as tqdm
from device_control.facility import WPU, ImageRotator
from scxconf.pyrokeys import VAMPIRES

from swmain.network.pyroclient import connect
from vampires_control.acquisition.acquire import (pause_acquisition,
                                                  resume_acquisition)
from vampires_control.configurations import prep_pdi

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
    ]  # , "Halpha", "SII"]

    def __init__(self, debug=False):
        self.cameras = {
            1: connect("VCAM1"),
            2: connect("VCAM2"),
        }
        self.filt = connect(VAMPIRES.FILT)
        self.imr = ImageRotator.connect()
        self.wpu = WPU()
        self.debug = debug
        if self.debug:
            # filthy, disgusting
            logger.setLevel(logging.DEBUG)
            logger.handlers[0].setLevel(logging.DEBUG)

    def run(self, time_per_cube=5, parity=False):
        logger.info("Starting HWP + IMR loop")
        filts = self.FILTERS
        if parity:
            filts = reversed(filts)

        for filt in tqdm.tqdm(filts, total=len(self.FILTERS), desc="Filters"):
            self.pause_cameras()
            if self.debug:
                logger.debug(f"MOVING FILTER TO {filt}")
            else:
                self.filt.move_configuration(filt)
            self.resume_cameras()
            time.sleep(time_per_cube)
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


@click.command("filter_sweep")
@click.option("-t", "--time", type=float, default=5, prompt="Time (s) per position")
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
def main(time, debug=False):
    manager = FilterSweeper(debug=debug)
    manager.run(time_per_cube=time)


if __name__ == "__main__":
    main()
