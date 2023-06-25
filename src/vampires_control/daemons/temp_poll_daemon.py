import logging
from argparse import ArgumentParser
from time import sleep

from Pyro4.errors import CommunicationError

from device_control.pyro_keys import VAMPIRES
from swmain.autoretry import autoretry
from swmain.network.pyroclient import connect

# set up logging
formatter = logging.Formatter(
    "%(asctime)s|%(name)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("vamp_temps")
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
    default=10,
    help="Polling time in seconds, by default %(default)f s",
)


def connect_cameras():
    vcam1 = vcam2 = None
    try:
        vcam1 = connect("VCAM1")
    except CommunicationError:
        logger.warn("Could not connect to VCAM1- will not push keywords to camera")
    try:
        vcam2 = connect("VCAM2")
    except CommunicationError:
        logger.warn("Could not connect to VCAM2- will not push keywords to camera")
    return vcam1, vcam2


@autoretry
def get_temperature_status(tc, cams):
    tc_temp = tc.get_temp()
    tc.update_keys(temperature=tc_temp)
    status = f"FLC={tc_temp:4.01f}°C"
    for i, cam in enumerate(cams):
        if cam is None:
            continue
        cam_temp = cam.get_temperature()
        status += f", VCAM{i+1}={cam_temp:4.01f}°C"

    return status


def main():
    args = parser.parse_args()
    tc = connect(VAMPIRES.TC)
    cams = connect_cameras()
    while True:
        status = get_temperature_status(tc, cams)
        logger.info(status)
        # status and sleep
        sleep(args.t)


if __name__ == "__main__":
    main()
