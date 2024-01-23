import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Tuple

import click
import numpy as np
import pandas as pd
from swmain.infra.badsystemd.aux import auto_register_to_watchers
from swmain.redis import get_values, update_keys

from vampires_control.helpers import get_dominant_filter

# set up logging
formatter = logging.Formatter("%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("qwp_daemon")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

__all__ = ("TRACKING_LAWS", "VAMPIRESFilterTrackingLaw", "QWPTrackingDaemon")


class VAMPIRESFilterTrackingLaw:
    conf_dir: Path = Path(os.getenv("CONF_DIR", f"{os.getenv('HOME')}/src/vampires_control/conf/"))

    def __init__(self) -> None:
        self.conf_data = pd.read_csv(self.conf_dir / "data" / "conf_vampires_qwp_filter_data.csv")

    def __call__(self) -> Tuple[float, float]:
        filt = self.get_filter()
        logger.info(f"Current filter is {filt}")
        angs = self.get_angles_from_conf(filt)
        return angs

    def get_filter(self):
        filter_dict = get_values(("U_DIFFL1", "U_FILTER"))
        curr_filter = get_dominant_filter(filter_dict["U_FILTER"], filter_dict["U_DIFFL1"])
        return curr_filter

    def get_angles_from_conf(self, filt: str) -> Tuple[float, float]:
        indices = self.conf_data["filter"] == filt
        if len(indices) == 0:
            conf_row = self.conf_data.loc[self.conf_data["filter"] == "default"]
        else:
            conf_row = self.conf_data.loc[indices]

        qwp1_angle = float(conf_row["qwp1"].iloc[0])
        qwp2_angle = float(conf_row["qwp2"].iloc[0])
        return qwp1_angle, qwp2_angle


TRACKING_LAWS = {"Filter": VAMPIRESFilterTrackingLaw}


class QWPTrackingDaemon:
    def move_qwps(self, qwp1_angle, qwp2_angle):
        logger.info(f"Moving QWP 1 to {qwp1_angle} deg")
        logger.info(f"Moving QWP 2 to {qwp2_angle} deg")
        p1 = subprocess.Popen(("vampires_qwp", "1", "goto", str(qwp1_angle)))
        p2 = subprocess.Popen(("vampires_qwp", "2", "goto", str(qwp2_angle)))
        p1.wait()
        p2.wait()

    def run(self, law="filter", poll=5):
        law_key = law.title()
        if law_key not in TRACKING_LAWS:
            msg = f"Unrecognized tracking law: {law_key}"
            raise ValueError(msg)
        tracking_law = TRACKING_LAWS[law_key]()  # instantiate tracking law object

        logger.info(f"Starting QWP tracking loop with {law_key} law")
        update_keys(U_QWPMOD=law_key)
        last_qwp1, last_qwp2 = get_values(("U_QWP1", "U_QWP2")).values()
        try:
            while True:
                qwp1_angle, qwp2_angle = tracking_law()
                # check if we have to move the QWPs
                if not np.isclose(qwp1_angle, last_qwp1) or not np.isclose(qwp2_angle, last_qwp2):
                    self.move_qwps(qwp1_angle, qwp2_angle)
                    last_qwp1, last_qwp2 = qwp1_angle, qwp2_angle
                time.sleep(poll)
        finally:
            update_keys(U_QWPMOD="None")


# conf_dir = Path(
#     os.getenv("CONF_DIR", f"{os.getenv('HOME')}/src/vampires_control/conf/")
# )

# parser = ArgumentParser(
#     description="QWP daemon",
#     usage="Enables tracking laws for the VAMPIRES quarter-wave plates. Right now, the only tracking law is the 'filter' law, which uses stored calibration values for counteracting the diattenuation of the visible periscope depending on the VAMPIRES filter and differential filter.",
# )
# parser.add_argument(
#     "-m",
#     "--mode",
#     default="filter",
#     choices=[k.lower() for k in TRACKING_LAWS.keys()]
#     help="Tracking law, by default '%(default)s'",
# )
# parser.add_argument(
#     "-t",
#     type=float,
#     default=10,
#     help="Polling time in seconds, by default %(default)f s",
# )


# def filter_tracking_mode(polling_time=10):
#     conf_data = pd.read_csv(conf_dir / "data" / "conf_vampires_qwp_filter_data.csv")

#     update_keys(U_QWPMOD="Filter")
#     last_qwp1, last_qwp2 = get_values(("U_QWP1", "U_QWP2")).values()
#     while True:
#         filter_dict = get_values(("U_DIFFL1", "U_FILTER"))
#         curr_filter = get_dominant_filter(
#             filter_dict["U_FILTER"], filter_dict["U_DIFFL1"]
#         )

#         # lookup values from table, fall back to default if unknown
#         indices = conf_data["filter"] == curr_filter
#         if len(indices) == 0:
#             curr_filter = "Unknown"
#             conf_row = conf_data.loc[conf_data["filter"] == "default"]
#         else:
#             conf_row = conf_data.loc[indices]
#         qwp1_pos = float(conf_row["qwp1"].iloc[0])
#         qwp2_pos = float(conf_row["qwp2"].iloc[0])
#         logger.info(
#             f"filter={curr_filter}, QWP1={qwp1_pos:6.02f}°, QWP2={qwp2_pos:6.02f}°"
#         )
#         # check if we have to move the QWPs
#         if np.isclose(qwp1_pos, last_qwp1) and np.isclose(qwp2_pos, last_qwp2):
#             sleep(polling_time)
#             continue
#         logger.info(f"Moving QWP1 to {qwp1_pos:6.02f}°, QWP2 to {qwp2_pos:6.02f}°")
#         # launch two processes to move each QWP simultaneously
#         p1 = subprocess.Popen(("vampires_qwp", "1", "goto", str(qwp1_pos)))
#         p2 = subprocess.Popen(("vampires_qwp", "2", "goto", str(qwp2_pos)))
#         p1.wait()
#         p2.wait()
#         last_qwp1, last_qwp2 = qwp1_pos, qwp2_pos
#         sleep(polling_time)


@click.command("qwp_daemon")
@click.option(
    "-l", "--law", type=click.Choice(TRACKING_LAWS.keys(), case_sensitive=False), default="filter"
)
@click.option("-p", "--poll", default=5, type=float, help="(s) Poll time for daemon")
def main(law: str, poll: float):
    auto_register_to_watchers("VAMP_QWP", "VAMPIRES QWP Tracking law daemon")
    daemon = QWPTrackingDaemon()
    daemon.run(law, poll=poll)


if __name__ == "__main__":
    main()
