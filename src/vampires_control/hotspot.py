from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Final, Iterable, Sequence

import click
import numpy as np
import pandas as pd
import tomli_w
from pydantic import BaseModel, Field, computed_field
from pyMilk.interfacing.isio_shmlib import SHM
from swmain import redis

from vampires_control import paths

from .centroid import guess_mbi_centroid, model_centroid
from .synthpsf import create_synth_psf

DEFAULT_CSV_STORE: Final[Path] = paths.DATA_DIR / "hotspots"
DEFAULT_CONFIG_STORE: Final[Path] = paths.DATA_DIR / "crops"


class HotspotInfo(BaseModel):
    timestamp: datetime = Field(default_factory=partial(datetime.now, timezone.utc))
    cam: str
    field: str
    cx: float
    cy: float
    cropx: int
    sizex: int
    cropy: int
    sizey: int

    @computed_field
    @property
    def absx(self) -> float:
        return self.cx + self.cropx

    @computed_field
    @property
    def absy(self) -> float:
        return self.cy + self.cropy

    @computed_field
    @property
    def crop_cx(self) -> float:
        return self.cropx + self.sizex / 2 - 0.5

    @computed_field
    @property
    def crop_cy(self) -> float:
        return self.cropy + self.sizey / 2 - 0.5

    @computed_field
    @property
    def delta_x(self) -> float:
        return self.absx - self.crop_cx

    @computed_field
    @property
    def delta_y(self) -> float:
        return self.absy - self.crop_cy

    @computed_field
    @property
    def separation(self) -> float:
        return np.hypot(self.delta_y, self.delta_x)

    @computed_field
    @property
    def angle(self) -> float:
        return np.rad2deg(np.arctan2(self.delta_y, self.delta_x))


def save_hotspots_to_db(hotspots: Sequence[HotspotInfo], save_dir: Path = DEFAULT_CSV_STORE):
    """Save hostpot info to persistent data store"""
    save_dir.mkdir(exist_ok=True)
    date = hotspots[0].timestamp.strftime("%Y%m%d")
    save_path = save_dir / f"{date}_{hotspots[0].cam}_hotspots.csv"
    rows = [hs.model_dump() for hs in hotspots]
    df = pd.DataFrame(rows)
    df.index = df.pop("timestamp")
    if save_path.exists():
        df.to_csv(save_path, mode="a", header=False)
    else:
        df.to_csv(save_path)


def fit_hotspots_standard(frame, shm: SHM) -> HotspotInfo:
    shm_kwds = shm.get_keywords()
    curfilt = shm_kwds["FILTER01"].strip()
    # psf = create_synth_psf(curfilt)
    ctr_guess = np.unravel_index(np.nanargmax(frame), frame.shape)
    centroid = gaussian_centroid(frame, ctr_guess)
    hotspot = HotspotInfo(
        cam=shm.FNAME,
        field=curfilt,
        cx=centroid[1],
        cy=centroid[0],
        cropx=shm_kwds["PRD-MIN1"],
        cropy=shm_kwds["PRD-MIN2"],
        sizex=shm_kwds["PRD-RNG1"],
        sizey=shm_kwds["PRD-RNG2"],
    )
    return hotspot


def fit_hotspots_mbi(frame, shm: SHM) -> dict[str, HotspotInfo]:
    shm_kwds = shm.get_keywords()
    cam = shm_kwds["U_CAMERA"]
    hotspots = {}
    for field in ("F610", "F670", "F720", "F760"):
        create_synth_psf(field)
        ctr = guess_mbi_centroid(frame, field=field, camera=cam)
        # centroid = cross_correlation_centroid(frame, psf, ctr)
        centroid = model_centroid(frame, ctr)
        hotspot = HotspotInfo(
            cam=shm.FNAME,
            field=field,
            cx=centroid[1],
            cy=centroid[0],
            cropx=shm_kwds["PRD-MIN1"],
            cropy=shm_kwds["PRD-MIN2"],
            sizex=shm_kwds["PRD-RNG1"],
            sizey=shm_kwds["PRD-RNG2"],
        )
        hotspots[field] = hotspot
    return hotspots


class CropConfig(BaseModel):
    cam: str
    origin: tuple[int, int]
    size: tuple[int, int]
    hotspots: dict[str, tuple[float, float]]

    @computed_field
    @property
    def center(self) -> tuple[float, float]:
        return tuple(np.add(self.origin, np.divide(self.size, 2) - 0.5))

    @computed_field
    @property
    def X0(self) -> int:
        return int(self.origin[1])

    @computed_field
    @property
    def X1(self) -> int:
        return int(self.origin[1] + self.size[1] - 1)

    @computed_field
    @property
    def Y0(self) -> int:
        return int(self.origin[0])

    @computed_field
    @property
    def Y1(self) -> int:
        return int(self.origin[0] + self.size[0] - 1)


