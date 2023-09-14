import logging
import multiprocessing as mp
from pathlib import Path
from typing import Union

import click
import numpy as np
import tqdm.auto as tqdm
from astropy.io import fits
from scxconf.pyrokeys import VAMPIRES, VCAM1, VCAM2

import vampires_control.acquisition.acquire as acq
from pyMilk.interfacing.isio_shmlib import SHM
from swmain.network.pyroclient import connect

# set up logging
formatter = logging.Formatter(
    "%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("PTC")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

SHMS = {1: SHM("vcam1"), 2: SHM("vcam2")}


class PTCAcquirer:
    """
    PTCAcquirer
    """

    def __init__(self, base_dir: Union[str, Path] = Path.cwd()):
        self.cameras = {
            1: connect(VCAM1),
            2: connect(VCAM2),
        }
        self.diffwheel = connect(VAMPIRES.DIFF)
        self.base_dir = Path(base_dir)

    def acquire(self, nframes):
        with mp.Pool(2) as pool:
            res1 = pool.apply_async(get_cube, args=(1, nframes))
            res2 = pool.apply_async(get_cube, args=(2, nframes))
            pool.close()
            cubes = res1.get(), res2.get()

        return cubes

    def take_bias(self, nframes=1000):
        logger.info("Nudging diffwheel to take bias frames")
        self.diffwheel.move_absolute(31)

        for cam in self.cameras.values():
            cam.set_tint(0)

        logger.info("Acquiring...")
        cubes = self.acquire(nframes)
        logger.info("Finished taking bias frames")

        logger.info("Opening diffwheel")
        self.diffwheel.move_absolute(0)

        return cubes

    def take_data(self, exptimes, nframes=30, **kwargs):
        logger.info("Beginning PTC acquisition")

        total_time = np.sum(exptimes * nframes)
        click.echo(
            f"{nframes} frames for {len(exptimes)} acquisitions will take {np.floor_divide(total_time, 60):02.0f}:{np.remainder(total_time, 60):02.0f}"
        )
        click.confirm("Confirm if ready to proceed", abort=True, default=True)

        actual_exptimes = []
        cubes = []
        pbar = tqdm.tqdm(exptimes)
        for exptime in pbar:
            pbar.desc = f"t={exptime:4.02e} s"
            for cam in self.cameras.values():
                tint = cam.set_tint(exptime)
            actual_exptimes.append(tint)
            cubes.append(np.array(self.acquire(nframes=nframes)))

        logger.info("Finished taking PTC data")
        return np.array(actual_exptimes), np.array(cubes)

    def run(self, name, exptimes, nframes=30, nbias=1000, **kwargs):
        ## take bias frames
        bias_cubes = np.array(self.take_bias(nframes=nbias))
        bias_path = self.base_dir / f"{name}_bias.fits"
        fits.writeto(bias_path, bias_cubes, overwrite=True)
        ## prepare for PTC
        click.confirm("Confirm when ready to proceed", abort=True, default=True)
        ## take PTC data
        exptimes, cubes = self.take_data(exptimes=exptimes, nframes=nframes)
        ## save to disk
        cube_path = self.base_dir / f"{name}_data.fits"
        fits.writeto(cube_path, cubes, overwrite=True)
        logger.info(f"Saved data to {cube_path}")
        texp_path = self.base_dir / f"{name}_texp.fits"
        fits.writeto(texp_path, exptimes, overwrite=True)
        logger.info(f"Saved exposure times to {texp_path}")
        return exptimes, cubes


def get_cube(shm, nframes):
    return SHMS[shm].multi_recv_data(nframes, outputFormat=2, timeout=6)


def main():
    pass


if __name__ == "__main__":
    main()
