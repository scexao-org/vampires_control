import multiprocessing as mp
import subprocess
import time
from pathlib import Path

import click

# from swmain.redis import update_keys
import swmain.redis as swr

from vampires_control.acquisition import logger
from vampires_control.cameras import connect_cameras

DATA_DIR_BASE = Path("/mnt/fuuu/")
ARCHIVE_DATA_DIR_BASE = Path("/mnt/fuuu/ARCHIVED_DATA")
# DATA_DIR_BASE = Path("/mnt/tier0/")
# ARCHIVE_DATA_DIR_BASE = Path("/mnt/tier1/ARCHIVED_DATA")


def update_keys(**kwargs):
    for _ in range(10):
        try:
            swr.update_keys(**kwargs)
            break
        except Exception:
            time.sleep(0.5)


DATA_TYPES = (
    "ACQUISITION",
    "BIAS",
    "COMPARISON",
    "DARK",
    "DOMEFLAT",
    "FLAT",
    "FOCUSING",
    "OBJECT",
    "SKYFLAT",
    "STANDARD",
    "TEST",
)
# BASE_COMMAND = ("ssh", "scexao@scexao6", "milk-streamFITSlog", "-cset", "aol0log")
BASE_COMMAND = ("ssh", "scexao@scexao5", "milk-streamFITSlog", "-cset", "q_asl")

CAMS = connect_cameras()


def start_acq_one_camera(
    base_dir: Path,
    cam_num: int,
    num_per_cube: int,
    num_cubes: int = -1,
    data_type="OBJECT",
    start=False,
):
    save_dir = base_dir  # / datetime.utcnow().strftime("%Y%m%d") / f"vcam{cam_num}"
    click.echo(f"Saving data to directory {save_dir}")
    CAMS[cam_num - 1].set_keyword("DATA-TYP", data_type.upper())
    cmd = [*BASE_COMMAND, "-z", f"{num_per_cube}", "-d", save_dir.absolute()]
    if num_cubes > 0:
        cmd.extend(("-c", f"{num_cubes}"))
    cmd.extend((f"vcam{cam_num}", "pstart"))
    subprocess.run(cmd, capture_output=True)
    if start:
        resume_acq_one_camera(cam_num=cam_num, num_cubes=num_cubes)


def kill_acq_one_camera(cam_num):
    cmd = [*BASE_COMMAND, f"vcam{cam_num}", "kill"]
    subprocess.run(cmd, capture_output=True)
    if cam_num == 1:
        update_keys(U_VLOG1=False)
    else:
        update_keys(U_VLOG2=False)


def stop_acq_one_camera(cam_num):
    cmd = [*BASE_COMMAND, f"vcam{cam_num}", "pstop"]
    subprocess.run(cmd, capture_output=True)
    if cam_num == 1:
        update_keys(U_VLOG1=False)
    else:
        update_keys(U_VLOG2=False)


def pause_acq_one_camera(cam_num, wait_for_complete=False):
    cmd = [*BASE_COMMAND, f"vcam{cam_num}"]
    cmd.append("offc" if wait_for_complete else "off")
    subprocess.run(cmd, capture_output=True)
    if cam_num == 1:
        update_keys(U_VLOG1=False)
    else:
        update_keys(U_VLOG2=False)


def resume_acq_one_camera(cam_num, num_cubes=-1):
    cmd = list(BASE_COMMAND)
    if num_cubes > 0:
        cmd.extend(("-c", f"{num_cubes}"))
    cmd.extend((f"vcam{cam_num}", "on"))
    subprocess.run(cmd, capture_output=True)
    if cam_num == 1:
        update_keys(U_VLOG1=True)
    else:
        update_keys(U_VLOG2=True)


