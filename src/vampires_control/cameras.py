import subprocess
import time

import click

from swmain.network.pyroclient import connect

DEFAULT_DELAY = 15  # s


def connect_cameras():
    vcam1 = connect("VCAM1")
    vcam2 = connect("VCAM2")
    return vcam1, vcam2


@click.command("get_tint", help="Print each camera's detector integration time.")
def get_tint():
    tints = [cam.get_tint() for cam in connect_cameras()]
    click.echo(
        f"Cam 1: {tints[0]:6.03f} s / {int(tints[0] * 1e6):d} us, Cam 2: {tints[1]:6.03f} s / {int(tints[1] * 1e6):d} us"
    )


@click.command("get_fps", help="Print each camera's framerate.")
def get_fps():
    frates = [cam.get_fps() for cam in connect_cameras()]
    click.echo(f"Cam 1: {frates[0]:6.02f} Hz, Cam 2: {frates[1]:6.02f} Hz")


@click.command("set_tint", help="Set both cameras' detector integration time")
@click.argument("tint", type=float)
def set_tint(tint):
    for cam in connect_cameras():
        cam.set_tint__oneway(tint)


@click.command(
    "set_trigger", help="Control the external trigger mode for both cameras."
)
@click.argument(
    "enable", type=click.Choice(["enable", "disable"], case_sensitive=False)
)
def set_trigger(enable: bool):
    for cam in connect_cameras():
        cam.set_external_trigger__oneway(enable)


@click.command("set_readout_mode", help="Set both cameras' readout modes.")
@click.argument("mode", type=click.Choice(["FAST", "SLOW"], case_sensitive=False))
def set_readout_mode(mode: str):
    for cam in connect_cameras():
        cam.set_readout_mode__oneway(mode)


@click.command("set_mode", help="Set both cameras' crop modes.")
@click.argument(
    "mode",
    type=click.Choice(["STANDARD", "MBI", "MBI_REDUCED", "FULL"], case_sensitive=False),
)
def set_mode(mode: str):
    for cam in connect_cameras():
        cam.set_camera_mode__oneway(mode)
        time.sleep(DEFAULT_DELAY)


@click.command("start_cameras")
@click.argument("mode", default="STANDARD")
@click.option(
    "-c", "--cam", type=int, required=False, help="Start a single camera by number"
)
def start_cameras(mode, cam=None):
    if cam is None:
        subprocess.run(["ssh", "sc5", "cam-vcamstart"], shell=True)
    elif cam == 1:
        subprocess.run(["ssh", "sc5", "cam-vcam1start"], shell=True)
    elif cam == 2:
        subprocess.run(["ssh", "sc5", "cam-vcam2start"], shell=True)
