from __future__ import annotations

import asyncio
from pathlib import Path

import click
import tomli
import tomli_w
from pydantic import BaseModel
from scxconf.pyrokeys import VAMPIRES
from swmain.network.pyroclient import connect

from vampires_control.helpers import Palette, color_to_rgb


class Configuration(BaseModel):
    name: str
    filter: str | int | None = None
    diff: str | int | None = None
    bs: str | int | None = None
    camfcs: str | int | None = None
    cam_defocus: float = 0
    fcs: str | int | None = None
    puplens: str | int | None = None
    mbi: str | int | None = None
    mask: str | int | None = None
    flc: str | int | None = None
    fieldstop: str | int | None = None

    @property
    def mbi_nudge(self) -> float:
        if self.bs and self.bs == "NPBS":
            return 0.0653
        else:
            return 0.0

    @classmethod
    def from_file(cls, filename):
        with Path(filename).open("rb") as fh:
            config = tomli.load(fh)
        return cls.model_validate(config)

    def to_toml(self) -> str:
        # get serializable output using pydantic
        model_dict = self.model_dump(exclude_none=True, mode="json", round_trip=True)
        return tomli_w.dumps(model_dict)

    def save(self, filename) -> None:
        """
        Save configuration settings to TOML file

        Parameters
        ----------
        filename
            Output filename
        """
        # get serializable output using pydantic
        model_dict = self.model_dump(exclude_none=True, mode="json", round_trip=True)
        # save output TOML
        with Path(filename).open("wb") as fh:
            tomli_w.dump(model_dict, fh)

    async def move_async(self) -> None:
        promises = []
        if self.filter:
            promises += [move_filter_async(self.filter)]
        if self.diff:
            promises += [move_diffwheel_async(self.diff)]
        if self.bs:
            promises += [move_bs_async(self.bs)]
        if self.camfcs:
            promises += [move_camfcs_async(self.camfcs, self.cam_defocus)]
        if self.fcs:
            promises += [move_fcs_async(self.fcs)]
        if self.puplens:
            promises += [move_puplens_async(self.puplens)]
        if self.mbi:
            promises += [move_mbi_async(self.mbi, self.mbi_nudge)]
        if self.mask:
            promises += [move_mask_async(self.mask)]
        if self.flc:
            promises += [move_flc_async(self.flc)]
        if self.fieldstop:
            promises += [move_fieldstop_async(self.fieldstop)]

        asyncio.gather(*promises)

        click.secho(" Finished! ", bg=color_to_rgb(Palette.green), fg=color_to_rgb(Palette.white))


async def move_fcs_async(conf):
    fcs = connect(VAMPIRES.FOCUS)
    click.echo(f" - Moving focus to {conf}")
    fcs.move_configuration(conf)


async def move_puplens_async(pos):
    pupil_lens = connect(VAMPIRES.PUPIL)
    word = "Inserting" if pos.upper() == "IN" else "Removing"
    click.echo(f" - {word} pupil lens")
    pupil_lens.move_configuration_name(pos)


async def move_camfcs_async(pos, defocus=0):
    camfcs = connect(VAMPIRES.CAMFCS)
    click.echo(f" - Moving camera focus to {pos} with {defocus} mm offset")
    camfcs.move_configuration_name(pos)
    if defocus != 0:
        camfcs.move_relative(defocus)


async def move_diffwheel_async(filtname):
    if isinstance(filtname, int):
        conf = filtname
    elif filtname.lower() == "open":
        conf = 1
    elif filtname.lower() == "sii":
        conf = 2
    elif filtname.lower() == "halpha":
        conf = 3
    elif filtname.lower() == "block":
        conf = 7
    else:
        conf = filtname
    diffwheel = connect(VAMPIRES.DIFF)
    click.echo(f" - Moving differential filter to {conf}")
    diffwheel.move_configuration(conf)


async def move_flc_async(pos):
    flc_stage = connect(VAMPIRES.FLC)
    word = "Inserting" if pos.upper() == "IN" else "Removing"
    click.echo(f" - {word} AFLC")
    flc_stage.move_configuration(pos)


async def move_bs_async(bsname):
    bs = connect(VAMPIRES.BS)
    click.echo(f" - Moving beamsplitter to {bsname}")
    bs.move_configuration(bsname)


async def move_filter_async(filtname):
    filt = connect(VAMPIRES.FILT)
    click.echo(f" - Moving filter to {filtname}")
    filt.move_configuration(filtname)


async def move_mbi_async(mbiconf, theta=0):
    mbi = connect(VAMPIRES.MBI)
    click.echo(f" - Moving MBI wheel to {mbiconf} with {theta} deg offset")
    mbi.move_configuration(mbiconf)
    mbi.move_relative(theta)


async def move_mask_async(conf):
    mask = connect(VAMPIRES.MASK)
    click.echo(f" - Moving pupil mask to {conf}")
    mask.move_configuration(conf)


async def move_fieldstop_async(conf):
    fieldstop = connect(VAMPIRES.FIELDSTOP)
    click.echo(f" - Moving fieldstop to {conf}")
    fieldstop.move_configuration(conf)
