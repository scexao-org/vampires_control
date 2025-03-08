import time
import logging

import click
import numpy as np
import tqdm.auto as tqdm
from numpy.polynomial import Polynomial
from pyMilk.interfacing.isio_shmlib import SHM
from swmain.network.pyroclient import connect
from typing import Literal
import matplotlib.pyplot as plt

# set up logging
formatter = logging.Formatter("%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("autofocus")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class CorAlign:
    # only get 30 fps over zmq, don't waste our time here
    DEFAULT_NUM_FRAMES = 10
    FACTOR = 0.1 # clc3
    # FACTOR = 100 # clc2
    def __init__(self, camera_num: Literal[1, 2]=1):
        self.camera = connect(f"VCAM{camera_num}")
        self.shm = SHM(f"vcam{camera_num}")
        self.fieldstop = connect("VAMPIRES_FIELDSTOP")

    def run(self, num_frames=DEFAULT_NUM_FRAMES, max_niter=100):
        niter = 0
        while niter <= max_niter:
            data_cube = self.shm.multi_recv_data(num_frames, output_as_cube=True).astype("f4")
            mean_frame = np.nanmedian(data_cube - 200, axis=0, overwrite_input=True)
            dx, dy = measure_quad_diffs(mean_frame)
            logger.info("Measured energy of dx=%.02g dy=%.02g", dx, dy)

            # to move left (-x) requires moving fieldstop stage +y
            # to move up (+y) requires moving fieldstop stage +x
            motion_x = dy * self.FACTOR
            motion_y = -dx * self.FACTOR
            logger.info("Offset applied: dx=%.4f mm dy=%.4f mm (r=%.4f mm)", motion_x, motion_y, np.hypot(motion_x, motion_y))
            self.fieldstop.move_relative("x", motion_x)
            self.fieldstop.move_relative("y", motion_y)
            _motion_criterion = 1e-5
            if np.hypot(dx, dy) < _motion_criterion:
                logger.info(f"Criteria reached: total motion < {_motion_criterion}")
                break
            niter += 1
            time.sleep(0.5)

def display_frame(frame, dx, dy):
    cy, cx = np.array(frame.shape) / 2 - 0.5
    plt.imshow(np.log10(frame), cmap="magma", origin="lower")
    plt.scatter([cx], [cy], marker="*", c="green", s=50, lw=1)
    plt.scatter([cx + dx*1e2], [cy + dy*1e2], marker="+", c="cyan", s=50, lw=1)
    plt.xlim((cx - 20, cx + 20))
    plt.ylim((cy - 20, cy + 20))
    plt.show(block=True)

def measure_quad_diffs(mean_frame, max_rad: float=256):
    ys, xs = np.indices(mean_frame.shape)
    cy, cx = np.array(mean_frame.shape) / 2 - 0.5

    ys_centered = ys - cy
    xs_centered = xs - cx
    radii = np.hypot(ys_centered, xs_centered)
    rad_mask = (radii <= max_rad) & (radii >= 5)

    # q2 | q1
    # -------
    # q3 | q4

    q1 = ((xs_centered >= 0) & (ys_centered >= 0)) & rad_mask
    q2 = ((xs_centered <= 0) & (ys_centered >= 0)) & rad_mask
    q3 = ((xs_centered <= 0) & (ys_centered <= 0)) & rad_mask
    q4 = ((xs_centered >= 0) & (ys_centered <= 0)) & rad_mask

    norm_image = mean_frame / np.nansum(mean_frame[rad_mask])

    counts_q1 = np.nansum(norm_image[q1])
    counts_q2 = np.nansum(norm_image[q2])
    counts_q3 = np.nansum(norm_image[q3])
    counts_q4 = np.nansum(norm_image[q4])
    logger.info("Quadrant counts %.02g %.02g %.02g %.02g", counts_q1, counts_q2, counts_q3, counts_q4)

    x_diff = (counts_q1 + counts_q4) - (counts_q2 + counts_q3)
    y_diff = (counts_q1 + counts_q2) - (counts_q3 + counts_q4)

    mask = (xs_centered >= 0) & (ys_centered >= 0) * rad_mask
    # display_frame(norm_image * mask, x_diff * 1e5, y_diff*1e5)
    return x_diff, y_diff


@click.command(
    "vampires_coralign",
    help="Optimize the focal plane mask position using quadrant energy differences",
)
@click.option(
    "-c",
    "--camera",
    default=1,
    type=int,
    help="Camera stream used for measuring focus metric (either 1 or 2)",
)
@click.option(
    "-n",
    "--num-frames",
    default=CorAlign.DEFAULT_NUM_FRAMES,
    type=int,
    help="Number of frames to coadd for each measurement",
    show_default=True,
)
def main(camera: int, num_frames: int):
    welcome = "Welcome to the VAMPIRES coronagraph alignment scripts"
    click.echo("=" * len(welcome))
    click.echo(welcome)
    click.echo("=" * len(welcome))


    # instantiate class
    cor_align = CorAlign(camera)
    cor_align.run(num_frames)

    click.echo("Coronagraph alignment finished")
    return None


if __name__ == "__main__":
    main()
