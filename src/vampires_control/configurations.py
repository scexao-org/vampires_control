import multiprocessing as mp

import click

from device_control.pyro_keys import VAMPIRES
from swmain.network.pyroclient import connect
from vampires_control.helpers import Palette, color_to_rgb


@click.command("sdi", help="Narrowband spectral differential imaging")
@click.option(
    "-f",
    "--filter",
    "filt",
    default="Halpha",
    type=click.Choice(["Halpha", "SII"], case_sensitive=False),
    prompt=True,
)
@click.option(
    "-bs",
    "--beamsplitter",
    default="NPBS",
    type=click.Choice(["PBS", "NPBS"], case_sensitive=False),
    prompt=True,
)
def prep_sdi(filt: str = "Halpha", beamsplitter: str = "NPBS"):
    mbi_nudge = 0
    if beamsplitter == "NPBS":
        mbi_nudge = 0.0653
    with mp.Pool() as pool:
        pool.apply_async(move_diffwheel, args=(filt,))
        pool.apply_async(move_fcs, args=("SDI",))
        pool.apply_async(move_camfcs, args=("dual",))
        pool.apply_async(move_filter, args=("Open",))
        pool.apply_async(move_puplens, args=("OUT",))
        pool.apply_async(move_bs, args=(beamsplitter,))
        pool.apply_async(move_mbi, args=("Mirror", mbi_nudge))
        # wait for previous results to complete
        pool.close()
        pool.join()
    click.secho(
        " Finished! ",
        bg=color_to_rgb(Palette.green),
        fg=color_to_rgb(Palette.white),
    )


@click.command("pdi", help="Polarimetric differential imaging")
@click.option("-f/-nf", "--flc/--no-flc", default=False, prompt=True)
@click.option(
    "-m",
    "--mbi",
    default="Mirror",
    type=click.Choice(["Mirror", "Dichroics"], case_sensitive=False),
    prompt="MBI",
)
def prep_pdi(flc: bool, mbi):
    with mp.Pool() as pool:
        pool.apply_async(move_fcs, args=("standard",))
        pool.apply_async(move_camfcs, args=("dual",))
        pool.apply_async(move_diffwheel, args=(1,))
        if flc:
            pool.apply_async(move_flc, args=("IN",))
        else:
            pool.apply_async(move_flc, args=("OUT",))
        pool.apply_async(move_puplens, args=("OUT",))
        pool.apply_async(move_bs, args=("PBS",))
        pool.apply_async(move_mbi, args=(mbi,))
        # wait for previous results to complete
        pool.close()
        pool.join()

    click.secho(
        " Finished! ",
        bg=color_to_rgb(Palette.green),
        fg=color_to_rgb(Palette.white),
    )


@click.command("nominal", help="Nominal bench status")
@click.option(
    "-bs",
    "--beamsplitter",
    default="PBS",
    type=click.Choice(["PBS", "NPBS"], case_sensitive=False),
    prompt=True,
)
@click.option(
    "-m",
    "--mbi",
    default="Mirror",
    type=click.Choice(["Mirror", "Dichroics"], case_sensitive=False),
    prompt="MBI",
)
def prep_nominal(beamsplitter, mbi):
    mbi_nudge = 0
    if beamsplitter == "NPBS":
        mbi_nudge = 0.0653
    with mp.Pool() as pool:
        pool.apply_async(move_fcs, args=("standard",))
        pool.apply_async(move_camfcs, args=("dual",))
        pool.apply_async(move_diffwheel, args=(1,))
        pool.apply_async(move_flc, args=("OUT",))
        pool.apply_async(move_puplens, args=("OUT",))
        pool.apply_async(move_bs, args=(beamsplitter,))
        pool.apply_async(move_mbi, args=(mbi, mbi_nudge))
        # wait for previous results to complete
        pool.close()
        pool.join()
    click.secho(
        " Finished! ",
        bg=color_to_rgb(Palette.green),
        fg=color_to_rgb(Palette.white),
    )