@click.command("startlog")
@click.option("-n", "--nframes", type=int, prompt="Specify number of frames per cube")
@click.option(
    "-z", "--ncubes", type=int, default=-1, prompt="Specify number of cubes (-1 for infinite)"
)
@click.option("-c", "--cam", default=-1, type=int, prompt="Specify camera, if -1 uses both")
@click.option("-a/-na", "--archive/--no-archive", default=False, prompt="Archive data to Gen2")
@click.option(
    "--data-type",
    "-t",
    default="OBJECT",
    type=click.Choice(DATA_TYPES, case_sensitive=False),
    help="Subaru-style data type",
    prompt="Data type",
)
def start_acquisition_main(nframes, ncubes=-1, data_type="OBJECT", cam=-1, archive=False):
    if archive:
        base_dir = ARCHIVE_DATA_DIR_BASE
    else:
        base_dir = click.prompt("Please enter save directory", type=Path, default=DATA_DIR_BASE)
    return start_acquisition(
        nframes, ncubes=ncubes, data_type=data_type, cam=cam, base_dir=base_dir
    )


def start_acquisition(nframes, ncubes=-1, data_type="OBJECT", cam=-1, archive=False, base_dir=None):
    if base_dir is None:
        base_dir = ARCHIVE_DATA_DIR_BASE if archive else DATA_DIR_BASE
    else:
        base_dir = Path(base_dir)
    click.echo(f"Saving data to base directory {base_dir}")
    with mp.Pool(2) as pool:
        if cam in (-1, 1):
            pool.apply_async(
                start_acq_one_camera, args=(base_dir, 1, nframes, ncubes, data_type, False)
            )
        if cam in (-1, 2):
            pool.apply_async(
                start_acq_one_camera, args=(base_dir, 2, nframes, ncubes, data_type, False)
            )
        pool.close()
        pool.join()
    msg = "\nLogger process started"
    msg += "-\nlogging will start after running 'startlog'"
    click.echo(msg)


@click.command("datatype")
@click.option(
    "--data-type",
    "-t",
    default="OBJECT",
    type=click.Choice(DATA_TYPES, case_sensitive=False),
    help="Subaru-style data type",
    prompt="Data type",
)
def set_datatype_main(data_type: str) -> None:
    set_datatype(data_type)


def set_datatype(data_type: str) -> None:
    for i, cam in enumerate(CAMS):
        cam.set_keyword("DATA-TYP", data_type.upper())
        click.echo(f"Cam {i + 1} DATA-TYP={data_type}")


@click.command("stoplog")
@click.option("-c", "--cam", default=-1, type=int, help="Specify camera, if -1 uses both")
@click.option(
    "-k/-nk", "--kill/--no-kill", default=True, help="Kills logging process and closes tmux"
)
def stop_acquisition_main(cam=-1, kill=True):
    stop_acquisition(cam, kill)


def stop_acquisition(cam=-1, kill=True):
    logger.info("Stopping data acquisition")
    func = kill_acq_one_camera if kill else stop_acq_one_camera
    with mp.Pool(2) as pool:
        if cam in (-1, 1):
            pool.apply_async(func, args=(1,))
        if cam in (-1, 2):
            pool.apply_async(func, args=(2,))
        pool.close()
        pool.join()


@click.command("pauselog")
@click.option("-c", "--cam", default=-1, type=int, help="Specify camera, if -1 uses both")
@click.option("-w/-nw", "--wait/--no-wait", default=False, help="Finish last cube before pausing")
def pause_acquisition_main(cam=-1, wait: bool = False):
    pause_acquisition(cam, wait)


def pause_acquisition(cam=-1, wait: bool = False):
    logger.info("Pausing data acquisition")
    with mp.Pool(2) as pool:
        if cam in (-1, 1):
            pool.apply_async(pause_acq_one_camera, args=(1, wait))
        if cam in (-1, 2):
            pool.apply_async(pause_acq_one_camera, args=(2, wait))
        pool.close()
        pool.join()


@click.command("resumelog")
@click.option("-c", "--cam", default=-1, type=int, help="Specify camera, if -1 uses both")
@click.option(
    "-z", "--ncubes", type=int, default=-1, prompt="Specify number of cubes (-1 for infinite)"
)
def resume_acquisition_main(cam=-1, ncubes=-1):
    resume_acquisition(cam, ncubes)


def resume_acquisition(cam=-1, ncubes=-1):
    logger.info("Resuming data acquisition")
    with mp.Pool(2) as pool:
        if cam in (-1, 1):
            pool.apply_async(resume_acq_one_camera, args=(1, ncubes))
        if cam in (-1, 2):
            pool.apply_async(resume_acq_one_camera, args=(2, ncubes))
        pool.close()
        pool.join()
