from docopt import docopt
from daemon import DaemonContext
import json
from vampires_control.devices.qwp import VAMPIRESQWP
from vampires_control.config import DEVICE_ADDRESSES_FILE, QWP_OFFSETS_FILE

with open(DEVICE_ADDRESSES_FILE) as fh:
    DEVICE_MAP = json.load(fh)

with open(QWP_OFFSETS_FILE) as fh:
    QWP_OFFSETS = json.load(fh)

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

    # QWP 2
    qwp_2 = VAMPIRESQWP(
        "qwp_2",
        DEVICE_MAP["qwp_2"],
        offset=QWP_OFFSETS["qwp_2_offset"],
        keyword="qwp_2",
        unit="deg",
    )
    with DaemonContext():
        qwp_2.launch_server()

if __name__ == "__main__":
    main()