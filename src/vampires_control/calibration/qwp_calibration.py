import logging

import click
import numpy as np
import tqdm.auto as tqdm
from pyMilk.interfacing.isio_shmlib import SHM
from swmain.network.pyroclient import connect

# set up logging
formatter = logging.Formatter("%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("qwp_sweep")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class QWPOptimizer:
    """
    QWPOptimizer
    """

    def __init__(self):
        self.cameras = {1: connect("VCAM1"), 2: connect("VCAM2")}
        self.shms = {1: SHM("vcam1"), 2: SHM("vcam2")}
        self.beamsplitter = connect("VAMPIRES_BS")
        self.filter = connect("VAMPIRES_FILT")
        self.qwp1 = connect("VAMPIRES_QWP1")
        self.qwp2 = connect("VAMPIRES_QWP2")

    def run(self, num_frames=5):
        logger.info("Beginning QWP calibration")
        # check if beamsplitter is inserted
        _, bs_config = self.beamsplitter.get_configuration()
        logger.debug(f"beamsplitter: {bs_config}")
        if bs_config.upper() != "PBS":
            # if beamsplitter is not inserted, prompt
            logger.warn("Polarizing beamsplitter is not inserted")
            click.confirm("Would you like to insert the beamsplitter?", abort=True, default=True)
            # insert beamsplitter
            logger.info("Inserting PBS beamsplitter")
            self.beamsplitter.move_configuration_name("PBS")

        result_dict = {}
        qwp_angles = None
        for config in tqdm.tqdm(self.filter.get_configurations(), desc="Filter"):
            if config["name"] == "625-50":
                continue
            self.filter.move_configuration_idx(config["idx"])
            logger.info(f"Moving filter to {config['name']}")
            # prepare cameras
            click.confirm("Adjust camera settings and confirm when ready", default=True, abort=True)
            qwp_angles, metrics = self.get_values_for_filter(num_frames=num_frames)
            result_dict[config["name"]] = metrics

        return qwp_angles, result_dict

    def get_values_for_filter(self, num_frames=5):
        qwp_angles = np.arange(0, 181, 5)
        metrics = np.empty((len(qwp_angles), len(qwp_angles)))
        for i, ang1 in enumerate(tqdm.tqdm(qwp_angles, desc="Scanning QWP1", leave=False)):
            logger.info(f"Moving QWP1 to {ang1:3.01f} deg")
            self.qwp1.move_absolute(ang1)
            # reverse every other qwp2 angle
            qwp2_angles = qwp_angles
            if i % 2:
                qwp2_angles = reversed(qwp_angles)
            for j, ang2 in enumerate(tqdm.tqdm(qwp2_angles, desc="Scanning QWP2", leave=False)):
                logger.info(f"Moving QWP2 to {ang2:3.01f} deg")
                self.qwp2.move_absolute(ang2)
                cube = self.shms[1].multi_recv_data(num_frames, output_as_cube=True)
                metrics[i, j] = np.median(cube, overwrite_input=True)
            if i % 2:
                metrics[i] = metrics[i][::-1]

        return qwp_angles, metrics


def get_focus_from_metric(focus, metrics):
    # fit quadratic to curve
    poly = np.polynomial.Polynomial.fit(focus, metrics, deg=2)
    # vertex is at -b / 2a
    coefs = poly.convert().coef
    return -coefs[1] / (2 * coefs[2])
