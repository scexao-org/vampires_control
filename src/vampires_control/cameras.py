import click

from swmain.network.pyroclient import connect


def connect_cameras():
    vcam1 = connect("VCAM1")
    vcam2 = connect("VCAM2")
    return vcam1, vcam2


@click.command("get_tint")
def get_tint():
    tints = [cam.get_tint() for cam in connect_cameras()]
    click.echo(f"Cam 1: {tints[0]:6.03f}, Cam 2: {tints[1]:6.03f}")


@click.command("set_tint")
@click.argument("tint", type=float)
def set_tint(tint: float):
    for cam in connect_cameras():
        cam.set_tint__oneway(tint)


@click.command("set_external_trigger")
@click.option("--enable/--disable", is_flag=True)
def set_external_trigger(enable: bool):
    for cam in connect_cameras():
        cam.set_external_trigger__oneway(enable)


@click.command("set_readout_mode")
@click.argument("mode", type=click.Choice(["FAST", "SLOW"], case_sensitive=False))
def set_readout_mode(mode: str):
    for cam in connect_cameras():
        cam.set_readout_mode__oneway(mode)


@click.argument(
    "mode", type=click.Choice(["STANDARD", "MBI", "MBI_REDUCED"], case_sensitive=False)
)
def set_camera_mode(mode: str):
    for cam in connect_cameras():
        cam.set_camera_mode__oneway(mode)
