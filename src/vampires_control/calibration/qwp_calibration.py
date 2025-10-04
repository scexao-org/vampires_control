import logging
import time
from concurrent.futures import ThreadPoolExecutor

import click
import numpy as np
import tqdm.auto as tqdm
from device_control.facility import ImageRotator
from pyMilk.interfacing.isio_shmlib import SHM
from swmain.network.pyroclient import connect

from vampires_control.acquisition.manager import VCAMLogManager

# set up logging
formatter = logging.Formatter("%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("qwp_sweep")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class QWPSweeper:
    """
    QWPSweeper
    """

    ANGLES = np.arange(0, 180, 5)
    IMR_ANGLES = np.linspace(60, 120, 7)

    def __init__(self):
        self.cameras = {1: connect("VCAM1"), 2: connect("VCAM2")}
        self.shms = {1: SHM("vcam1"), 2: SHM("vcam2")}
        self.managers = {i: VCAMLogManager(i) for i in (1, 2)}
        self.vis_qwp = connect("VIS_QWP")
        self.imr = ImageRotator.connect()

    def run(self):
        logger.info("Beginning QWP calibration")

        # prepare cameras
        click.confirm("Adjust camera settings and confirm when ready", default=True, abort=True)

        imr_pbar = tqdm.tqdm(self.IMR_ANGLES, desc="IMR")
        parity_flip1 = False
        parity_flip2 = False
        for imr_ang in imr_pbar:
            self.move_imr(imr_ang)
            qwp1_angs = self.ANGLES[::-1] if parity_flip1 else self.ANGLES
            qwp1_pbar = tqdm.tqdm(qwp1_angs, desc="QWP1", leave=False)
            for qwp1 in qwp1_pbar:
                self.vis_qwp.move_absolute("1", qwp1)
                self.shms[1].update_keyword("U_QWP1", qwp1)
                self.shms[2].update_keyword("U_QWP1", qwp1)

                qwp2_angs = self.ANGLES[::-1] if parity_flip2 else self.ANGLES
                qwp2_pbar = tqdm.tqdm(qwp2_angs, desc="QWP2", leave=False)
                for qwp2 in qwp2_pbar:
                    imr_pbar.write(f"IMR: {imr_ang} QWP1: {qwp1} QWP2: {qwp2}")
                    self.vis_qwp.move_absolute("2", qwp2)
                    self.shms[1].update_keyword("U_QWP2", qwp2)
                    self.shms[2].update_keyword("U_QWP2", qwp2)
                    imr_pbar.write("Taking a cube")
                    self.take_one_cube()

                    parity_flip2 = not parity_flip2
            parity_flip1 = not parity_flip1

    def move_imr(self, angle):
        # move image rotator to position
        self.imr.move_absolute(angle)
        while np.abs(self.imr.get_position() - angle) > 0.01:
            time.sleep(0.5)
        # let it settle so FITS keywords are sensible
        time.sleep(0.5)
        self.imr.get_position()

    def take_one_cube(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            jobs = []
            for mgr in self.managers.values():
                job = executor.submit(mgr.acquire_cubes, 1)
                jobs.append(job)
            for job in jobs:
                job.result()


@click.command("qwp_sweep")
def main():
    sweeper = QWPSweeper()
    sweeper.run()


if __name__ == "__main__":
    main()
