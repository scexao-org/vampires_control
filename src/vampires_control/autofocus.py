import logging

import click
import numpy as np
import tqdm.auto as tqdm
from numpy.polynomial import Polynomial

from pyMilk.interfacing.isio_shmlib import SHM
from swmain.network.pyroclient import connect

# set up logging
formatter = logging.Formatter(
    "%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("autofocus")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class Autofocuser:
    # only get 30 fps over zmq, don't waste our time here
    DEFAULT_NUM_FRAMES = 10

    """
        Autofocuser

    VAMPIRES is focused in a specific way in order to manage the many different focii encountered. VAMPIRES has two cameras, one of which has a motorized focus stage (cam 1) and the other with a manual focus stage (cam 2). VAMPIRES also has a motorized stage for the focusing lens which affects both cameras' focii.

    There are three optics that can affect the focal point of VAMPIRES-
    - beamsplitter cubes
    - narrowband filters in the differential filter wheel
    - pupil imaging lens

    The focusing is done in the following order:
    1. beamsplitter in, focus camera 2 using lens ("standard")
    2. beamsplitter in, focus camera 1 using camfocus ("dual")
    3. beamsplitter in, narrowband in, focus camera 1 and 2 using lens ("sdi")
    4. beampslitter out, focus camera 1 using camfocus ("single")
    5. TODO beamsplitter out, pupil lens in, focus camera 1 using camfocus ("pupil")
    """

    def __init__(self):
        self.cameras = {
            1: connect("VCAM1"),
            2: connect("VCAM2"),
        }
        self.shms = {1: SHM("vcam1"), 2: SHM("vcam2")}
        self.lens_stage = connect("VAMPIRES_FOCUS")
        self.cam_stage = connect("VAMPIRES_CAMFCS")

    def autofocus_lens(self, shm, start_point, num_frames=10):
        focus_range = _focus_range(start_point)
        metrics = np.empty_like(focus_range)
        pbar = tqdm.tqdm(focus_range, desc="Scanning lens", leave=False)
        for i, position in enumerate(pbar):
            pbar.write(f"Moving lens focus to {position:4.02f} mm", end=" | ")
            self.lens_stage.move_absolute(position)
            metrics[i] = measure_metric(shm, num_frames)
            pbar.write(f"normalized variance: {metrics[i]:3.02e} (adu)")

        best_fit = fit_optimal_focus(focus_range, metrics)
        logger.info(f"Best-fit focus was {best_fit:4.02f} mm")
        self.lens_stage.move_absolute(best_fit)
        return best_fit

    def autofocus_camfocus(self, shm, start_point, num_frames=10):
        focus_range = _focus_range(start_point)
        metrics = np.empty_like(focus_range)
        pbar = tqdm.tqdm(focus_range, desc="Scanning camfocus", leave=False)
        for i, position in enumerate(pbar):
            pbar.write(f"Moving camera focus to {position:4.02f} mm", end=" | ")
            self.cam_stage.move_absolute(position)
            metrics[i] = measure_metric(shm, num_frames)
            pbar.write(f"normalized variance: {metrics[i]:3.02e} (adu)")

        best_fit = fit_optimal_focus(focus_range, metrics)
        logger.info(f"Best-fit focus was {best_fit:4.02f} mm")
        self.cam_stage.move_absolute(best_fit)
        return best_fit


def _focus_range(start_point: float):
    search_width = 1.5  # mm
    step_size = 0.05  # mm
    focus_range = np.arange(
        max(0, start_point - search_width / 2),
        min(23, start_point + search_width / 2),
        step_size,
    )
    return focus_range


def measure_metric(shm: SHM, num_frames: int, **kwargs):
    """Get multiple frames, collapse, and measure focus metric"""
    cube = shm.multi_recv_data(num_frames, outputFormat=2, **kwargs)
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
    "autofocus",
    help="Optimize the focus using either the objective lens stage or the VCAM1 mount stage",
)
@click.argument("stage", type=click.Choice(["lens", "cam"], case_sensitive=False))
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
def main(stage: str, camera: int, num_frames: int):
    welcome = "Welcome to the VAMPIRES autofocusing scripts"
    click.echo("=" * len(welcome))
    click.echo(welcome)
    click.echo("=" * len(welcome))

    click.secho(f"Optimizing {stage.upper()} stage using VCAM{camera:.0f}", bold=True)

    # instantiate class
    af = Autofocuser()
    # get SHM to fit
    shm = af.shms[camera]

    if stage == "lens":
        focus_posn = click.prompt(
            "Please enter starting position for lens stage",
            default=af.lens_stage.get_position(),
            type=float,
        )
        af.lens_stage.move_absolute(focus_posn)
        click.confirm(
            "Adjust camera settings and proceed when ready", abort=True, default=True
        )
        result = af.autofocus_lens(shm, start_point=focus_posn, num_frames=num_frames)
    elif stage == "cam":
        camfocus_posn = click.prompt(
            "Please enter starting position for camera stage",
            default=af.cam_stage.get_position(),
            type=float,
        )
        af.cam_stage.move_absolute(camfocus_posn)
        click.confirm(
            "Adjust camera settings and proceed when ready", abort=True, default=True
        )
        result = af.autofocus_camfocus(
            shm, start_point=camfocus_posn, num_frames=num_frames
        )
    click.echo("Autofocus finished")
    return result


if __name__ == "__main__":
    autofocus()
