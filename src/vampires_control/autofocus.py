import logging

import click
import numpy as np
import tqdm.auto as tqdm
from numpy.polynomial import Polynomial
from tqdm.contrib.logging import logging_redirect_tqdm

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
        self.beamsplitter = connect("VAMPIRES_BS")
        self.diff_wheel = connect("VAMPIRES_DIFF")
        self.focus_stage = connect("VAMPIRES_FOCUS")
        self.camfocus_stage = connect("VAMPIRES_CAMFCS")

    def autofocus_dualcam(self, conf="standard"):
        logger.info(f"Beginning dual-cam autofocus ({conf})")
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
        num_frames = click.prompt(
            "Adjust camera settings and specify num frames per position when ready",
            default=self.DEFAULT_NUM_FRAMES,
            type=int,
        )

        ## 1. focus the lens to set standard focus
        config = None
        configs = self.focus_stage.get_configurations()
        for cfg in configs:
            if cfg["name"].lower() == conf.lower():
                config = cfg
        if config is None:
            raise ValueError(f"Could not find configuration '{conf}'")
        logger.info("Focusing camera 2 with the focusing lens")
        self.autofocus_lens(
            shm=self.shms[2],
            start_point=config["value"],
            num_frames=num_frames,
            config=config,
        )
        ## 2. focus the camera focus
        config = self.camfocus_stage.get_configurations()[0]
        logger.info("Focusing camera 1 with the camera focus stage")
        self.autofocus_camfocus(
            shm=self.shms[1],
            start_point=config["value"],
            num_frames=num_frames,
            config=config,
        )
        ## Done!
        logger.info("Finished dual-cam autofocus")

    def autofocus_sdi(self):
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

        # insert diff filter
        _, diff_config = self.diff_wheel.get_configuration()
        logger.debug(f"diff filter: {diff_config}")
        if "HA" not in diff_config.upper() or "SII" not in diff_config.upper():
            # if filter is not inserted, prompt
            logger.warn("Differential filter is not inserted")
            diff_filt = click.prompt(
                "Would you like to insert a filter?",
                type=click.Choice(["Halpha", "SII"], case_sensitive=False),
                default="SII",
            )
            # insert diff filter
            logger.info(f"Inserting {diff_filt} filter pair")
            if diff_filt == "Halpha":
                self.diff_wheel.move_configuration_name("Ha-cont / Halpha")
            elif diff_filt == "SII":
                self.diff_wheel.move_configuration_name("SII-cont / SII")
        # check if focus is at standard
        _, camfcs_config = self.camfocus_stage.get_configuration()
        logger.debug(f"focus: {camfcs_config}")
        if camfcs_config.upper() != "DUAL":
            # if focus is not at dual, prompt
            logger.warn("Not at dual focus")
            move_focus = click.prompt(
                "Would you like to move the camera focus?", default=True
            )
            if move_focus:
                # remove beamsplitter
                logger.info(f"Moving camfocus")
                self.camfocus_stage.move_configuration_idx(1)

        # prepare cameras
        num_frames = click.prompt(
            "Adjust camera settings and specify num frames per position when ready",
            default=self.DEFAULT_NUM_FRAMES,
            type=int,
        )

        ## 1. focus the lens to set sdi focus
        config = self.focus_stage.get_configurations()[1]
        logger.info("Focusing both cameras with the focusing lens")
        self.autofocus_lens(
            shm=(self.shms[1], self.shms[2]),
            start_point=config["value"],
            num_frames=num_frames,
            config=config,
        )
        ## Done!
        logger.info("Finished SDI autofocus")

    def autofocus_singlecam(self):
        logger.info("Beginning single-cam autofocus")
        # check if beamsplitter is inserted
        _, bs_config = self.beamsplitter.get_configuration()
        logger.debug(f"beamsplitter: {bs_config}")
        if bs_config.upper() != "OPEN":
            # if beamsplitter is not inserted, prompt
            logger.warn("Beamsplitter is inserted")
            remove_bs = click.prompt(
                "Would you like to remove the beamsplitter?", default=True
            )
            if remove_bs:
                # remove beamsplitter
                logger.info(f"Removing beamsplitter")
                self.beamsplitter.move_configuration_idx(3)
        # check if focus is at standard
        _, fcs_config = self.focus_stage.get_configuration()
        logger.debug(f"focus: {fcs_config}")
        if fcs_config.upper() != "STANDARD":
            # if focus is not at standard, prompt
            logger.warn("Not at standard focus")
            move_focus = click.prompt("Would you like to move the focus?", default=True)
            if move_focus:
                # remove beamsplitter
                logger.info(f"Moving focus")
                self.focus_stage.move_configuration_idx(1)

        # prepare cameras
        num_frames = click.prompt(
            "Adjust camera settings and specify num frames per position when ready",
            default=self.DEFAULT_NUM_FRAMES,
            type=int,
        )

        ## 1. focus the lens to set single focus
        config = self.camfocus_stage.get_configurations()[1]
        logger.info("Focusing both cameras with the focusing lens")
        self.autofocus_camfocus(
            shm=self.shms[1],
            start_point=config["value"],
            num_frames=num_frames,
            config=config,
        )
        ## Done!
        logger.info("Finished single-cam autofocus")

    def autofocus_lens(
        self, shm, start_point, step_size=0.05, num_frames=10, config=None
    ):
        search_width = 1.5
        focus_range = np.arange(
            max(0, start_point - search_width / 2),
            min(23, start_point + search_width / 2),
            step_size,
        )
        metrics = np.empty_like(focus_range)
        pbar = tqdm.tqdm(focus_range, desc="Scanning lens", leave=False)
        for i, position in enumerate(pbar):
            pbar.write(f"Moving objective lens to {position:4.02f} mm", end=" | ")
            self.focus_stage.move_absolute(position)
            if isinstance(shm, tuple) or isinstance(shm, list):
                metrics[i] = np.mean([self.measure_metric(s, num_frames) for s in shm])
            else:
                metrics[i] = self.measure_metric(shm, num_frames)
            pbar.write(f"normalized variance: {metrics[i]:3.02e} (adu)")
        best_fit = fit_optimal_focus(focus_range, metrics)
        logger.info(f"Best-fit focus was {best_fit:4.02f} mm")
        self.focus_stage.move_absolute(best_fit)
        if config is not None:
            save = click.confirm(
                f"Would you like to save this to the \"{config['name']}\" configuration?",
                default=True,
            )
            if save:
                self.focus_stage.save_configuration(
                    index=config["idx"], name=config["name"], position=best_fit
                )
            self.focus_stage.move_configuration_name(config["name"])

    def autofocus_camfocus(
        self, shm, start_point, step_size=0.05, num_frames=100, config=None
    ):
        search_width = 1.5
        focus_range = np.arange(
            max(0, start_point - search_width / 2),
            min(25, start_point + search_width / 2),
            step_size,
        )

        metrics = np.empty_like(focus_range)
        pbar = tqdm.tqdm(focus_range, desc="Scanning camfocus", leave=False)
        for i, position in enumerate(pbar):
            pbar.write(f"Moving camera focus to {position:4.02f} mm", end=" | ")
            self.camfocus_stage.move_absolute(position)
            metrics[i] = self.measure_metric(shm, num_frames)
            pbar.write(f"normalized variance: {metrics[i]:3.02e} (adu)")

        best_fit = fit_optimal_focus(focus_range, metrics)
        logger.info(f"Best-fit focus was {best_fit:4.02f} mm")
        self.camfocus_stage.move_absolute(best_fit)
        if config is not None:
            save = click.confirm(
                f"Would you like to save this to the \"{config['name']}\" configuration?",
                default=True,
            )
            if save:
                self.camfocus_stage.save_configuration(
                    index=config["idx"], name=config["name"], position=best_fit
                )
            self.camfocus_stage.move_configuration_name(config["name"])

    def measure_metric(self, shm, num_frames, **kwargs):
        cube = shm.multi_recv_data(num_frames, outputFormat=2, **kwargs)
        frame = np.median(cube, axis=0, overwrite_input=True)
        return autofocus_metric(frame)


