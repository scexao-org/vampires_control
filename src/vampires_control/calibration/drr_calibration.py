import logging
import subprocess
import time

import click
import numpy as np
import tqdm.auto as tqdm
from scxconf.pyrokeys import VAMPIRES

from device_control.facility import WPU, ImageRotator
from swmain.network.pyroclient import connect

from ..acquisition.manager import VCAMManager
from ..configurations import prep_pdi

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


class DRROptimizer:
    """
    DRROptimizer
    """

    HWP_POSNS = np.linspace(0, 180, 24)
    QWP_POSNS = 5 * HWP_POSNS
    FILTERS = [
        "Open",
        "625-50",
        "675-50",
        "725-50",
        "750-50",
        "775-50",
    ]

    def __init__(self, debug=False):
        self.cameras = {
            1: connect("VCAM1"),
            2: connect("VCAM2"),
        }
        self.managers = {
            1: VCAMManager(1),
            2: VCAMManager(2),
        }
        self.flc = connect(VAMPIRES.FLC)
        self.filt = connect(VAMPIRES.FILT)
        self.qwps = {1: connect(VAMPIRES.QWP1), 2: connect(VAMPIRES.QWP2)}
        self.imr = ImageRotator.connect()
        self.wpu = WPU()
        self.debug = debug
        if self.debug:
            # filthy, disgusting
            logger.setLevel(logging.DEBUG)
            logger.handlers[0].setLevel(logging.DEBUG)

    def prepare(self, flc: bool = False, imr=90):
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
            self.imr.move_absolute(imr)  # IMR to 90

    def move_qwps(self, angle):
        if self.debug:
            logger.debug(f"MOVING QWPs TO {angle}")
            return

        p1 = subprocess.Popen(("vampires_qwp", "1", "goto", str(angle)))
        p2 = subprocess.Popen(("vampires_qwp", "2", "goto", str(angle)))
        p1.wait()
        p2.wait()

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

    def iterate_one_filter(self, time_per_cube=1, parity=False):
        logger.info("Starting HWP + QWP loop")
        hwp_range = self.HWP_POSNS
        if parity:
            hwp_range = list(reversed(hwp_range))

        pbar = tqdm.tqdm(hwp_range, desc="HWP")
        for i, hwpang in enumerate(pbar):
            self.pause_cameras()
            self.move_hwp(hwpang)

            qwp_range = self.QWP_POSNS
            # every other sequence flip the HWP order to minimize travel
            if i % 2 == 1:
                qwp_range = list(reversed(qwp_range))

            for qwpang in tqdm.tqdm(qwp_range, total=len(qwp_range), desc="QWPs"):
                self.pause_cameras()
                self.move_qwps(qwpang)
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
            mgr.start_acqusition()

    def run(self, flc: bool = False, confirm=True, **kwargs):
        logger.info("Beginning DRR calibration")
        self.prepare(flc=flc)

        parity = False
        for config in tqdm.tqdm(self.FILTERS, desc="Filter"):
            logger.info(f"Moving filter to {config}")
            if not self.debug:
                self.filt.move_configuration(config)
            # prepare cameras
            if confirm and not click.confirm(
                "Adjust camera settings and confirm when ready, no to skip to next filter",
                default=True,
            ):
                continue
            self.iterate_one_filter(parity=parity, **kwargs)
            # every other sequence flip the IMR angle order to minimize travel
            parity = not parity


@click.command("drr_calib")
@click.option("-t", "--time", type=float, default=5, prompt="Time (s) per position")
@click.option("-f/-nf", "--flc/--no-flc", default=False, prompt="Use FLC")
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
def main(time, flc: bool = False, debug=False):
    manager = DRROptimizer(debug=debug)
    manager.run(flc=flc, time_per_cube=time)


if __name__ == "__main__":
    main()
