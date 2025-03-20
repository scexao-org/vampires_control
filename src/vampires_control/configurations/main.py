import asyncio

import click

from .configurations import Configuration

CONFIGS = {
    "nominal": Configuration(
        name="nominal", diff=1, bs="PBS", mbi="Mirror", puplens="OUT", fcs="Dual", mask=8
    ),
    "SDI": Configuration(name="SDI", bs="PBS", mbi="Mirror", puplens="OUT", fcs="SDI"),
    "VPL": Configuration(name="VPL", bs="PBS", fcs="VPL"),
    "LAPD": Configuration(
        name="LAPD",
        diff=1,
        bs="PBS",
        mbi="Mirror",
        puplens="OUT",
        cam_defocus=3.0,
        fcs="Dual",
        mask=8,
    ),
    "NRM": Configuration(name="NRM", diff=1, bs="Open", mbi="Dichroics", fcs="Dual", mask="SAM-18"),
}


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
    conf = CONFIGS["SDI"]
    conf.diff = filt
    conf.bs = beamsplitter
    asyncio.run(conf.move_async())


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
    conf = CONFIGS["PDI"]
    conf.flc = "IN" if flc else "OUT"
    conf.mbi = mbi
    asyncio.run(conf.move_async())


@click.command("nominal", help="Nominal bench status")
def prep_nominal():
    conf = CONFIGS["nominal"]
    asyncio.run(conf.move_async())


@click.command("parked", help="Parked bench status")
def prep_parked():
    conf = CONFIGS["parked"]
    asyncio.run(conf.move_async())


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
@click.option("-d", "--defocus", type=float, default=3.0, prompt="Camera defocus, in mm")
def prep_lapd(defocus, beamsplitter, mbi):
    conf = CONFIGS["LAPD"]
    conf.cam_defocus = defocus
    conf.bs = beamsplitter
    conf.mbi = mbi
    asyncio.run(conf.move_async())


@click.command("vpl", help="Defocus cam 1 for phase diversity")
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
    conf = CONFIGS["VPL"]
    conf.bs = beamsplitter
    conf.mbi = mbi
    asyncio.run(conf.move_async())


@click.command("nrm", help="NRM + MBI")
@click.option(
    "-bs",
    "--beamsplitter",
    default="Open",
    type=click.Choice(["PBS", "Open"], case_sensitive=False),
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
    "-h",
    "--holes",
    metavar="<holes>",
    default="7",
    type=click.Choice(["7", "9", "18"]),
    prompt=True,
)
def prep_nrm_mbi(beamsplitter: str, mbi: str, holes: int):
    conf = CONFIGS["NRM"]
    conf.bs = beamsplitter
    conf.mbi = mbi
    conf.mask = f"SAM-{holes}"
    if "PBS" not in beamsplitter:
        conf.fcs = "Single"
    else:
        conf.fcs = "Dual"
    print(conf)
    asyncio.run(conf.move_async())


SUBCOMMANDS = {
    "parked": prep_parked,
    "nominal": prep_nominal,
    "PDI": prep_pdi,
    "SDI": prep_sdi,
    "VPL": prep_vpl,
    "LAPD": prep_lapd,
    "NRM": prep_nrm_mbi,
}


@click.group("vampires_prep", invoke_without_command=True)
@click.pass_context
def main(ctx):
    # no configuration passed, choose from list
    if ctx.invoked_subcommand is None:
        sub = click.prompt(
            "Choose configuration", type=click.Choice(SUBCOMMANDS.keys(), case_sensitive=False)
        )
        ctx.invoke(SUBCOMMANDS[sub])


for subcommand in SUBCOMMANDS.values():
    main.add_command(subcommand)

if __name__ == "__main__":
    main()
