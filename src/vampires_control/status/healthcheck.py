import multiprocessing as mp

import click
from device_control.pyro_keys import VAMPIRES
from swmain.network.pyroclient import connect

from vampires_control.helpers import Palette, color_to_rgb


def check_device(devname):
    try:
        dev = connect(devname)
        if devname.upper() in ("VCAM1", "VCAM2", "VPUPCAM"):
            dev.get_temperature()
        else:
            dev.get_status()
    except Exception:
        click.secho(
            f" ! {devname}: FAILED to retrieve status",
            bg=color_to_rgb(Palette.red),
            fg=color_to_rgb(Palette.white),
            bold=True,
        )
        return False
    click.echo(f" - {devname}: SUCCEEDED")
    return True


DEVICES = [
    VAMPIRES.BS,
    VAMPIRES.CAMFCS,
    VAMPIRES.DIFF,
    VAMPIRES.FIELDSTOP,
    VAMPIRES.FILT,
    VAMPIRES.FLC,
    VAMPIRES.FOCUS,
    VAMPIRES.MASK,
    VAMPIRES.MBI,
    VAMPIRES.PUPIL,
    VAMPIRES.QWP1,
    VAMPIRES.QWP2,
    VAMPIRES.TC,
    VAMPIRES.TRIG,
    "VCAM1",
    "VCAM2",
    "VPUPCAM",
]


@click.command("vampires_healthcheck")
def main():
    click.echo("Checking VAMPIRES devices are connected")
    with mp.Pool() as pool:
        statuses = list(pool.map(check_device, DEVICES))

        result = all(statuses)

    if result:
        click.secho(
            f"{'Healthcheck SUCCEEDED':^28}",
            bg=color_to_rgb(Palette.green),
            fg=color_to_rgb(Palette.white),
        )
    else:
        click.secho(
            f"{'!!! Healthcheck FAILED !!!':^28}",
            bg=color_to_rgb(Palette.red),
            fg=color_to_rgb(Palette.white),
            bold=True,
        )

    return result


if __name__ == "__main__":
    main()
