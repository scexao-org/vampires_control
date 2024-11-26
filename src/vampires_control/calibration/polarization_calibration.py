import logging
import os
import time
from pathlib import Path

import click
import numpy as np
import pandas as pd
import tqdm.auto as tqdm
from device_control.facility import WPU, ImageRotator
from scxconf.pyrokeys import VAMPIRES
from swmain.network.pyroclient import connect
from swmain.redis import get_values
from concurrent import futures

from vampires_control.acquisition.manager import VCAMLogManager

conf_dir = Path(os.getenv("CONF_DIR", f"{os.getenv('HOME')}/src/vampires_control/conf/"))

# set up logging
formatter = logging.Formatter("%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class PolCalManager:
    """
    PolCalManager
    """

    IMR_POSNS = (45, 57.5, 70, 82.5, 95, 107.5, 120, 132.5)
    HWP_POSNS = (0, 11.25, 22.5, 33.75, 45, 56.25, 67.5, 78.75)
    EXT_HWP_POSNS = (90, 101.25, 112.5, 123.75, 135, 146.25, 157.5, 168.75)
    IMR_INDS_HWP_EXT = (2, 5)
    STANDARD_FILTERS = ("Open", "625-50", "675-50", "725-50", "750-50", "775-50")
    NB_FILTERS = ("Halpha", "Ha-cont", "SII", "SII-cont")

    def __init__(self, mode: str = "standard", use_flc: bool = False, extend: bool = True, debug: bool=False):
        self.cameras = {1: connect("VCAM1"), 2: connect("VCAM2")}
        self.managers = {1: VCAMLogManager(1), 2: VCAMLogManager(2)}
        self.extend = extend
        self.use_flc = use_flc
        if self.use_flc:
            self.flc = connect(VAMPIRES.FLC)
        self.filt = connect(VAMPIRES.FILT)
        self.diff_filt = connect(VAMPIRES.DIFF)
        self.imr = ImageRotator.connect()
        self.wpu = WPU()
        self.mode = mode
        self.filters = self.ask_for_filters()
        self.debug = debug
        if self.debug:
            # filthy, disgusting
            logger.setLevel(logging.DEBUG)
            logger.handlers[0].setLevel(logging.DEBUG)
        self.conf_data = pd.read_csv(conf_dir / "data" / "conf_vampires_qwp_filter_data.csv")

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
            logger.debug("PREPARING WPU:POLARIZER")
            logger.debug("PREPARING WPU:HWP")
            if self.mode in ("MBI", "NB"):
                logger.debug("PREPARING VAMPIRES:FILTER")
            return

        # prepare vampires
        # if self.mode == "NB":
        #     # prep_sdi.callback(flc=self.flc, mbi=mbi)
        #     pass
        # else:
        #     # prep_pdi.callback(flc=self.flc, mbi=mbi)
        if self.mode in ("MBI", "NB"):
            self.filt.move_configuration("Open")
        # prepare wpu
        self.wpu.spp.move_in()  # move polarizer in
        self.wpu.shw.move_in()  # move HWP in

    def move_imr(self, angle):
        if self.debug:
            logger.debug(f"MOVING IMR TO {angle}")
            return

        # move image rotator to position
        self.imr.move_absolute(angle)
        while np.abs(self.imr.get_position() - angle) > 0.01:
            time.sleep(0.5)
        # let it settle so FITS keywords are sensible
        time.sleep(0.5)
        self.imr.get_position()

    def move_hwp(self, angle):
        if self.debug:
            logger.debug(f"MOVING HWP TO {angle}")
            return

        # move HWP to position
        self.wpu.hwp.move_absolute(angle)
        while np.abs(self.wpu.hwp.get_position() - angle) > 0.01:
            time.sleep(0.5)
        # let it settle so FITS keywords are sensible
        time.sleep(0.5)
        # update camera SHM keywords
        hwp_status = self.wpu.hwp.get_status()
        for cam in self.cameras.values():
            cam.set_keyword("RET-ANG1", round(hwp_status["pol_angle"], 2))
            cam.set_keyword("RET-POS1", round(hwp_status["position"], 2))

    def iterate_one_filter(self, parity=False):
        logger.info("Starting HWP + IMR loop")
        imr_range = self.IMR_POSNS
        if parity:
            imr_range = list(reversed(imr_range))

        pbar = tqdm.tqdm(imr_range, desc="IMR")
        for i, imrang in enumerate(pbar):
            self.move_imr(imrang)

            hwp_range = self.HWP_POSNS
            if self.extend and i in self.IMR_INDS_HWP_EXT:
                hwp_range = self.HWP_POSNS + self.EXT_HWP_POSNS
            # every other sequence flip the HWP order to minimize travel
            if i % 2 == 1:
                hwp_range = list(reversed(hwp_range))

            pbar.write(f"HWP angles: [{', '.join(map(str, hwp_range))}]")
            for hwpang in tqdm.tqdm(hwp_range, total=len(hwp_range), desc="HWP"):
                self.move_hwp(hwpang)
                self.acquire_cube()

    def acquire_cube(self):
        if self.debug:
            logger.debug("PLAY PRETEND MODE: take VAMPIRES cube")
            return
        def wrapper(mgr):
            mgr.start_acquisition()
            mgr.pause_acquisition(wait_for_cube=True)
            time.sleep(0.5)
        # execute function simultaneously using thread-pool, this way there's no 
        # delay between signals fired to the fps-ctrl
        with futures.ThreadPoolExecutor() as executor:
            fs = [executor.submit(wrapper, mgr) for mgr in self.managers.values()]
            for f in fs:
                f.result()

    def move_filters(self, filt):
        logger.info(f"Moving filter to {filt}")
        if self.debug:
            return
        if filt in self.STANDARD_FILTERS:
            self.filt.move_configuration(filt)
        elif filt in self.NB_FILTERS:
            if filt == "Halpha":
                self.diff_filt.move_configuration_idx(3)
            elif filt == "Ha-cont":
                self.diff_filt.move_configuration_idx(6)
            elif filt == "SII":
                self.diff_filt.move_configuration_idx(2)
            elif filt == "SII-cont":
                self.diff_filt.move_configuration_idx(5)

    def run(self, confirm=False, **kwargs):
        logger.info("Beginning HWP calibration")
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

    def wait_for_qwp_pos(self, filt):
        if self.debug:
            return
        if filt == "Ha-cont":
            filt = "Halpha"
        elif filt == "SII-cont":
            filt = "SII"
        indices = self.conf_data["filter"] == filt
        conf_row = self.conf_data.loc[indices]

        qwp1_pos = float(conf_row["qwp1"].iloc[0])
        qwp2_pos = float(conf_row["qwp2"].iloc[0])
        while True:
            last_qwp1, last_qwp2 = get_values(("U_QWP1", "U_QWP2")).values()
            if np.abs(last_qwp1 - qwp1_pos) < 0.1 and np.abs(last_qwp2 - qwp2_pos) < 0.1:
                break
            time.sleep(0.5)


@click.command("pol_calib")
@click.option(
    "-m",
    "--mode",
    default="standard",
    type=click.Choice(["standard", "MBI", "NB"], case_sensitive=False),
    prompt="Select calibraiton mode",
)
@click.option("-f/-nf", "--flc/--no-flc", default=False, prompt="Use FLC")
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
@click.option("-e/-ne", "--extend/--no-extend", default=True, help=f"For IMR angles {'°, '.join(str(PolCalManager.IMR_POSNS[idx]) for idx in PolCalManager.IMR_INDS_HWP_EXT)} extend HWP angles to 180°")
def main(mode: str, flc: bool, debug: bool, extend: bool):
    manager = PolCalManager(mode=mode, use_flc=flc, extend=extend, debug=debug)
    manager.run()


if __name__ == "__main__":
    main()
