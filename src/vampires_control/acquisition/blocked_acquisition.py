import logging
import time

import click
import tqdm.auto as tqdm
import zmq
from rich.logging import RichHandler
from rich.progress import Progress

from swmain.network.pyroclient import connect
from vampires_control.acquisition import logger
from vampires_control.acquisition.acquire import (pause_acquisition,
                                                  resume_acquisition,
                                                  start_acquisition,
                                                  stop_acquisition)
from vampires_control.cameras import connect_cameras
from vampires_control.daemons import PDI_DAEMON_PORT

# set up logging
formatter = logging.Formatter(
    "%(asctime)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("block_acq")
rich_handler = RichHandler(level=logging.INFO, show_path=False)
logger.addHandler(rich_handler)
# logger.setLevel(logging.INFO)
# stream_handler = logging.StreamHandler()
# stream_handler.setLevel(logging.INFO)
# stream_handler.setFormatter(formatter)
# logger.addHandler(stream_handler)


def get_pdi_socket(ctx):
    pdi_socket = ctx.socket(zmq.REQ)
    pdi_socket.connect(PDI_DAEMON_PORT)
    return pdi_socket


def trigger_acquisition(num_frames: int, num_cubes: int = 1, progress=None):
    logger.info("Starting acquisition")
    acq_time = num_frames * 5e-3 * 1e9  # seconds -> ns
    for _ in tqdm.trange(num_cubes, leave=False):
        start_time = time.monotonic_ns()
        # TODO replace this with status call to logshim??
        while (time.monotonic_ns() - start_time) < acq_time:
            continue
    logger.info("Acquisition finished")


class SDIStateMachine:
    def __init__(self, mode: str) -> None:
        if mode == "Halpha":
            self.indices = 4, 8
        elif mode == "SII":
            self.indices = 3, 6
        else:
            raise ValueError(f"SDI mode {mode} not recognized")
        self.mode = mode
        self.diffwheel = connect("VAMPIRES_DIFFWHEEL")

    def prepare(self, confirm=True):
        if confirm:
            click.confirm(
                f"Preparing for {self.mode} SDI.\nConfirm when ready to move diff wheel.",
                default=True,
                abort=True,
            )
        logger.info(f"Moving diff wheel into first {self.mode} position")
        self.diffwheel.move_configuration_idx(self.indices[0])
        self.current_idx = 0

    def next(self):
        self.current_idx = (self.current_idx + 1) % 2
        logger.info(
            f"[State {self.current_idx + 1} / 2] moving diff wheel to configuration: {self.indices[self.current_idx]}"
        )
        self.diffwheel.move_configuration_idx(self.indices[self.current_idx])


def blocked_acquire_cubes(
    num_frames,
    num_cubes=None,
    pdi=False,
    sdi_mode=None,
    pdi_num_per_hwp=1,
    sdi_num_per=1,
    archive=False,
):
    zmq.Context()
    if pdi:
        if num_cubes is not None and num_cubes % 4 != 0:
            raise ValueError(
                "PDI Sequences must be multiples of 4 to allow for HWP rotation."
            )
        # pdi_socket = get_pdi_socket(ctx)
    if sdi_mode is not None:
        if num_cubes is not None and num_cubes % 2 != 0:
            raise ValueError(
                "SDI Sequences must be multiples of 2 to allow for differential wheel switching."
            )
        sdi_state = SDIStateMachine(sdi_mode)
        sdi_state.prepare()
        # Now let's pause and allow for adjusting exposure times
        click.confirm(
            "Adjust camera settings. Confirm when ready.", default=True, abort=True
        )

    with Progress(expand=True) as progress:
        if num_cubes is None:
            iter = progress.add_task("Acquiring cubes", total=None)
        else:
            iter = progress.add_task("Acquiring cubes", total=num_cubes)
        start_acquisition()
        while not progress.finished:
            if sdi_mode is not None:
                ## acquire
                resume_acquisition()  # (num_frames=num_frames, num_cubes=sdi_num_per)

                ## move diffwheel
                sdi_state.next()
            progress.update(iter, advance=1)
