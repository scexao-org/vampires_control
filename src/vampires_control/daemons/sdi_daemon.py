from argparse import ArgumentParser
import logging
from swmain.network.pyroclient import connect
from device_control.vampires import PYRO_KEYS
from swmain.redis import update_keys
from rich.prompt import Prompt, Confirm
from rich.progress import track
from rich.live import Live
from rich.spinner import Spinner

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

SDI_MODES = (
    "HALPHA",
    "SII"
)

parser = ArgumentParser(description="SDI Daemon for synchronizing exposures with the differential filter wheel")
parser.add_argument("mode", choices=SDI_MODES, type=str.upper, help="SDI Mode.")
parser.add_argument("-N", default=1, type=int, help="Number of cubes to acquire per diff wheel position. Default is %(default)d")

diff_wheel = connect(PYRO_KEYS["diffwheel"])

def prepare_halpha():
    # diff_wheel.move_configuration_idx(2, wait=True)
    indices = (2, 5)
    return indices

def prepare_sii():
    # diff_wheel.move_configuration_idx(3, wait=True)
    indices = (3, 6)
    return indices


def push_updates():
    pass
import time
def trigger_acquisition(N=1):
    time.sleep(0.5)


def sdi_loop(indices, N=1, mode=""):
    # with Live(Spinner("shark", text=f"SDI Control Loop ({mode})"), refresh_per_second=10) as live:
    while True:
        # move to first position
        for i in track(range(1, 3), description="Wheel state", transient=True):
            print(f"Moving to diff wheel state {i}: {indices[i - 1]}")
            # diff_wheel.move_configuration_idx(indices[i], wait=True)
            push_updates()
            trigger_acquisition()

def main():
    args = parser.parse_args()
    if args.mode == "HALPHA":
        inds = prepare_halpha()
    elif args.mode == "SII":
        inds = prepare_sii()

    result = Confirm.ask("Adjust camera settings. Confirm when ready.")
    if not result:
        return
    
    sdi_loop(inds, mode=args.mode, N=args.N)

if __name__ == "__main__":
    main()