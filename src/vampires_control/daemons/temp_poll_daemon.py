from argparse import ArgumentParser
import os
from pathlib import Path
from swmain.network.pyroclient import connect
from device_control.vampires import PYRO_KEYS
import pandas as pd
from time import sleep
import logging


# set up logging
formatter = logging.Formatter(
    "%(asctime)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("vampires_temp_daemon")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

parser = ArgumentParser(
    description="VAMPIRES Temperature daemon",
    usage="Will consistently ping the FLC temperature sensor and both camera sensors to push status updates",
)
parser.add_argument(
    "-t",
    type=float,
    default=5,
    help="Polling time in seconds, by default %(default)f s",
)



def main():
    args = parser.parse_args()
    tc = connect(PYRO_KEYS["tc"])
    while True:
        tc_temp = tc.temp
        logger.info(f"FLC = {tc_temp} °C")
        # status and sleep
        sleep(args.t)
 


if __name__ == "__main__":
    main()
