from argparse import ArgumentParser
import logging
from swmain.network.pyroclient import connect
from device_control.vampires import PYRO_KEYS
from swmain.redis import update_keys
from rich.prompt import Prompt, Confirm
from rich.progress import track
from rich.live import Live
from rich.spinner import Spinner
import zmq

from vampires_control.daemons import SDI_DAEMON_PORT, TRIGGER_READY_PORT

# set up logging
formatter = logging.Formatter(
    "%(asctime)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("vampires_sdi_daemon")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

SDI_MODES = ("HALPHA", "SII")

parser = ArgumentParser(
    description="SDI Daemon for synchronizing exposures with the differential filter wheel"
)
parser.add_argument("mode", choices=SDI_MODES, type=str.upper, help="SDI Mode.")
parser.add_argument(
    "-N",
    default=1,
    type=int,
    help="Number of cubes to acquire per diff wheel position. Default is %(default)d",
)

diff_wheel = connect(PYRO_KEYS["diffwheel"])


def prepare_halpha():
    logger.info("Moving diff wheel into first H-alpha position")
    # diff_wheel.move_configuration_idx(2, wait=True)
    indices = (2, 5)
    return indices


def prepare_sii():
    logger.info("Moving diff wheel into first SII position")
    # diff_wheel.move_configuration_idx(3, wait=True)
    indices = (3, 6)
    return indices


def push_updates():
    pass


import time


def sdi_loop(indices, N=1, mode=""):
    # with Live(Spinner("shark", text=f"SDI Control Loop ({mode})"), refresh_per_second=10) as live:
    logger.debug("Preparing 0MQ socket")
    ctx = zmq.Context()
    sdi_socket = ctx.socket(zmq.REP)
    sdi_socket.bind(SDI_DAEMON_PORT)

    logger.info("Starting loop")
    while True:
        # move between first and second position
        for posn in range(1, 3):
            # wait until ready to trigger again
            logger.info(
                f"[State {posn}] moving diff wheel to configuration: {indices[posn - 1]}"
            )
            # diff_wheel.move_configuration_idx(indices[i], wait=True)
            time.sleep(1)
            push_updates()
            for i in range(N):
                # handle inputs until we get clear "READY" input
                while True:
                    response = sdi_socket.recv_string()
                    logger.debug(f"received response {response}")
                    if response == "status READY":
                        # send acquire signal
                        msg = "trigger GO"
                        logger.debug(f"Sending message {msg}")
                        logger.info(f"    ({i + 1}/{N}) Triggering acquisition")
                        sdi_socket.send_string(msg)
                        break
                    elif response == "status BUSY":
                        pass
                    else:
                        logger.warn(f"Unrecognized input {response}")
                    msg = "trigger HOLD"
                    logger.debug(f"Sending message {msg}")
                    sdi_socket.send_string(msg)


def main():
    args = parser.parse_args()

    if args.mode == "HALPHA":
        wheel_indices = prepare_halpha()
    elif args.mode == "SII":
        wheel_indices = prepare_sii()

    sdi_loop(wheel_indices, mode=args.mode, N=args.N)


if __name__ == "__main__":
    main()
