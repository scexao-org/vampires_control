import urllib
from typing import Final

import astropy.units as u
import numpy as np
from astropy.utils.data import download_file
from synphot import SpectralElement

VAMPIRES_STD_FILTERS: Final[set] = {"Open", "625-50", "675-50", "725-50", "750-50", "775-50"}
VAMPIRES_MBI_FILTERS: Final[set] = {"F610", "F670", "F720", "F760"}
VAMPIRES_NB_FILTERS: Final[set] = {"Halpha", "Ha-Cont", "SII", "SII-Cont"}
VAMPIRES_FILTERS: Final[set] = set.union(
    VAMPIRES_STD_FILTERS, VAMPIRES_MBI_FILTERS, VAMPIRES_NB_FILTERS
)
VAMPIRES_ND_FILTERS: Final[set] = {"ND10", "ND25"}


VAMP_FILT_KEY: Final[str] = "1FHGh3tLlDUwATP6smFGz0nk2e0NF14rywTUjFTUT1OY"
VAMP_FILT_NAME: Final[str] = urllib.parse.quote("VAMPIRES Filter Curves")
VAMPIRES_FILTER_URL: Final[
    str
] = f"https://docs.google.com/spreadsheets/d/{VAMP_FILT_KEY}/gviz/tq?tqx=out:csv&sheet={VAMP_FILT_NAME}"


def load_vampires_filter(name: str) -> SpectralElement:
    if name not in VAMPIRES_FILTERS:
        msg = f"VAMPIRES filter '{name}' not recognized"
        raise ValueError(msg)
    csv_path = download_file(VAMPIRES_FILTER_URL, cache=True)
    return SpectralElement.from_file(csv_path, wave_unit="nm", include_names=["wave", name])


def get_filter_info_dict(filt_name: str) -> tuple[SpectralElement, dict]:
    filt = load_vampires_filter(filt_name)
    waves = filt.waveset
    through = filt.model.lookup_table
    above_50 = np.nonzero(through >= 0.5 * np.nanmax(through))
    waveset = waves[above_50]
    info = {
        "FILTNAME": filt_name,
        "WAVEMIN": waveset[0].to(u.nm).value,
        "WAVEMAX": waveset[-1].to(u.nm).value,
        "WAVEAVE": filt.avgwave(waveset).to(u.nm).value,
    }
    info["WAVEFWHM"] = info["WAVEMAX"] - info["WAVEMIN"]
    info["DLAMLAM"] = info["WAVEFWHM"] / info["WAVEAVE"]
    info["DIAMETER"] = 7.92
    info["RESELEM"] = np.rad2deg(info["WAVEAVE"] * 1e-9 / info["DIAMETER"]) * 3.6e6
    return filt, info
