
from argparse import ArgumentParser
import zmq
from rich.prompt import Confirm
import time
import sys
from rich.spinner import Spinner
from rich.progress import track

from functools import partial

from swmain.infra.tmux import find_or_create, send_keys, kill_running

from vampires_control.daemons import TRIGGER_READY_PORT, SDI_DAEMON_PORT, PDI_DAEMON_PORT
from vampires_control.acquisition.free_acquisition import acquire_cubes
from vampires_control.acquisition.blocked_acquisition import blocked_acquire_cubes
from vampires_control.acquisition import logger



DATA_TYPES = (
    "OBJECT",
    "DARK",
    "FLAT",
    "BIAS",
    "SKYFLAT",
    "DOMEFLAT",
    "COMPARISON",
    "TEST"
)

parser = ArgumentParser("acquire", description="Acquire data with VAMPIRES")
parser.add_argument("num_frames", type=int, help="Number of frames per cube")
parser.add_argument("-a", "--archive", action="store_true", help="If provided will archive to Gen2.")
parser.add_argument("-N", "--num-cubes", default=-1, type=int, help="Number of cubes. If -1, will acquire until aborted. Default is %(default)d")

parser.add_argument("-t", "--type", type=str.upper, default="OBJECT", choices=DATA_TYPES, help="FITS Data type")
parser.add_argument("--single-cam", const=1, nargs="?", choices=(1, 2), help="Only log from a single camera (which can be specified by passing --single-cam=1 or 2). Note that both cameras will still trigger.")
parser.add_argument("-P", "--pdi", action="store_true", help="PDI mode. In this mode every FITS cube exposure is triggered by the HWP daemon. All PDI settings (like number of cubes per HWP position) are handled by the HWP daemon.")
parser.add_argument("-S", "--sdi", type=str.upper, choices=("HALPHA", "SII"), help="SDI mode. In this mode, exposures are controlled by the SDI daemon.")
parser.add_argument("--sdi-num", default=1, type=int, help="(SDI mode only) Number of acquisitions per differential wheel position,  by default %(default)d.")

def handle_metadata():
    pass

def main():
    args = parser.parse_args()

    # determine whether using blocked triggering or free-running
    # The blocked mode is used whenever doing PDI or SDI to ensure
    # synchronization with devices (like the HWP or diff wheel)
    if args.pdi or args.sdi:
        acquisition_func = partial(blocked_acquire_cubes, pdi=args.pdi, sdi_mode=args.sdi, sdi_num_per=args.sdi_num)
    else:
        acquisition_func = acquire_cubes

    try:
        if args.num_cubes > 0:
            acquisition_func(args.num_frames, args.num_cubes)
        else:
            acquisition_func(args.num_frames, None)
    except KeyboardInterrupt as e:
        logger.info("This will be the last acquisition.")
        # TODO command for last acqusition
    finally:
        logger.info("Shutting down SDI daemon")
        kill_running(find_or_create("vampires_sdi_daemon"))


if __name__ == "__main__":
    main()