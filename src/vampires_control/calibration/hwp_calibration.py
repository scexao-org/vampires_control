import logging
import time

import click
import numpy as np
import tqdm.auto as tqdm
from scxconf.pyrokeys import VAMPIRES

from device_control.facility import WPU, ImageRotator
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

    def move_imr(self, angle):
        if self.debug:
            logger.debug(f"MOVING IMR TO {angle}")
            return

        # move image rotator to position
        self.imr.move_absolute(angle)
        while np.abs(self.imr.get_position() - angle) > 1:
            time.sleep(0.5)

    def move_hwp(self, angle):
        if self.debug:
            logger.debug(f"MOVING HWP TO {angle}")
            return

        # move HWP to position
        self.wpu.hwp.move_absolute(angle)
        while np.abs(self.wpu.hwp.get_position() - angle) > 1:
            time.sleep(0.5)

        # update camera SHM keywords
        hwp_status = self.wpu.hwp.get_status()
        qwp_status = self.wpu.qwp.get_status()
        for cam in self.cameras.values():
            cam.set_keyword("RET-ANG1", hwp_status["pol_angle"])
            cam.set_keyword("RET-POS1", hwp_status["position"])
            cam.set_keyword("RET-ANG2", qwp_status["pol_angle"])
            cam.set_keyword("RET-POS2", qwp_status["position"])

    def iterate_one_filter(self, time_per_cube=5, parity=False, do_extended_range=True):
        logger.info("Starting HWP + IMR loop")
        imr_range = self.IMR_POSNS
        if parity:
            imr_range = list(reversed(imr_range))

        pbar = tqdm.tqdm(imr_range, desc="IMR")
        for i, imrang in enumerate(pbar):
            self.pause_cameras()
            self.move_imr(imrang)

            hwp_range = self.HWP_POSNS
            if do_extended_range and i in self.IMR_INDS_HWP_EXT:
                hwp_range = self.HWP_POSNS + self.EXT_HWP_POSNS
            # every other sequence flip the HWP order to minimize travel
            if i % 2 == 1:
                hwp_range = list(reversed(hwp_range))

            pbar.write(f"HWP angles: [{', '.join(map(str, hwp_range))}]")
            for hwpang in tqdm.tqdm(hwp_range, total=len(hwp_range), desc="HWP"):
                self.pause_cameras()
                self.move_hwp(hwpang)
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

        parity = False
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
            self.iterate_one_filter(parity=parity, **kwargs)
            # every other sequence flip the IMR angle order to minimize travel
            parity = not parity


@click.command("hwp_calib")
@click.option("-t", "--time", type=float, default=5, prompt="Time (s) per position")
@click.option("-f/-nf", "--flc/--no-flc", default=False, prompt="Use FLC")
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
def main(time, flc: bool = False, debug=False):
    manager = HWPOptimizer(debug=debug)
    manager.run(flc=flc, time_per_cube=time)


if __name__ == "__main__":
    main()
