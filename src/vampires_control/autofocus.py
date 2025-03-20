import logging
import os

import click
import numpy as np
import pandas as pd
import tqdm.auto as tqdm
from numpy.polynomial import Polynomial
from pyMilk.interfacing.isio_shmlib import SHM
from swmain.network.pyroclient import connect
import time

from .strehl import measure_strehl_shm

# set up logging
formatter = logging.Formatter("%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("autofocus")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class Autofocuser:
    # only get 30 fps over zmq, don't waste our time here
    DEFAULT_NUM_FRAMES = 10
    DEFAULT_SLEEP = 0.1

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
        self.cameras = {1: connect("VCAM1"), 2: connect("VCAM2")}
        self.shms = {1: SHM("vcam1"), 2: SHM("vcam2")}
        self.focus_stage = connect("VAMPIRES_FOCUS")

    def autofocus_lens(self, shm, start_point, num_frames=10):
        focus_range = _focus_range(start_point)
        strehls = []
        pbar = tqdm.tqdm(focus_range, desc="Scanning lens", leave=False)
        for _i, position in enumerate(pbar):
            pbar.write(f"Moving lens focus to {position:4.02f} mm", end=" | ")
            self.focus_stage.move_absolute("lens", position)
            time.sleep(self.DEFAULT_SLEEP)
            cur_strehl = measure_metric(shm, num_frames)
            strehls.append(cur_strehl)
            strehl_val = cur_strehl["F720"] if len(cur_strehl) > 1 else list(cur_strehl.values())[0]
            pbar.write(f"Strehl ratio: {strehl_val*1e2:04.01f}%")

        strehl_table = pd.DataFrame(strehls)
        best_fit, best_value = fit_optimal_focus(focus_range, strehl_table)
        logger.info(f"Best Strehl - {best_value * 1e2:04.01f}% - focus= {best_fit:4.02f} mm")
        self.focus_stage.move_absolute("lens", best_fit)
        return best_fit

    def autofocus_camfocus(self, shm, start_point, num_frames=10):
        focus_range = _focus_range(start_point)
        strehls = []
        pbar = tqdm.tqdm(focus_range, desc="Scanning camfocus", leave=False)
        for _i, position in enumerate(pbar):
            pbar.write(f"Moving camera focus to {position:4.02f} mm", end=" | ")
            self.focus_stage.move_absolute("cam", position)
            time.sleep(self.DEFAULT_SLEEP)
            cur_strehl = measure_metric(shm, num_frames)
            strehls.append(cur_strehl)
            strehl_val = cur_strehl["F720"] if len(cur_strehl) > 1 else list(cur_strehl.values())[0]
            pbar.write(f"Strehl ratio: {strehl_val*1e2:04.01f}%")

        strehl_table = pd.DataFrame(strehls)
        best_fit, best_value = fit_optimal_focus(focus_range, strehl_table)
        logger.info(f"Best Strehl - {best_value * 1e2:04.01f}% - focus= {best_fit:4.02f} mm")
        self.focus_stage.move_absolute("cam", best_fit)
        return best_fit


def _focus_range(start_point: float):
    search_width = 1.5  # mm
    step_size = 0.05  # mm
    focus_range = np.arange(
        max(0, start_point - search_width / 2), min(23, start_point + search_width / 2), step_size
    )
    return focus_range


def measure_metric(shm: SHM, num_frames: int, **kwargs) -> dict[str, float]:
    """Get multiple frames, collapse, and measure focus metric"""
    strehls = measure_strehl_shm(shm.FNAME, nave=num_frames, **kwargs)
    if isinstance(strehls, dict):
        # optimize over F720 field
        return strehls
    # otherwise strehls is just a float
    return {shm.FNAME: strehls}


def fit_optimal_focus(focus, metrics: pd.DataFrame, plot: bool = True) -> tuple[float, float]:
    """Given sample points and values, fit maximum using parabola"""
    # fit quadratic to curve, make sure
    # to convert back to origina domain and range
    vertices = {}
    values = {}
    polynomials = {}
    for key in metrics.columns:
        poly = Polynomial.fit(focus, metrics[key].values, deg=2).convert()
        # vertex of polynomial
        polynomials[key] = poly
        vertex = -poly.coef[1] / (2 * poly.coef[2])
        vertices[key] = vertex
        values[key] = poly(vertex)
    logger.info(vertices)
    logger.info(values)
    weighted_ave_vertex = sum(
        val * vertex for val, vertex in zip(values.values(), vertices.values())
    )
    weighted_ave_vertex /= sum(values.values())
    weighted_ave_value = sum(val**2 for val in values.values())
    weighted_ave_value /= sum(values.values())

    if plot:
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots()
            test_focus = np.linspace(focus.min(), focus.max(), 1000)
            for i, key in enumerate(metrics.columns):
                _metrics = metrics[key].values
                color = f"C{i}"
                ax.scatter(focus, _metrics, label=key, c=color)
                fit_vals = polynomials[key](test_focus)
                ax.plot(test_focus, fit_vals, c=color, lw=1)
                ax.axvline(vertices[key], c=color, label=None)
            ax.axvline(weighted_ave_vertex, c="k", lw=3)
            ax.set(
                xlabel="Stage position (mm)",
                ylabel="Strehl ratio",
            )
            ax.legend()
            plt.show(block=True)
        except Exception as e:
            print(e)
            print("Could not plot")

    return weighted_ave_vertex, weighted_ave_value


@click.command(
    "vampires_autofocus",
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
    if os.environ.get("WHICHCOMP", "") != "5":
        msg = "WARNING: this script should be ran on scexao5"
        raise ValueError(msg)

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
            default=af.focus_stage.get_position("lens"),
            type=float,
        )
        af.focus_stage.move_absolute("lens", focus_posn)
        click.confirm("Adjust camera settings and proceed when ready", abort=True, default=True)
        result = af.autofocus_lens(shm, start_point=focus_posn, num_frames=num_frames)
    elif stage == "cam":
        camfocus_posn = click.prompt(
            "Please enter starting position for camera stage",
            default=af.focus_stage.get_position("cam"),
            type=float,
        )
        af.focus_stage.move_absolute("cam", camfocus_posn)
        click.confirm("Adjust camera settings and proceed when ready", abort=True, default=True)
        result = af.autofocus_camfocus(shm, start_point=camfocus_posn, num_frames=num_frames)
    click.echo("Autofocus finished")
    return result


if __name__ == "__main__":
    main()
