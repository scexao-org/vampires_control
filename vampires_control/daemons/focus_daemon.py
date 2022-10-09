from docopt import docopt
from daemon import DaemonContext
import json
from vampires_control.devices.qwp import VAMPIRESQWP
from vampires_control.config import DEVICE_ADDRESSES_FILE, QWP_OFFSETS_FILE

with open(DEVICE_ADDRESSES_FILE) as fh:
    DEVICE_MAP = json.load(fh)

def main():
    # QWP 1
    qwp_1 = VAMPIRESQWP(
        "qwp_1",
        DEVICE_MAP["qwp_1"],
        offset=QWP_OFFSETS["qwp_1_offset"],
        keyword="qwp_1",
        unit="deg",
    )
    with DaemonContext():
        qwp_1.launch_server()

if __name__ == "__main__":
    main()