import multiprocessing as mp
import os
import pprint
import time
from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path
from typing import Literal

import click
import pandas as pd
import tqdm.auto as tqdm
from astropy.io import fits
from scxconf.pyrokeys import VCAM1, VCAM2
from swmain.network.pyroclient import connect

from vampires_control.acquisition.manager import VCAMLogManager

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


def _estimate_total_time(headers):
    headers["TINT"] = headers["EXPTIME"] * headers["nframes"]
    groups = headers.groupby("U_CAMERA")
    tints = headers["TINT"].sum() + len(groups) * _DEFAULT_DELAY
    return tints.max()


BASE_COMMAND = ("milk-streamFITSlog", "-cset", "q_asl")


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


def process_one_camera(table, cam_num: Literal[1, 2], num_frames=1000, folder=None):
    camera = connect(VCAM1) if cam_num == 1 else connect(VCAM2)
    manager = VCAMLogManager.create(cam_num, num_frames=num_frames, num_cubes=1, folder=folder)
    time.sleep(1)
    table["crop"] = table.apply(
        lambda r: (r["PRD-MIN1"], r["PRD-MIN2"], r["PRD-RNG1"], r["PRD-RNG2"]), axis=1
    )

    pbar = tqdm.tqdm(table.groupby("crop"), desc="Crop")

    for key, group in pbar:
        manager.fps.run_stop()
        manager.fps.conf_stop()
        _set_camera_crop(camera, key, group["OBS-MOD"].iloc[0], pbar=pbar)

        pbar2 = tqdm.tqdm(
            group.sort_values("U_DETMOD", ascending=False).groupby("U_DETMOD"),
            desc="Det. mode",
            leave=False,
        )
        for key2, group2 in pbar2:
            _set_readout_mode(cam_num, key2, pbar=pbar)
            pbar3 = tqdm.tqdm(group2.iterrows(), total=len(group2), desc="Exp. time", leave=False)
            for _, row in pbar3:
                camera.set_keyword("DATA-TYP", "DARK")
                camera.set_tint(row["EXPTIME"])
                manager.fps.conf_start(5.0)
                manager.fps.set_param("cubesize", row["nframes"])
                manager.fps.run_start(100.0)
                assert manager.fps.run_isrunning()
                manager.acquire_cubes(1)


def process_dark_frames(table, folder):
    kwargs = dict(folder=folder)
    groups = table.groupby("U_CAMERA")
    with mp.Pool(2) as pool:
        jobs = []
        for key, group in groups:
            job = pool.apply_async(process_one_camera, args=(group, key), kwds=kwargs)
            jobs.append(job)
        for job in jobs:
            job.get()


@click.command("vampires_autodarks")
@click.argument("folder", type=Path, default=_default_sc5_archive_folder())
@click.option("-o", "--outdir", type=Path)
@click.option("-n", "--num-frames", default=250, type=int, help="Number of frames per dark.")
@click.option("-y", "--no-confirm", is_flag=True, help="Skip confirmation prompts.")
def main(folder: Path, outdir: Path, num_frames: int, no_confirm: bool):
    if outdir is None:
        outdir = folder
    click.echo(f"Saving data to {outdir.absolute()}")
    if os.getenv("WHICHCOMP", "") != "5":
        msg = "This script must be run from sc5 in the `vampires_control` conda env"
        raise WrongComputerError(msg)
    table = vampires_dark_table(folder)
    table["nframes"] = num_frames
    mask_med = (table["EXPTIME"] > 0.5) & (table["EXPTIME"] < 5)
    table[mask_med]["nframes"] = 500
    mask_long = table["EXPTIME"] >= 5
    table[mask_long]["nframes"] = 100
    pprint.pprint(table)
    est_tint = _estimate_total_time(table)
    click.echo(f"Est. time for all darks with {num_frames} frames each is {est_tint/60:.01f} min.")
    process_dark_frames(table, outdir)
