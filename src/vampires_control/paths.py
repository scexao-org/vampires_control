from pathlib import Path

__all__ = ("CONF_DIR", "DATA_DIR")

EXPECTED_INSTALL_DIR = Path("~/src/vampires_control").expanduser()
CONF_DIR = EXPECTED_INSTALL_DIR / "conf"
CONF_DIR.mkdir(exist_ok=True)
DATA_DIR = CONF_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
SYNTHPSF_DIR = DATA_DIR / "psfs"
SYNTHPSF_DIR.mkdir(exist_ok=True)
CROPS_DIR = CONF_DIR / "crops"
CROPS_DIR.mkdir(exist_ok=True)
