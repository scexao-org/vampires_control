import click
import numpy as np
from pyMilk.interfacing.isio_shmlib import SHM
from swmain.network.pyroclient import connect


def connect_cameras():
    vcam1 = connect("VCAM1")
    vcam2 = connect("VCAM2")
    return vcam1, vcam2


def connect_shms():
    return SHM("vcam1"), SHM("vcam2")


@click.command("get_tint", help="Print each camera's detector integration time.")
def get_tint():
    tints = [cam.get_tint() for cam in connect_cameras()]
    click.echo(
        f"Cam 1: {tints[0]:6.03f} s / {int(tints[0] * 1e6):d} us | Cam 2: {tints[1]:6.03f} s / {int(tints[1] * 1e6):d} us"
    )


@click.command("set_tint", help="Set both cameras' detector integration time")
@click.argument("tint", type=float)
def set_tint(tint):
    for cam in connect_cameras():
        cam.set_tint__oneway(tint)


@click.command("target_tint")
@click.argument("target", type=float, default=1e4)
@click.option("-s", "--sync", is_flag=True, default=True)
def target_tint(target: float, niter=5, sync=True):
    cams = connect_cameras()
    shms = connect_shms()
    tints = [cam.get_tint() for cam in cams]
    best_guess = tints
    i = 0
    while i < niter:
        tints = np.array([cam.set_tint(t) for t, cam in zip(best_guess, cams)])
        peaks = np.array([shm.get_data(check=True).max() for shm in shms])
        flux = peaks / tints
        best_guess = target / flux
        if np.any(peaks >= 65535) and np.any(tints > 8e-6):
            continue
        if sync:
            best_guess[:] = best_guess.mean()
        i += 1
    click.echo(
        f"Cam 1: {best_guess[0]:6.03f} s / {int(best_guess[0] * 1e6):d} us | Cam 2: {best_guess[1]:6.03f} s / {int(best_guess[1] * 1e6):d} us"
    )
    return best_guess


@click.command("get_fps", help="Print each camera's framerate.")
def get_fps():
    frates = [cam.get_fps() for cam in connect_cameras()]
    click.echo(f"Cam 1: {frates[0]:6.02f} Hz | Cam 2: {frates[1]:6.02f} Hz")


@click.command("set_fps", help="Set each camera's framerate.")
@click.argument("framerate", type=float)
def set_fps(framerate):
    frates = [cam.set_fps(framerate) for cam in connect_cameras()]
    click.echo(f"Cam 1: {frates[0]:6.02f} Hz | Cam 2: {frates[1]:6.02f} Hz")


@click.command("get_trigger", help="Get the external trigger mode for both cameras.")
def get_trigger():
    enab = [cam.get_external_trigger() for cam in connect_cameras()]
    click.echo(f"Cam 1: {enab[0]} | Cam 2: {enab[1]}")


@click.command("set_trigger", help="Control the external trigger mode for both cameras.")
@click.argument("enable", type=click.Choice(["enable", "disable"], case_sensitive=False))
def set_trigger(enable: bool):
    for cam in connect_cameras():
        cam.set_external_trigger__oneway(enable)


@click.command("get_readout_mode", help="Get the readout mode for both cameras.")
def get_readout_mode():
    mode = [cam.get_readout_mode() for cam in connect_cameras()]
    click.echo(f"Cam 1: {mode[0]} | Cam 2: {mode[1]}")


@click.command("set_readout_mode", help="Set both cameras' readout modes.")
@click.argument("mode", type=click.Choice(["FAST", "SLOW"], case_sensitive=False))
def set_readout_mode(mode: str):
    for cam in connect_cameras():
        cam.set_readout_mode__oneway(mode)


@click.command("get_crop", help="Set both cameras' crop modes.")
def get_crop():
    mode = [cam.get_camera_mode() for cam in connect_cameras()]
    click.echo(f"Cam 1: {mode[0]} | Cam 2: {mode[1]}")


@click.command("set_crop", help="Set both cameras' crop modes.")
@click.argument(
    "crop",
    type=click.Choice(
        [
            "STANDARD",
            "TWOARC",
            "ONEARC",
            "HALFARC",
            "NPBS",
            "MBI",
            "MBI_REDUCED",
            "MBI_ONEHALF",
            "MBI_JEWEL",
            "FULL",
            "PUPIL",
        ],
        case_sensitive=False,
    ),
)
def set_crop(crop: str):
    for cam in connect_cameras():
        cam.set_camera_mode__oneway(crop)
