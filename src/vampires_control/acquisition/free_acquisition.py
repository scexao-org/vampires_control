import time
from itertools import repeat

from rich.progress import track

from device_control.pyro_keys import VAMPIRES
from swmain.network.pyroclient import connect
from vampires_control.acquisition import logger
from vampires_control.acquisition.acquire import (start_acquisition,
                                                  stop_acquisition)


def acquire_cubes(num_frames, num_cubes=None, archive=False, use_trigger=False):
    if num_cubes is None:
        iterator = repeat(None)
    else:
        iterator = track(range(num_cubes), description="Acquiring cubes")
    if use_trigger:
        trigger = connect(VAMPIRES.TRIG)
    # trigger.disable()
    logger.info("Starting acquisition")
    if use_trigger:
        trigger.disable()
    start_acquisition(num_frames)
    if use_trigger:
        trigger.enable()
    logger.info("Acquisition started")
    update_interval = 100
    it = 0
    try:
        while True:
            if it % update_interval == 0:
                logger.info("...acquiring...")
            it += 1
            time.sleep(0.1)
    finally:
        logger.info("stopping acquisition")
        stop_acquisition()

    # for _ in iterator:
    #     ## acquire
    #     acq_time = num_frames * 5e-3 * 1e9  # seconds -> ns
    #     start_time = time.monotonic_ns()
    #     # TODO replace this with status call to logshim??
    #     while (time.monotonic_ns() - start_time) < acq_time:
    #         continue
    #     logger.info("Acquisition finished")
