from pathlib import Path

__all__ = ("CONF_DIR", "DATA_DIR")

EXPECTED_INSTALL_DIR = Path("~/src/vampires_control").expanduser()
CONF_DIR = EXPECTED_INSTALL_DIR / "conf"
CONF_DIR.mkdir(exist_ok=True)
DATA_DIR = EXPECTED_INSTALL_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
