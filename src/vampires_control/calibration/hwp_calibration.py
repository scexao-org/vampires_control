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
logger = logging.getLogger("hwp_cals")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class HWPOptimizer:
    """
    HWPOptimizer
    """

    IMR_POSNS = [45, 57.5, 70, 82.5, 95, 107.5, 120, 132.5]
    HWP_POSNS = [0, 11.25, 22.5, 33.75, 45, 56.25, 67.5, 78.75]
    EXT_HWP_POSNS = [90, 101.25, 112.5, 123.75, 135, 146.25, 157.5, 168.75]
    IMR_INDS_HWP_EXT = [2, 5]
    FILTERS = [
        "625-50",
        "675-50",
        "725-50",
        "750-50",
        "775-50",
        "Open",
    ]  # , "Halpha", "SII"]

    def __init__(self, debug=False):
        self.cameras = {
            1: connect("VCAM1"),
            2: connect("VCAM2"),
        }
        self.flc = connect(VAMPIRES.FLC)
        self.filt = connect(VAMPIRES.FILT)
        self.diff_filt = connect(VAMPIRES.DIFF)
        self.imr = ImageRotator.connect()
        self.wpu = WPU()
        self.debug = debug
        if self.debug:
            # filthy, disgusting
            logger.setLevel(logging.DEBUG)
            logger.handlers[0].setLevel(logging.DEBUG)

    def prepare(self, flc: bool = False):
        if self.debug:
            logger.debug("PREPARING VAMPIRES")
            logger.debug("PREPARING WPU:POLARIZER")
            logger.debug("PREPARING WPU:HWP")
        else:
            # prepare vampires
            prep_pdi(flc=flc)
            # prepare wpu
            self.wpu.spp.move_in()  # move polarizer in
            self.wpu.shw.move_in()  # move HWP in

    def iterate_one_filter(self, time_per_cube=5, parity=False, do_extended_range=True):
        logger.info("Starting HWP + IMR loop")
        imr_range = self.IMR_POSNS
        if parity:
            imr_range = reversed(imr_range)

        for i, imrang in tqdm.tqdm(
            enumerate(imr_range), total=len(self.IMR_POSNS), desc="IMR"
        ):
            self.pause_cameras()
            if self.debug:
                logger.debug(f"MOVING IMR TO {imrang}")
            else:
                self.imr.move_absolute(imrang)
            hwp_range = self.HWP_POSNS
            if do_extended_range and i in self.IMR_INDS_HWP_EXT:
                hwp_range += self.EXT_HWP_POSNS
            N = len(hwp_range)
            if i % 2 == 0:
                hwp_range = reversed(hwp_range)
            for hwpang in tqdm.tqdm(hwp_range, total=N, desc="HWP"):
                self.pause_cameras()
                if self.debug:
                    logger.debug(f"MOVING HWP TO {hwpang}")
                else:
                    self.wpu.hwp.move_absolute(hwpang)
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

    def run(self, flc: bool = False, **kwargs):
        logger.info("Beginning HWP calibration")
        self.prepare(flc=flc)

        for config in tqdm.tqdm(self.FILTERS, desc="Filter"):
            # if config == "Halpha":
            #     self.filt.move_configuration("Open")
            #     self.diff_filt.move_configuration
            # elif config == "SII":
            #     self.filt.move_configuration("Open")
            #     continue
            # else:
            logger.info(f"Moving filter to {config}")
            if not self.debug:
                self.filt.move_configuration(config)
            # prepare cameras
            if not click.confirm(
                "Adjust camera settings and confirm when ready, no to skip to next filter",
                default=True,
            ):
                continue
            self.iterate_one_filter(**kwargs)


@click.command("hwp_calib")
@click.option("-t", "--time", type=float, default=5, prompt="Time (s) per position")
@click.option("-f/-nf", "--flc/--no-flc", default=False, prompt="Use FLC")
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
def main(time, flc: bool = False, debug=False):
    manager = HWPOptimizer(debug=debug)
    manager.run(flc=flc, time_per_cube=time)


if __name__ == "__main__":
    main()
