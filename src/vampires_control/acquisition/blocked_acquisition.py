from vampires_control.acquisition import logger
from swmain.infra.tmux import find_or_create, send_keys, kill_running
from vampires_control.daemons import SDI_DAEMON_PORT, PDI_DAEMON_PORT
import zmq
from rich.prompt import Confirm
from rich.progress import track
import sys
from itertools import repeat
import time


def get_pdi_socket(ctx):
    pdi_socket = ctx.socket(zmq.REQ)
    pdi_socket.connect(PDI_DAEMON_PORT)
    return pdi_socket


def trigger_acquisition(num_frames):
    logger.info("Starting acquisition")
    acq_time = num_frames * 5e-3 * 1e9  # seconds -> ns
    start_time = time.monotonic_ns()
    # TODO replace this with status call to logshim??
    while (time.monotonic_ns() - start_time) < acq_time:
        continue
    logger.info("Acquisition finished")


def prepare_sdi(ctx, sdi_mode=None, sdi_num_per=1):
    logger.info("Initializing SDI daemon")
    sdi_pane = find_or_create("vampires_sdi_daemon")

    logger.debug("Resetting tmux")
    kill_running(sdi_pane)

    # Before the command runs, let's make sure we're ready to move the diff wheel:
    result = Confirm.ask(
        f"Preparing for SDI mode - {sdi_mode}.\nConfirm when ready to move diff wheel.",
        default="y",
    )
    if not result:
        sys.exit(1)
    cmd = f"python -m vampires_control.daemons.sdi_daemon {sdi_mode} -N {sdi_num_per}"
    logger.debug(f"launching SDI daemon with tmux command '{cmd}'")
    send_keys(sdi_pane, cmd)

    logger.debug("connecting to SDI port")
    sdi_socket = ctx.socket(zmq.REQ)
    try:
        sdi_socket.connect(SDI_DAEMON_PORT)
    except zmq.ZMQError as e:
        logger.error("Could not connect to SDI port.", exc_info=True)
    # Now let's pause and allow for adjusting exposure times
    result = Confirm.ask("Adjust camera settings. Confirm when ready.", default="y")
    if not result:
        sys.exit(1)

    return sdi_socket


def blocked_acquire_cubes(
    num_frames, num_cubes=None, pdi=False, sdi_mode=None, sdi_num_per=1
):
    ctx = zmq.Context()
    pdi_socket = sdi_socket = None
    if pdi:
        if num_cubes is not None and num_cubes % 4 != 0:
            raise ValueError(
                "PDI Sequences must be multiples of 4 to allow for HWP rotation."
            )
        pdi_socket = get_pdi_socket(ctx)
    if sdi_mode is not None:
        if num_cubes is not None and num_cubes % 2 != 0:
            raise ValueError(
                "SDI Sequences must be multiples of 2 to allow for differential wheel switching."
            )
        sdi_socket = prepare_sdi(ctx, sdi_mode=sdi_mode, sdi_num_per=sdi_num_per)

    if num_cubes is None:
        iterator = repeat()
    else:
        iterator = track(range(num_cubes), description="Acquiring cubes")
    for _ in iterator:
        if sdi_mode is not None:
            # wait until SDI process says we're good to go
            while True:
                msg = "status READY"
                logger.debug(f"Sending message {msg}")
                sdi_socket.send_string(msg)
                logger.info("Waiting for response from SDI daemon...")
                response = sdi_socket.recv_string()
                logger.debug(f"received response {response}")
                if response == "trigger GO":
                    break
        ## acquire
        trigger_acquisition(num_frames=num_frames)
