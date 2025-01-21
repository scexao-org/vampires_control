import logging
import time

import click
import numpy as np
from scxconf.pyrokeys import VAMPIRES
from swmain.network.pyroclient import connect
from concurrent import futures

from vampires_control.acquisition.manager import VCAMLogManager

# set up logging
formatter = logging.Formatter("%(asctime)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("sdi_daemon")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


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
        self.managers = {1: VCAMLogManager(1), 2: VCAMLogManager(2)}

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
        # settle time for good luck and good headers
        settling_time = 1 # s 
        time.sleep(settling_time)
        self.diffwheel.update_keys()

    def run(self, num_cubes: int=1, max_loops=np.inf):
        if max_loops < 0:
            max_loops = np.inf
        i = 1
        N_per_loop = len(self.indices)
        with futures.ThreadPoolExecutor() as pool:
            while i <= N_per_loop * max_loops:
                # start both cameras simultaneously
                tasks = []
                for mgr in self.managers.values():
                    tasks.append(pool.submit(mgr.acquire_cubes, num_cubes))
                # wait for all tasks to complete
                [task.result() for task in tasks]
                logger.info(f"Finished taking iteration {i} / {N_per_loop * max_loops}")
                self.next()
                i += 1


    def cleanup(self, wait=True):
        with futures.ThreadPoolExecutor() as pool:
            tasks = []
            for mgr in self.managers.values():
                tasks.append(pool.submit(mgr.pause_acquisition, wait_for_cube=wait))
            [task.result() for task in tasks]
            

@click.command("sdi_daemon")
@click.option(
    "-m", "--mode", default="Halpha", type=click.Choice(["Halpha", "SII", "both"], case_sensitive=False), prompt=True
)
@click.option(
    "-n",
    "--num-cubes",
    default=1,
    type=int,
    prompt="Number of cubes per SDI state"
)
@click.option(
    "-l",
    "--max-loops",
    default=-1,
    type=int,
    prompt="If set will stop after this many SDI loops (half the number of cubes)",
    required=False,
)
def main(mode, num_cubes=1, max_loops=None):
    sdi_mgr = SDIStateMachine(mode)
    try:
        sdi_mgr.prepare()
        sdi_mgr.run(num_cubes=num_cubes, max_loops=max_loops)
    except KeyboardInterrupt:
        logger.debug("Keyboard interrupt !")
        click.secho(
            "\nInterrupt received, this will be the last iteration (CTRL+C again to force)",
            fg="white",
            bg="blue",
        )
        try:
            sdi_mgr.cleanup(wait=True)
        except KeyboardInterrupt:
            logger.debug("Keyboard interrupt - forcing shutdown!")

            sdi_mgr.cleanup(wait=False)


if __name__ == "__main__":
    main()
