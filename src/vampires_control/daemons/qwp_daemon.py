import logging
import multiprocessing as mp
import os
from argparse import ArgumentParser
from pathlib import Path
from time import sleep

import pandas as pd
from Pyro4.errors import CommunicationError

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


def move_qwp(qwpnum, theta):
    if qwpnum == 1:
        qwp = connect(VAMPIRES.QWP1)
    elif qwpnum == 2:
        qwp = connect(VAMPIRES.QWP2)
    return qwp.move_absolute(theta)


def filter_tracking_mode(polling_time=5):
    conf_data = pd.read_csv(conf_dir / "data" / "conf_vampires_qwp_filter_data.csv")
    # filt = connect(VAMPIRES.FILT)
    # diffwheel = connect(VAMPIRES.DIFF)
    update_keys(U_QWPMOD="FILTER")
    while True:
        # check if Halpha or SII filters are in
        # _, diff_filter = diffwheel.get_configuration()
        diff_filter = "NA"  # TODO temporary
        if "H-alpha" in diff_filter:
            curr_filter = "H-alpha"
        elif "SII" in diff_filter:
            curr_filter = "SII"
        else:
            # Otherwise get from VAMPIRES filter
            # curr_filter = filt.get_status()
            curr_filter = "625-50"  # TODO temporary

        # lookup values from table, fall back to default if unknown
        indices = conf_data["filter"] == curr_filter
        if len(indices) == 0:
            curr_filter = "Unknown"
            conf_row = conf_data.loc[conf_data["filter"] == "default"]
        else:
            conf_row = conf_data.loc[indices]
        qwp1_pos = float(conf_row["qwp1"].iloc[0])
        qwp2_pos = float(conf_row["qwp2"].iloc[0])
        logger.info(f"filter={curr_filter}, QWP1 = {qwp1_pos}°, QWP2 = {qwp2_pos}°")
        # launch two processes to move each QWP simultaneously
        with mp.Pool(2) as pool:
            pool.apply_async(move_qwp, args=(1, qwp1_pos))
            pool.apply_async(move_qwp, args=(2, qwp2_pos))
            # wait for previous two results to complete
            pool.close()
            pool.join()
        sleep(polling_time)


def main():
    args = parser.parse_args()
    # connect to cameras
    if args.mode.lower() == "filter":
        try:
            filter_tracking_mode(polling_time=args.t)
        finally:
            # update mode to off:
            update_keys(U_QWPMOD="NONE")


if __name__ == "__main__":
    main()