def fit_optimal_focus(focus, metrics):
    # fit quadratic to curve, make sure
    # to convert back to origina domain and range
    poly = Polynomial.fit(focus, metrics, deg=2).convert()
    # vertex of polynomial
    return -poly.coef[1] / (2 * poly.coef[2])


def autofocus_metric(frame):
    # calculate normalized variance
    var = np.var(frame)
    mean = np.mean(frame)
    return var / mean


@click.command("autofocus")
@click.argument(
    "mode", type=click.Choice(["dual", "sdi", "single", "all"], case_sensitive=False)
)
def autofocus(mode: str):
    af = Autofocuser()
    welcome = "Welcome to the VAMPIRES autofocusing scripts"
    click.echo("=" * len(welcome))
    click.echo(welcome)
    click.echo("=" * len(welcome))
    if mode == "all":
        if click.confirm("Would you like to do dual-cam autofocus?", default=True):
            af.autofocus_dualcam("vpl")
        if click.confirm("Would you like to do SDI autofocus?", default=True):
            af.autofocus_sdi()
        if click.confirm("Would you like to do single-cam autofocus?", default=True):
            af.autofocus_singlecam()
    elif mode == "dual":
        af.autofocus_dualcam()
    elif mode == "sdi":
        af.autofocus_sdi()
    elif mode == "single":
        af.autofocus_singlecam()


if __name__ == "__main__":
    autofocus()
