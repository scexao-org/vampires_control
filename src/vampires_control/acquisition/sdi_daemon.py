import logging
import time

import click
import numpy as np
from rich.logging import RichHandler
from scxconf.pyrokeys import VAMPIRES
from swmain.network.pyroclient import connect

from vampires_control.acquisition.manager import VCAMManager

# set up logging
formatter = logging.Formatter("%(asctime)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("sdi_daemon")
rich_handler = RichHandler(level=logging.INFO, show_path=False)
logger.addHandler(rich_handler)
# logger.setLevel(logging.INFO)
# stream_handler = logging.StreamHandler()
# stream_handler.setLevel(logging.INFO)
# stream_handler.setFormatter(formatter)
# logger.addHandler(stream_handler)


class SDIStateMachine:
    def __init__(self, mode: str) -> None:
        if mode == "Halpha":
            self.indices = 3, 6
        elif mode == "SII":
            self.indices = 2, 4
        elif mode == "both":
            self.indices = 2, 4, 3, 6
        else:
            msg = f"SDI mode {mode} not recognized"
            raise ValueError(msg)
        self.mode = mode
        self.diffwheel = connect(VAMPIRES.DIFF)
        self.managers = {1: VCAMManager(1), 2: VCAMManager(2)}

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
        N = len(self.indices)
        self.current_idx = (self.current_idx + 1) % N
        logger.info(
            f"[State {self.current_idx + 1} / {N}] moving diff wheel to configuration: {self.indices[self.current_idx]}"
        )
        self.diffwheel.move_configuration_idx(self.indices[self.current_idx])

    def run(self, time_per_posn=30, max_loops=np.inf):
        if max_loops < 0:
            max_loops = np.inf
        i = 1
        N_per_loop = len(self.indices)
        self.prepare()
        while i <= N_per_loop * max_loops:
            for mgr in self.managers.values():
                mgr.start_acquisition()
            time.sleep(time_per_posn)
            for mgr in self.managers.values():
                mgr.pause_acquisition()
            logger.info(f"Finished taking iteration {i} / {N_per_loop * max_loops}")
            self.next()
            i += 1


@click.command("sdi_daemon")
@click.option(
    "-m", "--mode", type=click.Choice(["Halpha", "SII", "both"], case_sensitive=False), prompt=True
)
@click.option("-e", "--exptime", default=30, type=float, prompt="Time per SDI filter position")
@click.option(
    "-n",
    "--max-loops",
    default=-1,
    type=int,
    prompt="If set will stop after this many SDI loops (half the number of cubes)",
    required=False,
)
def main(mode, exptime=30, max_loops=None):
    sdi_mgr = SDIStateMachine(mode)
    sdi_mgr.run(time_per_posn=exptime, max_loops=max_loops)


if __name__ == "__main__":
    main()
