import logging
from argparse import ArgumentParser
from time import sleep

from device_control.pyro_keys import VAMPIRES
from swmain.autoretry import autoretry
from swmain.infra.badsystemd.aux import auto_register_to_watchers
from swmain.network.pyroclient import connect

# set up logging
formatter = logging.Formatter(
    "%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("flc_temps")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

parser = ArgumentParser(
    description="VAMPIRES FLC temperature poll daemon",
    usage="Will consistently ping the FLC temperature sensor to push status updates",
)
parser.add_argument(
    "-t",
    type=float,
    default=10,
    help="Polling time in seconds, by default %(default)f s",
)


@autoretry
def get_temperature_status(tc):
    tc_temp = tc.get_temp()
    tc.update_keys(temperature=tc_temp)
    status = f"FLC={tc_temp:4.01f}°C"
    return status


def main():
    args = parser.parse_args()
    auto_register_to_watchers("VCAM_TEMP", "VCAM temperature redis updater")
    tc = connect(VAMPIRES.TC)
    while True:
        status = get_temperature_status(tc)
        logger.info(status)
        # status and sleep
        sleep(args.t)


if __name__ == "__main__":
    main()
