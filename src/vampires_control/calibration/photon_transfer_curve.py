import logging
import multiprocessing as mp
from pathlib import Path
from typing import Union

import click
import numpy as np
import tqdm.auto as tqdm
from scxconf.pyrokeys import VCAM1, VCAM2
from swmain.network.pyroclient import connect

from vampires_control.acquisition.manager import VCAMLogManager

# set up logging
formatter = logging.Formatter("%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("PTC")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)



MANAGERS = {c: VCAMLogManager(c) for c in (1, 2)}
exptimes_fast = (0.05)

class PTCAcquirer:
    """
    PTCAcquirer
    """
    TEXP_FAST = np.geomspace(7.2e-6, 0.05, 50) # works well for 15V 3A
    TEXP_SLOW = np.geomspace(95e-3, 0.5, 5)

    def __init__(self, base_dir: Union[str, Path, None] = None):
        self.cameras = {1: connect(VCAM1), 2: connect(VCAM2)}
        self.base_dir = Path.cwd() if base_dir is None else Path(base_dir)

    def get_exposure_times(self):
        # determine if we're in fast or slow readout mode
        is_fast = [cam.get_readout_mode() == "FAST" for cam in self.cameras.values()]
        if all(is_fast):
            texp = self.TEXP_FAST
        elif not any(is_fast):
            texp = self.TEXP_SLOW
        else:
            msg = "Both cameras have different readout modes, please make them equal"
            raise RuntimeError(msg)
        
        ndits = [mgr.fps.get_param("cubesize") for mgr in MANAGERS.values()]
        assert ndits[0] == ndits[1], "There are different cube sizes for each camera"
        total_tint = np.sum(texp * ndits[0])
        click.echo(f"Total integration time: {total_tint:.01f} s")

        return texp

    def run(self):
        ## prepare for PTC
        ## take PTC data
        logger.info("Beginning PTC acquisition")
        exptimes = self.get_exposure_times()
        click.confirm("Confirm if ready to proceed", abort=True, default=True)

        pbar = tqdm.tqdm(exptimes)
        for exptime in pbar:
            for cam in self.cameras.values():
                tint = cam.set_tint(exptime)
            pbar.desc = f"t={tint:4.02e} s"
            self.acquire()

        logger.info("Finished taking PTC data")

    def acquire(self):
        with mp.Pool(2) as pool:
            j1 = pool.apply_async(get_cube, (1,))#MANAGERS[1].acquire_cubes, args=(1,))
            j2 = pool.apply_async(get_cube, args=(2,))#MANAGERS[2].acquire_cubes, args=(1,))
            pool.close()
            j1.get()
            j2.get()

    def cleanup(self):
        # when exiting, make sure camera loggers have stopped
        for mgr in MANAGERS.values():
            mgr.pause_acquisition(wait_for_cube=False)


@click.command("vampires_ptc")
def main():
    ptc = PTCAcquirer()
    try:
        ptc.run()
    except Exception as e:
        ptc.cleanup()
        raise e


def get_cube(index):
    return MANAGERS[index].acquire_cubes(1)

if __name__ == "__main__":
    main()
