import logging

import click
import numpy as np
import tqdm.auto as tqdm
from numpy.polynomial import Polynomial
from pyMilk.interfacing.isio_shmlib import SHM
from swmain.network.pyroclient import connect

# set up logging
formatter = logging.Formatter("%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("autofocus")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class AutofocuserFieldstop:
    # only get 30 fps over zmq, don't waste our time here
    DEFAULT_NUM_FRAMES = 10

    """
        AutofocuserFieldstop

    The fieldstop can be auto-focused by using a flat field image of the corongraph masks and maximizing sharpness.
    """

    def __init__(self):
        self.cameras = {1: connect("VCAM1"), 2: connect("VCAM2")}
        self.shms = {1: SHM("vcam1"), 2: SHM("vcam2")}
        self.fieldstop_stage = connect("VAMPIRES_FIELDSTOP")

    def autofocus(self, shm, start_point, num_frames=10):
        focus_range = _focus_range(start_point)
        metrics = np.empty_like(focus_range)
        pbar = tqdm.tqdm(focus_range, desc="Scanning lens", leave=False)
        for i, position in enumerate(pbar):
            pbar.write(f"Moving fieldstop focus to {position:4.02f} mm", end=" | ")
            self.fieldstop_stage.move_absolute("f", position)
            metrics[i] = measure_metric(shm, num_frames)
            pbar.write(f"normalized variance: {metrics[i]:3.02e} (adu)")

        best_fit = fit_optimal_focus(focus_range, metrics)
        logger.info(f"Best-fit focus was {best_fit:4.02f} mm")
        self.fieldstop_stage.move_absolute("f", best_fit)
        return best_fit


def _focus_range(start_point: float):
    search_width = 1.5  # mm
    step_size = 0.05  # mm
    focus_range = np.arange(
        max(0, start_point - search_width / 2), min(13, start_point + search_width / 2), step_size
    )
    return focus_range


def measure_metric(shm: SHM, num_frames: int, **kwargs):
    """Get multiple frames, collapse, and measure focus metric"""
    cube = shm.multi_recv_data(num_frames, output_as_cube=True, **kwargs)
    frame = np.median(cube, axis=0, overwrite_input=True)
    return autofocus_metric(frame)


def autofocus_metric(frame):
    """Return the autofocus metric (to maximize) from a single frame"""
    # calculate normalized variance
    var = np.var(frame)
    mean = np.mean(frame)
    return var / mean


def fit_optimal_focus(focus, metrics) -> float:
    """Given sample points and values, fit maximum using parabola"""
    # fit quadratic to curve, make sure
    # to convert back to origina domain and range
    poly = Polynomial.fit(focus, metrics, deg=2).convert()
    # vertex of polynomial
    return -poly.coef[1] / (2 * poly.coef[2])


@click.command(
    "autofocus_fieldstop",
    help="Optimize the focus using either the objective lens stage or the VCAM1 mount stage",
)
@click.option(
    "-c",
    "--camera",
    type=int,
    prompt=True,
    help="Camera stream used for measuring focus metric (either 1 or 2)",
)
@click.option(
    "-n",
    "--num-frames",
    default=10,
    type=int,
    help="Number of frames to coadd for each measurement",
    show_default=True,
)
def main(camera: int, num_frames: int):
    welcome = "Welcome to the VAMPIRES autofocusing scripts"
    click.echo("=" * len(welcome))
    click.echo(welcome)
    click.echo("=" * len(welcome))

    click.secho(f"Optimizing fieldstop focus using VCAM{camera:.0f}", bold=True)

    # instantiate class
    af = AutofocuserFieldstop()
    # get SHM to fit
    shm = af.shms[camera]

    focus_posn = click.prompt(
        "Please enter starting position for lens stage",
        default=af.fieldstop_stage.get_position("f"),
        type=float,
    )
    af.fieldstop_stage.move_absolute("f", focus_posn)
    click.confirm("Adjust camera settings and proceed when ready", abort=True, default=True)
    result = af.autofocus(shm, start_point=focus_posn, num_frames=num_frames)
    click.echo("Autofocus finished")
    return result


if __name__ == "__main__":
    main()