@click.command("lapd", help="Defocus cam 1 for phase diversity")
@click.option(
    "-bs",
    "--beamsplitter",
    default="PBS",
    type=click.Choice(["PBS", "NPBS"], case_sensitive=False),
    prompt=True,
)
@click.option(
    "-m",
    "--mbi",
    default="Mirror",
    type=click.Choice(["Mirror", "Dichroics"], case_sensitive=False),
    prompt=True,
)
@click.option(
    "-d", "--defocus", type=float, default=3.0, prompt="Camera defocus, in mm"
)
def prep_lapd(defocus, beamsplitter, mbi):
    mbi_nudge = 0
    if beamsplitter == "NPBS":
        mbi_nudge = 0.0653
    with mp.Pool() as pool:
        pool.apply_async(move_fcs, args=("standard",))
        pool.apply_async(move_camfcs, args=("dual", defocus))
        pool.apply_async(move_diffwheel, args=(1,))
        pool.apply_async(move_flc, args=("OUT",))
        pool.apply_async(move_puplens, args=("OUT",))
        pool.apply_async(move_bs, args=(beamsplitter,))
        pool.apply_async(move_mbi, args=(mbi, mbi_nudge))
        # wait for previous results to complete
        pool.close()
        pool.join()
        click.secho(
            " Finished! ",
            bg=color_to_rgb(Palette.green),
            fg=color_to_rgb(Palette.white),
        )


@click.command("vpl", help="Defocus for visible photonic lantern pickoff")
@click.option(
    "-bs",
    "--beamsplitter",
    default="PBS",
    type=click.Choice(["PBS", "NPBS"], case_sensitive=False),
    prompt=True,
)
@click.option(
    "-m",
    "--mbi",
    default="Mirror",
    type=click.Choice(["Mirror", "Dichroics"], case_sensitive=False),
    prompt=True,
)
def prep_vpl(beamsplitter, mbi):
    mbi_nudge = 0
    if beamsplitter == "NPBS":
        mbi_nudge = 0.0653
    with mp.Pool() as pool:
        pool.apply_async(move_fcs, args=("vpl",))
        pool.apply_async(move_camfcs, args=("vpl",))
        pool.apply_async(move_diffwheel, args=(1,))
        pool.apply_async(move_flc, args=("OUT",))
        pool.apply_async(move_puplens, args=("OUT",))
        pool.apply_async(move_bs, args=(beamsplitter,))
        pool.apply_async(move_mbi, args=(mbi, mbi_nudge))
        # wait for previous results to complete
        pool.close()
        pool.join()
        click.secho(
            " Finished! ",
            bg=color_to_rgb(Palette.green),
            fg=color_to_rgb(Palette.white),
        )


def move_fcs(pos):
    fcs = connect(VAMPIRES.FOCUS)
    click.echo(f" - Moving focus to {pos}")
    fcs.move_configuration_name(pos)


def move_puplens(pos):
    pupil_lens = connect(VAMPIRES.PUPIL)
    word = "Inserting" if pos.upper() == "IN" else "Removing"
    click.echo(f" - {word} pupil lens")
    pupil_lens.move_configuration_name(pos)


def move_camfcs(pos, defocus=0):
    camfcs = connect(VAMPIRES.CAMFCS)
    click.echo(f" - Moving camera focus to {pos} with {defocus} mm offset")
    camfcs.move_configuration_name(pos)
    if defocus != 0:
        camfcs.move_relative(defocus)


def move_diffwheel(idx):
    diffwheel = connect(VAMPIRES.DIFF)
    click.echo(f" - Moving differential filter to {idx}")
    diffwheel.move_configuration_idx(idx)


def move_flc(pos):
    flc_stage = connect(VAMPIRES.FLC)
    word = "Inserting" if pos.upper() == "IN" else "Removing"
    click.echo(f" - {word} AFLC")
    flc_stage.move_configuration_name(pos)


def move_bs(bsname):
    bs = connect(VAMPIRES.BS)
    click.echo(f" - Moving beamsplitter to {bsname}")
    bs.move_configuration_name(bsname)


def move_filter(filtname):
    filt = connect(VAMPIRES.FILT)
    click.echo(f" - Moving filter to {filtname}")
    filt.move_configuration_name(filtname)


def move_mbi(mbiconf, theta=0):
    mbi = connect(VAMPIRES.MBI)
    click.echo(f" - Moving MBI wheel to {mbiconf} with {theta} deg offset")
    mbi.move_configuration_name(mbiconf)
    mbi.move_relative(theta)


## TODO dataclass and TOML-ify these things

SUBCOMMANDS = {
    "nominal": prep_nominal,
    "PDI": prep_pdi,
    "SDI": prep_sdi,
    "VPL": prep_vpl,
    "LAPD": prep_lapd,
}


@click.group("vampires_prep", invoke_without_command=True)
@click.pass_context
def main(ctx):
    # no configuration passed, choose from list
    if ctx.invoked_subcommand is None:
        sub = click.prompt(
            "Choose configuration",
            type=click.Choice(SUBCOMMANDS.keys(), case_sensitive=False),
        )
        ctx.invoke(SUBCOMMANDS[sub])


for subcommand in SUBCOMMANDS.values():
    main.add_command(subcommand)

if __name__ == "__main__":
    main()
