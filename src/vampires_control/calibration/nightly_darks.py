import os
import pprint
import subprocess
import time
from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path

import click
import pandas as pd
from astropy.io import fits
from scxconf.pyrokeys import VCAM1, VCAM2
from swmain.network.pyroclient import connect

logger = getLogger(__file__)


def _default_sc5_archive_folder():
    base = Path("/mnt/fuuu/ARCHIVED_DATA")
    today = datetime.now(timezone.utc)
    return base / f"{today:%Y%m%d}"


def _default_output():
    today = datetime.now(timezone.utc)
    return Path(f"{today:%Y%m%d})_vcam_darks.csv")


def _relevant_header_for_darks(filename) -> dict:
    path = Path(filename)
    hdr = fits.getheader(path)
    dark_keys = ("U_CAMERA", "EXPTIME", "U_DETMOD", "PRD-MIN1", "PRD-MIN2", "PRD-RNG1", "PRD-RNG2")
    return {k: hdr[k] for k in dark_keys}


def vampires_dark_table(folder=None):
    if folder is None:
        folder = _default_sc5_archive_folder()
    # get all vcam1 and vcam2 filenames
    filenames = folder.glob("vcam[12]/vcam*.fits")
    logger.info(f"Found {len(filenames)} input FITS files")
    # get a table from all filenames
    header_rows = [_relevant_header_for_darks(f) for f in filenames]
    # get unique combinations
    header_table = pd.DataFrame(header_rows).drop_duplicates()
    header_table.sort_values(
        ["PRD-MIN1", "PRD-MIN2", "PRD-RNG1", "PRD-RNG2", "U_DETMOD", "EXPTIME", "U_CAMERA"],
        inplace=True,
    )
    return header_table


def _estimate_total_time(headers, num_frames=250):
    tints = headers.groupby("U_CAMERA")["EXPTIME"].sum() * num_frames
    return tints.max()


BASE_COMMAND = ("milk-streamFITSlog", "-cset", "q_asl")


def _kill_log(cam: int):
    command = [*BASE_COMMAND, f"vcam{cam} kill"]
    subprocess.run(command, capture_output=True)


def _prep_log(cam_num: int, num_frame: int):
    save_dir = Path("/mnt/fuuu/ARCHIVED_DATA")
    click.echo(f"Saving data to directory {save_dir}")
    cmd = [
        *BASE_COMMAND,
        "-z",
        f"{num_frame}",
        "-d",
        save_dir.absolute(),
        "-c 1",
        f"vcam{cam_num}",
        "pstart",
    ]
    subprocess.run(cmd, capture_output=True)


def _run_log(cam_num: int):
    cmd = [*BASE_COMMAND, "-c 1", f"vcam{cam_num}", "on"]
    subprocess.run(cmd, capture_output=True)


def _set_readout_mode(cam: int, mode: str):
    if cam == 1:
        camera = connect(VCAM1)
    elif cam == 2:
        camera = connect(VCAM2)
    # readout mode
    camera.set_readout_mode(mode.strip().upper())


class WrongComputerError(BaseException):
    pass


def _set_camera_crop(camera, crop):
    width, height, w_offset, h_offset = crop
    click.echo(f"Setting camera crop {crop}")
    camera.set_camera_size(height, width, h_offset, w_offset)


def process_dark_frames(table, num_frames=250):
    table["crop"] = table.apply(
        lambda r: (r["PRD-MIN1"], r["PRD-MIN2"], r["PRD-RNG1"], r["PRD-RNG2"])
    )
    for key, group in table.groupby("crop"):
        if 1 in group["U_CAMERA"]:
            _set_camera_crop(connect(VCAM1), key)
            _kill_log(1)

        if 2 in group["U_CAMERA"]:
            _set_camera_crop(connect(VCAM2), key)
            _kill_log(2)

        while not click.confirm("Confirm camera stream has restarted", default=True):
            pass

        if 1 in group["U_CAMERA"]:
            _prep_log(1, num_frames)
        if 2 in group["U_CAMERA"]:
            _prep_log(2, num_frames)

        for key2, group2 in group.sort_values("U_DETMOD", ascending=False).groupby("U_DETMOD"):
            if 1 in group2["U_CAMERA"]:
                _set_readout_mode(1, key2)

            if 2 in group2["U_CAMERA"]:
                _set_readout_mode(2, key2)

            while not click.confirm("Confirm camera stream has restarted", default=True):
                pass

            for _, row in group2.iterrows():
                if row["U_CAMERA"] == 1:
                    camera = connect(VCAM1)
                elif row["U_CAMERA"] == 2:
                    camera = connect(VCAM2)
                camera.set_keyword("DATA-TYP", "DARK")
                tint = row["EXPTIME"] * num_frames + 2  # s
                camera.set_tint(tint)
                _run_log(row["U_CAMERA"])
                time.sleep(tint)


@click.command("vampires_auto_darks")
@click.argument("folder", type=Path, default=_default_sc5_archive_folder())
def main(folder):
    if os.getenv("WHICHCOMP", "") != "5":
        msg = "This script must be run from sc5 in the `vampires_control` conda env"
        raise WrongComputerError(msg)
    table = vampires_dark_table(folder)
    pprint.pprint(table)
    est_tint = _estimate_total_time(table)
    click.echo(f"Est. time for 250 frames is {est_tint/60:.01f} min.")
    num_frames = click.prompt("Please enter num frames", default=250, type=int)
    process_dark_frames(table, num_frames)


# @click.command("vampires_auto_darks")
# @click.option("-e", "--exptime", default=0.1, type=float, prompt="Specify exposure time")
# @click.option("-n", "--nframes", default=100, type=int, prompt="Specify number of frames per cube")
# @click.option(
#     "-z", "--ncubes", type=int, default=1, prompt="Specify number of cubes (-1 for infinite)"
# )
# @click.option("-c", "--cam", default=-1, type=int, prompt="Specify camera, if -1 uses both")
# @click.option("-a/-na", "--archive/--no-archive", default=True, prompt="Archive data to Gen2")
# def main(exptime, nframes, ncubes, cam, archive):
#     # step 1: take pinholes
#     delta_time = nframes * ncubes * exptime  # s
#     if click.confirm("Would you like to take pinholes?", default=True):
#         click.echo(f"Beginning to take pinholes, should take ~{delta_time:.0f}s")
#         calibs.take_pinholes.callback(
#             nframes=nframes, ncubes=ncubes, exptime=exptime, cam=cam, archive=archive
#         )
#         time.sleep(delta_time)

#     if click.confirm("Would you like to move pinholes out?", default=True):
#         subprocess.run(["ssh", "sc2", "src_fib", "out"], capture_output=True)

#     if click.confirm("Would you like to take flats?", default=True):
#         click.echo(f"Beginning to take flats, should take ~{delta_time:.0f}s")
#         calibs.take_flats.callback(
#             nframes=nframes, ncubes=ncubes, exptime=exptime, cam=cam, archive=archive
#         )
#         time.sleep(delta_time)

#     if click.confirm("Would you like to take darks?", default=True):
#         move_diff = click.confirm("Would you like to block using diff wheel?", default=True)
#         if move_diff:
#             diff = connect(VAMPIRES.DIFF)
#             prior_diff_position = diff.get_position()
#             diff.move_relative(31)
#         click.echo(f"Beginning to take darks, should take ~{delta_time:.0f}s")
#         calibs.take_darks.callback(
#             nframes=nframes, ncubes=ncubes, exptime=exptime, cam=cam, archive=archive
#         )
#         time.sleep(delta_time)
#         if move_diff:
#             diff.move_absolute(prior_diff_position)
