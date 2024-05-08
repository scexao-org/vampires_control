import logging
import time

import click
import numpy as np
import tqdm.auto as tqdm
from scxconf.pyrokeys import VAMPIRES
from swmain.network.pyroclient import connect

from vampires_control.acquisition.manager import VCAMManager

# set up logging
formatter = logging.Formatter("%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("focus_sweep")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class FocusSweep:
    """
    FocusSweep
    """

    def __init__(self, debug=False, plot=False):
        self.camera = VCAMManager(1)
        self.focus = connect(VAMPIRES.FOCUS)
        self.debug = debug
        if self.debug:
            # filthy, disgusting
            logger.setLevel(logging.DEBUG)
            logger.handlers[0].setLevel(logging.DEBUG)

    def move_focus(self, position):
        self.focus.move_absolute(position)
        time.sleep(0.5)

    def run(self, time_per_cube=1, step=0.1, width=3.0):
        logger.info("Starting focus search")

        cur_posn = self.focus.get_position()
        posns = np.arange(cur_posn - width / 2, cur_posn + width / 2 + step / 2, step)
        for posn in tqdm.tqdm(posns):
            self.pause_cameras()
            self.move_focus(posn)
            self.resume_cameras()
            time.sleep(time_per_cube)

        return np.array(posns)

    def pause_cameras(self):
        if self.debug:
            logger.debug("PLAY PRETEND MODE: turn VAMPIRES off")
            return
        self.camera.pause_acquisition()

    def resume_cameras(self):
        if self.debug:
            logger.debug("PLAY PRETEND MODE: turn VAMPIRES on")
            return
        self.camera.start_acquisition()

    def cleanup(self):
        self.pause_cameras()


@click.command("focus_sweep")
@click.option("-t", "--time", type=float, default=1, prompt="Time (s) per position")
@click.option("-s", "--step", type=float, default=0.1, prompt="Step size in mm")
@click.option("-w", "--width", type=float, default=3.0, prompt="Range of defocus in mm")
# @click.option("-c", "--camera", type=int, default=1, prompt="Camera to log (1 or 2)")
@click.option("--debug/--no-debug", default=False, help="Dry run and debug information")
def main(time, step, width, debug=False):
    manager = FocusSweep(debug=debug)
    try:
        manager.run(time_per_cube=time, step=step, width=width)
    finally:
        manager.cleanup()


if __name__ == "__main__":
    main()
