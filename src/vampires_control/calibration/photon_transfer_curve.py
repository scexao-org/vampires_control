import logging
import multiprocessing as mp
from pathlib import Path
from typing import Union

import click
import numpy as np
import tqdm.auto as tqdm
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

    def run(self, num_frames=5):
        logger.info("Beginning PTC acquisition")
        # check if beamsplitter is inserted
        _, bs_config = self.beamsplitter.get_configuration()
        logger.debug(f"beamsplitter: {bs_config}")
        if not bs_config.upper() == "PBS":
            # if beamsplitter is not inserted, prompt
            logger.warn("Polarizing beamsplitter is not inserted")
            click.confirm(
                "Would you like to insert the beamsplitter?", abort=True, default=True
            )
            # insert beamsplitter
            logger.info(f"Inserting PBS beamsplitter")
            self.beamsplitter.move_configuration_name("PBS")

        result_dict = {}
        qwp_angles = None
        for config in tqdm.tqdm(self.filter.get_configurations(), desc="Filter"):
            if config["name"] == "625-50":
                continue
            self.filter.move_configuration_idx(config["idx"])
            logger.info(f"Moving filter to {config['name']}")
            # prepare cameras
            click.confirm(
                "Adjust camera settings and confirm when ready",
                default=True,
                abort=True,
            )
            qwp_angles, metrics = self.get_values_for_filter(num_frames=num_frames)
            result_dict[config["name"]] = metrics

        return qwp_angles, result_dict

    def acquire(self, nframes):
        with mp.Pool(2) as pool:
            res1 = pool.apply_async(get_cube, args=(1, nframes))
            res2 = pool.apply_async(get_cube, args=(2, nframes))
            pool.close()
            cubes = res1.get(), res2.get()

        return cubes

    def take_bias(self, nframes=1000):
        logger.info("Nudging diffwheel to take bias frames")
        self.diffwheel.move_absolute(30)

        for cam in self.cameras.values():
            cam.set_tint(0)

        logger.info("Acquiring...")
        cubes = self.acquire(nframes)
        logger.info("Finished taking bias frames")

        logger.info("Opening diffwheel")
        self.diffwheel.move_absolute(0)

        return cubes


def get_cube(shm, nframes):
    return SHMS[shm].multi_recv_data(nframes, outputFormat=2)


def main():
    pass


if __name__ == "__main__":
    main()
