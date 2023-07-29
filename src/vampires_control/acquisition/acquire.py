import multiprocessing as mp
import time
from datetime import datetime
from pathlib import Path

import click

from camstack.core.tmux import find_or_create_remote
from swmain.redis import update_keys
from vampires_control.acquisition import logger
from vampires_control.cameras import connect_cameras

DATA_DIR_BASE = Path("/mnt/tier0/")
ARCHIVE_DATA_DIR_BASE = Path("/mnt/tier1/ARCHIVED_DATA")

LOG_TMUX = {
    1: find_or_create_remote("vcam1_log", "scexao@scexao6"),
    2: find_or_create_remote("vcam2_log", "scexao@scexao6"),
}

DATA_TYPES = (
    "OBJECT",
    "DARK",
    "FLAT",
    "BIAS",
    "SKYFLAT",
    "DOMEFLAT",
    "COMPARISON",
    "TEST",
)

CAMS = connect_cameras()


def start_acq_one_camera(
    base_dir: Path, cam_num: int, num_per_cube: int, data_type="OBJECT"
):
    tmux = LOG_TMUX[cam_num]
    save_dir = base_dir / f"vcam{cam_num}"
    tmux.send_keys(f"mkdir -p {save_dir.absolute()}")
    CAMS[cam_num - 1].set_keyword("DATA-TYP", data_type.upper())
    tmux.send_keys(
        f"milk-logshim -c aol0log vcam{cam_num} {num_per_cube} {save_dir.absolute()} &"
    )
    if cam_num == 1:
        update_keys(U_VLOG1=True)
    else:
        update_keys(U_VLOG2=True)


def kill_acq_one_camera(cam_num):
    tmux = LOG_TMUX[cam_num]
    tmux.send_keys(f"milk-logshimoff vcam{cam_num}")
    if cam_num == 1:
        update_keys(U_VLOG1=False)
    else:
        update_keys(U_VLOG2=False)
    time.sleep(4)
    tmux.send_keys(f"milk-logshimkill vcam{cam_num}")


def pause_acq_one_camera(cam_num):
    tmux = LOG_TMUX[cam_num]
    tmux.send_keys(f"milk-logshimoff vcam{cam_num}")
    if cam_num == 1:
        update_keys(U_VLOG1=False)
    else:
        update_keys(U_VLOG2=False)


def resume_acq_one_camera(cam_num):
    tmux = LOG_TMUX[cam_num]
    tmux.send_keys(f"milk-logshimon vcam{cam_num}")
    if cam_num == 1:
        update_keys(U_VLOG1=True)
    else:
        update_keys(U_VLOG2=True)


@click.command("startlog")
@click.option("-n", "--nframes", type=int, prompt="Specify number of frames per cube")
@click.option(
    "-c", "--cam", default=-1, type=int, prompt="Specify camera, if -1 uses both"
)
@click.option(
    "-a/-na", "--archive/--no-archive", default=False, prompt="Archive data to Gen2"
)
@click.option(
    "--data-type",
    "-t",
    default="OBJECT",
    type=click.Choice(DATA_TYPES, case_sensitive=False),
    help="Subaru-style data type",
    prompt="Data type",
)
def start_acquisition(nframes, data_type="OBJECT", cam=-1, archive=False, watch=True):
    subfold = datetime.utcnow().strftime("%Y%m%d")
    base_dir = ARCHIVE_DATA_DIR_BASE / subfold if archive else DATA_DIR_BASE / subfold
    logger.info(f"Saving data to base directory {base_dir}")
    with mp.Pool(2) as pool:
        if cam in (-1, 1):
            pool.apply_async(
                start_acq_one_camera, args=(base_dir, 1, nframes, data_type)
            )
        if cam in (-1, 2):
            pool.apply_async(
                start_acq_one_camera, args=(base_dir, 2, nframes, data_type)
            )
        pool.close()
        pool.join()
    if not watch:
        return
    it = 0
    update_interval = 10
    try:
        while True:
            if it % update_interval == 0:
                logger.info("...acquiring...")
            it += 1
            time.sleep(0.1)
    finally:
        logger.info("stopping acquisition")
        with mp.Pool(2) as pool:
            if cam in (-1, 1):
                pool.apply_async(kill_acq_one_camera, args=(1,))
            if cam in (-1, 2):
                pool.apply_async(kill_acq_one_camera, args=(2,))
            pool.close()
            pool.join()


@click.command("stoplog")
@click.option(
    "-c", "--cam", default=-1, type=int, help="Specify camera, if -1 uses both"
)
def stop_acquisition(cam=-1):
    logger.info(f"Stopping data acquisition")
    with mp.Pool(2) as pool:
        if cam in (-1, 1):
            pool.apply_async(kill_acq_one_camera, args=(1,))
        if cam in (-1, 2):
            pool.apply_async(kill_acq_one_camera, args=(2,))
        pool.close()
        pool.join()


@click.command("pauselog")
@click.option(
    "-c", "--cam", default=-1, type=int, help="Specify camera, if -1 uses both"
)
def pause_acquisition(cam=-1):
    logger.info(f"Pausing data acquisition")
    with mp.Pool(2) as pool:
        if cam in (-1, 1):
            pool.apply_async(pause_acq_one_camera, args=(1,))
        if cam in (-1, 2):
            pool.apply_async(pause_acq_one_camera, args=(2,))
        pool.close()
        pool.join()


@click.command("resumelog")
@click.option(
    "-c", "--cam", default=-1, type=int, help="Specify camera, if -1 uses both"
)
def resume_acquisition(cam=-1):
    logger.info(f"Resuming data acquisition")
    with mp.Pool(2) as pool:
        if cam in (-1, 1):
            pool.apply_async(resume_acq_one_camera, args=(1,))
        if cam in (-1, 2):
            pool.apply_async(resume_acq_one_camera, args=(2,))
        pool.close()
        pool.join()
