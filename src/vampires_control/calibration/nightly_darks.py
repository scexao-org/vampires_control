import os
import pprint
import subprocess
import time
from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path

import click
import pandas as pd
import tqdm.auto as tqdm
from astropy.io import fits
from scxconf.pyrokeys import VCAM1, VCAM2
from swmain.network.pyroclient import connect

logger = getLogger(__file__)
_DEFAULT_DELAY = 2  # s


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
    dark_keys = (
        "PRD-MIN1",
        "PRD-MIN2",
        "PRD-RNG1",
        "PRD-RNG2",
        "OBS-MOD",
        "DATA-TYP",
        "U_DETMOD",
        "EXPTIME",
        "U_CAMERA",
    )
    return {k: hdr[k] for k in dark_keys}


def vampires_dark_table(folder=None):
    if folder is None:
        folder = _default_sc5_archive_folder()
    # get all vcam1 and vcam2 filenames
    filenames = list(folder.glob("vcam[12]/vcam*.fits"))
    n_input = len(filenames)
    logger.info(f"Found {n_input} input FITS files")
    if n_input == 0:
        msg = f"No FITS files found in VCAM1/2 folders of {folder}"
        raise ValueError(msg)
    # get a table from all filenames
    header_rows = [_relevant_header_for_darks(f) for f in filenames]
    # get unique combinations
    header_table = pd.DataFrame(header_rows).query("`DATA-TYP` not in ('DARK', 'BIAS')")
    dark_keys = ["PRD-MIN1", "PRD-MIN2", "PRD-RNG1", "PRD-RNG2", "U_DETMOD", "EXPTIME", "U_CAMERA"]
    header_table.drop_duplicates(dark_keys, keep="first", inplace=True)
    header_table.sort_values(dark_keys, inplace=True)
    return header_table


def _estimate_total_time(headers, num_frames=250):
    exptimes = headers.groupby("U_CAMERA")["EXPTIME"]
    tints = exptimes.sum() * num_frames + len(exptimes) * _DEFAULT_DELAY
    return tints.max()


BASE_COMMAND = ("milk-streamFITSlog", "-cset", "q_asl")


def _kill_log(cam: int):
    command = [*BASE_COMMAND, f"vcam{cam}", "kill"]
    subprocess.run(command, check=True, capture_output=True)


def _prep_log(cam_num: int, num_frame: int, folder: Path):
    click.echo(f"Saving data to directory {folder.absolute()}")
    cmd = [
        *BASE_COMMAND,
        "-z",
        f"{num_frame}",
        "-D",
        str(folder.absolute() / f"vcam{cam_num}"),
        "-c",
        "1",
        f"vcam{cam_num}",
        "pstart",
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _run_log(cam_num: int):
    cmd = [*BASE_COMMAND, "-c", "1", f"vcam{cam_num}", "on"]
    subprocess.run(cmd, check=True, capture_output=True)


def _set_readout_mode(cam: int, mode: str, pbar):
    if cam == 1:
        camera = connect(VCAM1)
    elif cam == 2:
        camera = connect(VCAM2)
    pbar.write(f"Setting readout mode to {mode} for VCAM{cam}")
    # readout mode
    camera.set_readout_mode(mode.strip().upper())


class WrongComputerError(BaseException):
    pass


def _set_camera_crop(camera, crop, obsmode, pbar):
    w_offset, h_offset, width, height = crop
    # gotta do backflips to make sure data is labeled correctly
    if obsmode.endswith("MBI"):
        modename = "MBI"
    elif obsmode.endswith("MBIR"):
        modename = "MBI_REDUCED"
    elif obsmode.endswith("PUP"):
        modename = "PUPIL"
    else:
        modename = "CUSTOM"

    pbar.write(f"Setting camera crop x={w_offset} y={h_offset} w={width} h={height} ({modename})")

    camera.set_camera_size(height, width, h_offset, w_offset, mode_name=modename)


def process_dark_frames(table, folder, num_frames=250):
    table["crop"] = table.apply(
        lambda r: (r["PRD-MIN1"], r["PRD-MIN2"], r["PRD-RNG1"], r["PRD-RNG2"]), axis=1
    )
    pbar = tqdm.tqdm(table.groupby("crop"), desc="Crop")
    for key, group in pbar:
        if 1 in group["U_CAMERA"]:
            _set_camera_crop(connect(VCAM1), key, group["OBS-MOD"].iloc[0], pbar=pbar)
            _kill_log(1)

        if 2 in group["U_CAMERA"]:
            _set_camera_crop(connect(VCAM2), key, group["OBS-MOD"].iloc[0], pbar=pbar)
            _kill_log(2)

        if 1 in group["U_CAMERA"]:
            _prep_log(1, num_frames, folder)
        if 2 in group["U_CAMERA"]:
            _prep_log(2, num_frames, folder)

        pbar2 = tqdm.tqdm(
            group.sort_values("U_DETMOD", ascending=False).groupby("U_DETMOD"),
            desc="Det. mode",
            leave=False,
        )
        for key2, group2 in pbar2:
            if 1 in group2["U_CAMERA"].values:
                _set_readout_mode(1, key2, pbar=pbar)

            if 2 in group2["U_CAMERA"].values:
                _set_readout_mode(2, key2, pbar=pbar)
            pbar3 = tqdm.tqdm(group2.iterrows(), total=len(group2), desc="Exp. time", leave=False)
            for _, row in pbar3:
                if row["U_CAMERA"] == 1:
                    camera = connect(VCAM1)
                elif row["U_CAMERA"] == 2:
                    camera = connect(VCAM2)
                camera.set_keyword("DATA-TYP", "DARK")
                camera.set_tint(row["EXPTIME"])
                time.sleep(_DEFAULT_DELAY)
                _run_log(row["U_CAMERA"])
                click.confirm("Confirm when cube is done", default=True, abort=True)
                # tint = row["EXPTIME"] * num_frames + _DEFAULT_DELAY  # s
                # time.sleep(tint)


@click.command("vampires_auto_darks")
@click.argument("folder", type=Path, default=_default_sc5_archive_folder())
@click.option("-o", "--outdir", type=Path, default=_default_sc5_archive_folder(), prompt=True)
@click.option("-n", "--num-frames", default=250, type=int, help="Number of frames per dark.")
@click.option("-y", "--no-confirm", is_flag=True, help="Skip confirmation prompts.")
def main(folder: Path, outdir: Path, num_frames: int, no_confirm: bool):
    if os.getenv("WHICHCOMP", "") != "5":
        msg = "This script must be run from sc5 in the `vampires_control` conda env"
        raise WrongComputerError(msg)
    table = vampires_dark_table(folder)
    pprint.pprint(table)
    est_tint = _estimate_total_time(table, num_frames)
    click.echo(f"Est. time for all darks with {num_frames} frames each is {est_tint/60:.01f} min.")
    if not no_confirm:
        click.confirm("Confirm to proceed", default=True, abort=True)
    try:
        process_dark_frames(table, outdir, num_frames)
    except Exception:
        _kill_log(1)
        _kill_log(2)


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
