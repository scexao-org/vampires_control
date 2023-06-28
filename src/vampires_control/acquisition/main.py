from functools import partial

import click
from trogon import Trogon

from vampires_control.acquisition.blocked_acquisition import blocked_acquire_cubes
from vampires_control.acquisition.free_acquisition import acquire_cubes
from vampires_control.cameras import connect_cameras

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


def handle_metadata():
    pass


def open_tui(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    didx = None
    # remove --tui from context
    for i, par in enumerate(ctx.command.params):
        if par.name == "tui":
            didx = i
    if didx is not None:
        del ctx.command.params[didx]
    Trogon(ctx.command, app_name=ctx.info_name, click_context=ctx).run()
    ctx.exit()


@click.option(
    "--tui",
    help="Launch TUI.",
    is_flag=True,
    callback=open_tui,
    expose_value=False,
    is_eager=True,
)
@click.argument("num_frames", type=int, required=False)
@click.option(
    "--data-type",
    "-T",
    default="OBJECT",
    type=click.Choice(DATA_TYPES, case_sensitive=False),
    help="Data type",
)
@click.option("--archive", "-a", is_flag=True, default=False, help="Archive to Gen2")
@click.option(
    "--num-cubes",
    "-N",
    default=-1,
    help="Number of cubes to acquire. If less than 1 will acquire indefinitely.",
)
@click.option(
    "--pdi",
    "-P",
    is_flag=True,
    default=False,
    help="Enable PDI mode for synchronizing with the SCExAO HWP daemon.",
)
@click.option(
    "--sdi",
    "-S",
    type=(click.Choice(["Halpha", "SII"], case_sensitive=False), int),
    help="Enable SDI mode with given filter and number of cubes per filter state.",
)
@click.command()
def main(
    num_frames, num_cubes=-1, data_type="OBJECT", archive=False, pdi=False, sdi=None
):
    # determine whether using blocked triggering or free-running
    # The blocked mode is used whenever doing PDI or SDI to ensure
    # synchronization with devices (like the HWP or diff wheel)
    if pdi or sdi is not None:
        acquisition_func = partial(
            blocked_acquire_cubes,
            pdi=pdi,
            sdi_mode=sdi[0],
            sdi_num_per=sdi[1],
        )
    else:
        acquisition_func = acquire_cubes

    for cam in connect_cameras():
        if cam is not None:
            cam.set_keyword("DATA-TYP", data_type)
    if num_cubes > 0:
        acquisition_func(num_frames, num_cubes)
    else:
        acquisition_func(num_frames, None)


if __name__ == "__main__":
    main()
