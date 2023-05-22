from itertools import repeat
from rich.progress import track
from vampires_control.acquisition import logger
import time


def acquire_cubes(num_frames, num_cubes=None):
    if num_cubes is None:
        iterator = repeat()
    else:
        iterator = track(range(num_cubes), description="Acquiring cubes")
    logger.info("Starting acquisition")
    for _ in iterator:
        ## acquire
        acq_time = num_frames * 5e-3 * 1e9  # seconds -> ns
        start_time = time.monotonic_ns()
        # TODO replace this with status call to logshim??
        while (time.monotonic_ns() - start_time) < acq_time:
            continue
        logger.info("Acquisition finished")
