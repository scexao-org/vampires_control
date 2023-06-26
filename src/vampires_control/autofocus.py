import logging

import click
import numpy as np
import tqdm.auto as tqdm

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
    3. beampslitter out, focus camera 1 using camfocus ("single")
    4. beamsplitter in, narrowband in, focus camera 1 and 2 using lens ("sdi")
    5. beamsplitter out, pupil lens in, focus camera 1 using camfocus ("pupil")
    """

    def __init__(self):
        self.cameras = {
            1: connect("VCAM1"),
            2: connect("VCAM2"),
        }
        self.shms = {1: SHM("vcam1"), 2: SHM("vcam2")}
        self.beamsplitter = connect("VAMPIRES_BS")
        self.diff_wheel = connect("VAMPIRES_DIFF")
        self.focus_stage = connect("VAMPIRES_FOCUS")
        self.camfocus_stage = connect("VAMPIRES_CAMFCS")

    def autofocus_dualcam(self):
        logger.info("Beginning dual-cam autofocus")
        # check if beamsplitter is inserted
        _, bs_config = self.beamsplitter.get_configuration()
        logger.debug(f"beamsplitter: {bs_config}")
        if not bs_config.upper() in ("PBS", "NPBS"):
            # if beamsplitter is not inserted, prompt
            logger.warn("Beamsplitter is not inserted")
            bs = click.prompt(
                "Would you like to insert a beamsplitter?",
                type=click.Choice(["PBS", "NPBS"], case_sensitive=False),
                default="PBS",
            )
            # insert beamsplitter
            logger.info(f"Inserting {bs} beamsplitter")
            self.beamsplitter.move_configuration_name(bs)

        # prepare cameras
        click.confirm(
            "Adjust camera settings and confirm when ready", default=True, abort=True
        )

        # focus the lens
        self.autofocus_stage_one()
        # focus the camera focus
        self.autofocus_stage_two()

        # done!
        logger.info("Finished dual-cam autofocus")

    def autofocus_stage_one(self, step_size=0.05, num_frames=100):
        logger.info("Focusing camera 2 with lens")

        search_width = 1.5
        start_point = self.focus_stage.get_configurations()[0]["value"]
        focus_range = np.arange(
            start_point - search_width / 2, start_point + search_width / 2, step_size
        )

        metrics = np.empty_like(focus_range)
        for i, position in enumerate(
            tqdm.tqdm(focus_range, desc="Scanning focus", leave=False)
        ):
            logger.info(f"Moving focus lens to {position:4.02f} mm")
            self.focus_stage.move_absolute(position)
            cube = self.shms[2].multi_recv_data(num_frames, outputFormat=2)
            frame = np.median(cube, axis=0, overwrite_input=True)
            metrics[i] = autofocus_metric(frame)

        best_fit = get_focus_from_metric(focus_range, metrics)
        logger.info(f"Best-fit focus was {best_fit:4.02f} mm")
        self.focus_stage.move_absolute(best_fit)
        save = click.confirm(
            'Would you like to save this to the "standard" configuration?', default=True
        )
        if save:
            self.focus_stage.save_configuration(index=1, position=best_fit)
        self.focus_stage.move_configuration_name("standard")
        logger.info("Finished focusing camera 2")

    def autofocus_stage_two(self, step_size=0.05, num_frames=100):
        logger.info("Focusing camera 1 with camfocus stage")

        search_width = 1.5
        start_point = self.camfocus_stage.get_configurations()[0]["value"]
        focus_range = np.arange(
            start_point - search_width / 2, start_point + search_width / 2, step_size
        )

        metrics = np.empty_like(focus_range)
        for i, position in enumerate(
            tqdm.tqdm(focus_range, desc="Scanning focus", leave=False)
        ):
            logger.info(f"Moving camfocus stage to {position:4.02f} mm")
            self.camfocus_stage.move_absolute(position)
            cube = self.shms[1].multi_recv_data(num_frames, outputFormat=2)
            frame = np.median(cube, axis=0, overwrite_input=True)
            metrics[i] = autofocus_metric(frame)

        best_fit = get_focus_from_metric(focus_range, metrics)
        logger.info(f"Best-fit focus was {best_fit:4.02f} mm")
        self.camfocus_stage.move_absolute(best_fit)
        save = click.confirm(
            'Would you like to save this to the "dual" configuration?', default=True
        )
        if save:
            self.camfocus_stage.save_configuration(index=1, position=best_fit)
        self.camfocus_stage.move_configuration_name("dual")
        logger.info("Finished focusing camera 1")


def get_focus_from_metric(focus, metrics):
    # fit quadratic to curve
    poly = np.polynomial.Polynomial.fit(focus, metrics, deg=2)
    # vertex is at -b / 2a
    coefs = poly.convert().coef
    return -coefs[1] / (2 * coefs[2])


def autofocus_metric(frame):
    # calculate normalized variance
    var = np.var(frame)
    mean = np.mean(frame)
    return var / mean


@click.command("autofocus")
@click.argument("mode", type=click.Choice(["dual", "single"], case_sensitive=False))
@click.option("-n", "--num-frames", type=int, default=100, show_default=True)
def autofocus(mode: str, num_frames: int = 100):
    af = Autofocuser()
    if mode == "dual":
        af.autofocus_dualcam()
    elif mode == "single":
        click.echo("Not ready yet")


if __name__ == "__main__":
    autofocus()
