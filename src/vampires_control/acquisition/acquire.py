
from argparse import ArgumentParser

DATA_TYPES = (
    "OBJECT",
    "DARK",
    "FLAT",
    "BIAS",
    "SKYFLAT",
    "DOMEFLAT",
    "COMPARISON",
    "TEST"
)

parser = ArgumentParser("acquire", description="Acquire data with VAMPIRES")
parser.add_argument("num_frames", type=int, description="Number of frames per cube")
parser.add_argument("num_cubes", required=False, type=int, description="Number of cubes. If None, will acquire until aborted")

parser.add_argument("-t", "--type", type=str.upper, default="OBJECT", choices=DATA_TYPES, help="FITS Data type")
parser.add_argument("--single-cam", const=1, nargs="?", choices=(1, 2), help="Only log from a single camera (which can be specified by passing --single-cam=1 or 2). Note that both cameras will still trigger.")
parser.add_argument("-P", "--pdi", action="store_true", help="PDI mode. In this mode every FITS cube exposure is triggered by the HWP daemon. All PDI settings (like number of cubes per HWP position) are handled by the HWP daemon.")
parser.add_argument("-S", "--sdi", action="store_true", help="SDI mode. In this mode, exposures are controlled by the SDI daemon. All SDI settings (like number of cubes per diff wheel position) are handled by the SDI daemon.")


def main():
    args = parser.parse_args()


if __name__ == "__main__":
    main()