def save_configs_to_db(
    config: CropConfig, config_reduced: CropConfig, save_dir: Path = DEFAULT_CONFIG_STORE
):
    """Save hostpot info to persistent data store"""
    save_dir.mkdir(exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    save_path = save_dir / f"{date}_{config.cam}_mbi_config.toml"
    with save_path.open("wb") as fh:
        tomli_w.dump(config.model_dump(mode="json"), fh)
    save_path = save_dir / f"{date}_{config.cam}_mbir_config.toml"
    with save_path.open("wb") as fh:
        tomli_w.dump(config_reduced.model_dump(mode="json"), fh)


def generate_standard_crop_config(hotspot: HotspotInfo) -> CropConfig:
    """Generate config file for MBI crops in camstack"""
    ## Step 2: determine padding required to fit fieldstop (536 px, nominally)
    pad_size = 536 / 2
    min_x = hotspot.absx - pad_size
    min_y = hotspot.absy - pad_size
    ## Step 3: round origin point (down) to nearest multiple of 4, which is
    # required for the orcaquests
    min_x_rounded = np.floor(min_x / 4) * 4
    min_y_rounded = np.floor(min_y / 4) * 4
    ## Step 4: assemble config object
    # note: hard-coded width of 536
    config = CropConfig.model_construct(
        cam=hotspot.cam,
        origin=(min_y_rounded, min_x_rounded),
        size=(536, 536),
        hotspots={hotspot.field: (hotspot.absx, hotspot.absy)},
    )
    return config


def generate_mbi_crop_config(hotspots: dict[str, HotspotInfo]) -> CropConfig:
    """Generate config file for MBI crops in camstack"""
    ## Step 1: get minimum, maximum psf centers
    hotspot_values = hotspots.values()
    min_cx = min(h.absx for h in hotspot_values)
    max_cx = max(h.absx for h in hotspot_values)
    min_cy = min(h.absy for h in hotspot_values)
    max_cy = max(h.absy for h in hotspot_values)
    # TODO do some sanity checks here
    ## Step 2: determine padding required to fit fieldstop (536 px, nominally)
    pad_size = 536 / 2
    min_x = min_cx - pad_size
    max_x = max_cx + pad_size
    min_y = min_cy - pad_size
    max_y = max_cy + pad_size
    ## Step 3: round origin point (down) to nearest multiple of 4, which is
    # required for the orcaquests
    min_x_rounded = np.floor(min_x / 4) * 4
    min_y_rounded = np.floor(min_y / 4) * 4
    ## Step 4: determine upper bound by finding ncols,nrows that
    # are closest multiple of 4 (rounding up)
    range_x_rounded = np.ceil((max_x - min_x_rounded) / 4) * 4
    range_y_rounded = np.ceil((max_y - min_y_rounded) / 4) * 4
    ## Step 5: assemble config object
    spots = {f: (h.absx, h.absy) for f, h in hotspots.items()}
    config = CropConfig.model_construct(
        cam=hotspots["F720"].cam,
        origin=(int(min_y_rounded), int(min_x_rounded)),
        size=(int(range_y_rounded), int(range_x_rounded)),
        hotspots=spots,
    )
    return config


def generate_mbir_crop_config(hotspots: Iterable[HotspotInfo]) -> CropConfig:
    """Generate config file for MBI crops in camstack"""
    hotspot_values = [val for key, val in hotspots.items() if key != "F610"]
    min_cx = min(h.absx for h in hotspot_values)
    max_cx = max(h.absx for h in hotspot_values)
    min_cy = min(h.absy for h in hotspot_values)
    max_cy = max(h.absy for h in hotspot_values)
    # TODO do some sanity checks here
    ## Step 2: determine padding required to fit fieldstop (536 px, nominally)
    pad_size = 536 / 2
    min_x = min_cx - pad_size
    max_x = max_cx + pad_size
    min_y = min_cy - pad_size
    max_y = max_cy + pad_size
    ## Step 3: round origin point (down) to nearest multiple of 4, which is
    # required for the orcaquests
    min_x_rounded = np.floor(min_x / 4) * 4
    min_y_rounded = np.floor(min_y / 4) * 4
    ## Step 4: determine upper bound by finding ncols,nrows that
    # are closest multiple of 4 (rounding up)
    range_x_rounded = np.ceil((max_x - min_x_rounded) / 4) * 4
    range_y_rounded = np.ceil((max_y - min_y_rounded) / 4) * 4
    ## Step 5: assemble config object
    spots = {f: (h.absx, h.absy) for f, h in hotspots.items() if f != "F610"}
    config_reduced = CropConfig.model_construct(
        cam=hotspots["F720"].cam,
        origin=(int(min_y_rounded), int(min_x_rounded)),
        size=(int(range_y_rounded), int(range_x_rounded)),
        hotspots=spots,
    )
    return config_reduced


@click.command("hotspot")
@click.argument("shm_name")
@click.option("-n", "--num-frames", default=10, type=int)
@click.option(
    "-r", "--report", is_flag=True, help=f"Save crop configs to CSV file in {DEFAULT_CSV_STORE}"
)
@click.option(
    "-s/-ns",
    "--save/--no-save",
    default=True,
    help=f"Save hotspots to CSV file in {DEFAULT_CSV_STORE}",
)
def hotspot(shm_name: str, num_frames=10, save: bool = True, report: bool = False):
    shm = SHM(shm_name)
    data = shm.multi_recv_data(num_frames, outputFormat=2)
    frame = np.median(data, axis=0, overwrite_input=True)
    mbi_status = redis.RDB.hget("U_MBI", "value")
    if mbi_status.lower() == "dichroics":
        hotspots = fit_hotspots_mbi(frame, shm)
        if report:
            report = generate_mbi_crop_config(hotspots)
            config_reduced = generate_mbir_crop_config(hotspots)
            save_configs_to_db(report, config_reduced)
        hotspot_values = list(hotspots.values())
    else:
        hotspots = fit_hotspots_standard(frame, shm)
        if report:
            report = generate_standard_crop_config(hotspots)
        hotspot_values = (hotspots,)

    if save:
        save_hotspots_to_db(hotspot_values)

    print_hotspots(hotspots)
    return hotspots


def print_hotspots(hotspots):
    pass


if __name__ == "__main__":
    click.echo(hotspot())
