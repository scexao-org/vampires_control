import subprocess
import time

import click
from scxconf.pyrokeys import VAMPIRES, VCAM1, VCAM2
from swmain.network.pyroclient import connect

from vampires_control.acquisition.acquire import start_acquisition


@click.command("take_flats")
@click.option("-n", "--nframes", default=100, type=int, prompt="Specify number of frames per cube")
@click.option(
    "-z", "--ncubes", type=int, default=1, prompt="Specify number of cubes (-1 for infinite)"
)
@click.option("-c", "--cam", default=-1, type=int, prompt="Specify camera, if -1 uses both")
@click.option("-a/-na", "--archive/--no-archive", default=True, prompt="Archive data to Gen2")
def take_flats(nframes=100, ncubes=1, exptime=0.1, archive=True, cam=-1):
    cam1 = connect(VCAM1)
    cam2 = connect(VCAM2)
    cam1.set_tint(exptime)
    cam2.set_tint(exptime)

    start_acquisition(
        nframes=nframes, ncubes=ncubes, data_type="FLAT", cam=cam, archive=archive, start=True
    )


@click.command("take_pinholes")
@click.option("-n", "--nframes", default=100, type=int, prompt="Specify number of frames per cube")
@click.option(
    "-z", "--ncubes", type=int, default=1, prompt="Specify number of cubes (-1 for infinite)"
)
@click.option("-c", "--cam", default=-1, type=int, prompt="Specify camera, if -1 uses both")
@click.option("-a/-na", "--archive/--no-archive", default=True, prompt="Archive data to Gen2")
def take_pinholes(nframes=100, ncubes=1, exptime=0.1, archive=True, cam=-1):
    cam1 = connect(VCAM1)
    cam2 = connect(VCAM2)
    cam1.set_tint(exptime)
    cam2.set_tint(exptime)

    start_acquisition(
        nframes=nframes, ncubes=ncubes, data_type="COMPARISON", cam=cam, archive=archive, start=True
    )


@click.command("take_darks")
@click.option("-n", "--nframes", default=100, type=int, prompt="Specify number of frames per cube")
@click.option(
    "-z", "--ncubes", type=int, default=1, prompt="Specify number of cubes (-1 for infinite)"
)
@click.option("-c", "--cam", default=-1, type=int, prompt="Specify camera, if -1 uses both")
@click.option("-a/-na", "--archive/--no-archive", default=True, prompt="Archive data to Gen2")
def take_darks(nframes=100, ncubes=1, exptime=0.1, archive=True, cam=-1):
    cam1 = connect(VCAM1)
    cam2 = connect(VCAM2)
    cam1.set_tint(exptime)
    cam2.set_tint(exptime)

    start_acquisition(
        nframes=nframes, ncubes=ncubes, data_type="DARK", cam=cam, archive=archive, start=True
    )


@click.command("take_cals")
@click.option("-e", "--exptime", default=0.1, type=float, prompt="Specify exposure time")
@click.option("-n", "--nframes", default=100, type=int, prompt="Specify number of frames per cube")
@click.option(
    "-z", "--ncubes", type=int, default=1, prompt="Specify number of cubes (-1 for infinite)"
)
@click.option("-c", "--cam", default=-1, type=int, prompt="Specify camera, if -1 uses both")
@click.option("-a/-na", "--archive/--no-archive", default=True, prompt="Archive data to Gen2")
def main(exptime, nframes, ncubes, cam, archive):
    # step 1: take pinholes
    delta_time = nframes * ncubes * exptime  # s
    if click.confirm("Would you like to take pinholes?", default=True):
        click.echo(f"Beginning to take pinholes, should take ~{delta_time:.0f}s")
        take_pinholes.callback(
            nframes=nframes, ncubes=ncubes, exptime=exptime, cam=cam, archive=archive
        )
        time.sleep(delta_time)

    if click.confirm("Would you like to move pinholes out?", default=True):
        subprocess.run(["ssh", "sc2", "src_fib", "out"], capture_output=True)

    if click.confirm("Would you like to take flats?", default=True):
        click.echo(f"Beginning to take flats, should take ~{delta_time:.0f}s")
        take_flats.callback(
            nframes=nframes, ncubes=ncubes, exptime=exptime, cam=cam, archive=archive
        )
        time.sleep(delta_time)

    if click.confirm("Would you like to take darks?", default=True):
        move_diff = click.confirm("Would you like to block using diff wheel?", default=True)
        if move_diff:
            diff = connect(VAMPIRES.DIFF)
            prior_diff_position = diff.get_position()
            diff.move_relative(31)
        click.echo(f"Beginning to take darks, should take ~{delta_time:.0f}s")
        take_darks.callback(
            nframes=nframes, ncubes=ncubes, exptime=exptime, cam=cam, archive=archive
        )
        time.sleep(delta_time)
        if move_diff:
            diff.move_absolute(prior_diff_position)
