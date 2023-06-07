import logging
import os
from argparse import ArgumentParser
from pathlib import Path
from time import sleep

import pandas as pd

from device_control.pyro_keys import VAMPIRES
from swmain.network.pyroclient import connect
from swmain.redis import update_keys

# set up logging
formatter = logging.Formatter(
    "%(asctime)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("vampires_qwp_daemon")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

conf_dir = Path(
    os.getenv("CONF_DIR", f"{os.getenv('HOME')}/src/vampires_control/conf/")
)

parser = ArgumentParser(
    description="VAMPIRES QWP daemon",
    usage="Enables tracking laws for the VAMPIRES quarter-wave plates. Right now, the only tracking law is the 'filter' law, which uses stored calibration values for counteracting the diattenuation of the visible periscope depending on the VAMPIRES filter and differential filter.",
)
parser.add_argument(
    "-m",
    "--mode",
    default="filter",
    choices=("filter",),
    help="Tracking law, by default '%(default)s'",
)
parser.add_argument(
    "-t",
    type=float,
    default=5,
    help="Polling time in seconds, by default %(default)f s",
)


def filter_tracking_mode(polling_time=5):
    conf_data = pd.read_csv(conf_dir / "data" / "conf_vampires_qwp_filter_data.csv")
    filter = connect(VAMPIRES.FILT)
    diffwheel = connect(VAMPIRES.DIFF)
    qwp1 = connect(VAMPIRES.QWP1)
    qwp2 = connect(VAMPIRES.QWP2)
    update_keys(U_QWPMOD="FILTER")
    while True:
        # check if Halpha or SII filters are in
        _, diff_filter = diffwheel.get_configuration()
        if "H-alpha" in diff_filter:
            curr_filter = "H-alpha"
        elif "SII" in diff_filter:
            curr_filter = "SII"
        else:
            # Otherwise get from VAMPIRES filter
            curr_filter = filter.status()

        # lookup values from table, fall back to default if unknown
        indices = conf_data["filter"] == curr_filter
        if len(indices) == 0:
            curr_filter = "Unknown"
            conf_row = conf_data.loc[conf_data["filter"] == "default"]
        else:
            conf_row = conf_data.loc[indices]
        qwp1_pos = conf_row["qwp1"].iloc[0]
        qwp2_pos = conf_row["qwp2"].iloc[0]
        logger.info(f"filter={curr_filter}, QWP1 = {qwp1_pos}°, QWP2 = {qwp2_pos}°")
        qwp1.move_absolute(float(qwp1_pos))
        qwp2.move_absolute(float(qwp2_pos))
        # status and sleep
        qwp1.update_keys()
        qwp2.update_keys()
        sleep(polling_time)


def main():
    args = parser.parse_args()
    if args.mode == "filter":
        try:
            filter_tracking_mode(args.t)
        finally:
            # update mode to off:
            update_keys(U_QWPMOD="NONE")


if __name__ == "__main__":
    main()
