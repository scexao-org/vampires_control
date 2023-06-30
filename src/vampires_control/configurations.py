import multiprocessing as mp

import click

from device_control.pyro_keys import VAMPIRES
from swmain.network.pyroclient import connect


@click.command("prep_sdi", help="Prepare VAMPIRES for SDI imaging")
@click.option(
    "-bs",
    "--beamsplitter",
    default="NPBS",
    type=click.Choice(["PBS", "NPBS"], case_sensitive=False),
    prompt=True,
)
def prep_sdi(beamsplitter: str = "NPBS"):
    with mp.Pool() as pool:
        pool.apply_async(move_fcs, args=("SDI",))
        pool.apply_async(move_camfcs, args=("dual",))
        pool.apply_async(move_bs, args=(beamsplitter,))
        pool.apply_async(move_filter, args=("Open",))
        # wait for previous results to complete
        pool.close()
        pool.join()


@click.command("prep_pdi", help="Prepare VAMPIRES for PDI imaging")
@click.option("-f/-nf", "--flc/--no-flc", default=False, prompt=True)
def prep_pdi(flc: bool):
    with mp.Pool() as pool:
        pool.apply_async(move_fcs, args=("standard",))
        pool.apply_async(move_camfcs, args=("dual",))
        pool.apply_async(move_diffwheel, args=(1,))
        if flc:
            pool.apply_async(move_flc, args=("IN",))
        else:
            pool.apply_async(move_flc, args=("OUT",))
        pool.apply_async(move_bs, args=("PBS",))
        # wait for previous results to complete
        pool.close()
        pool.join()


@click.command("prep_nominal", help="Return VAMPIRES to nominal bench status")
def nominal():
    with mp.Pool() as pool:
        pool.apply_async(move_fcs, args=("standard",))
        pool.apply_async(move_camfcs, args=("dual",))
        pool.apply_async(move_diffwheel, args=(1,))
        pool.apply_async(move_flc, args=("OUT",))
        pool.apply_async(move_bs, args=("NPBS",))
        # wait for previous results to complete
        pool.close()
        pool.join()


def move_fcs(pos):
    fcs = connect(VAMPIRES.FOCUS)
    click.echo(f"Moving focus to {pos}")
    fcs.move_configuration_name(pos)


def move_camfcs(pos):
    camfcs = connect(VAMPIRES.CAMFCS)
    click.echo(f"Moving camera focus to {pos}")
    camfcs.move_configuration_name(pos)


def move_diffwheel(idx):
    diffwheel = connect(VAMPIRES.DIFF)
    click.echo(f"Moving differential filter to {idx}")
    diffwheel.move_configuration_idx(idx)


def move_flc(pos):
    flc_stage = connect(VAMPIRES.FLC)
    word = "Inserting" if pos == "IN" else "Removing"
    click.echo(f"{word} AFLC")
    flc_stage.move_configuration_name(pos)


def move_bs(bsname):
    bs = connect(VAMPIRES.BS)
    click.echo(f"Moving beamsplitter to {bsname}")
    bs.move_configuration_name(bsname)


def move_filter(filtname):
    filt = connect(VAMPIRES.FILT)
    click.echo(f"Moving filter to {filtname}")
    filt.move_configuration_name(filtname)
