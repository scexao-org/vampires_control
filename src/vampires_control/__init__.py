from pathlib import Path
import os

__version__ = "0.1.0"

conf_dir = Path(os.getenv("CONF_DIR", f"{os.getenv('HOME')}/src/vampires_control/conf/"))