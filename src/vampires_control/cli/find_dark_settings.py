from argparse import ArgumentParser
from astropy.io import fits
import tqdm.auto as tqdm

# color codes
TB = "\033[34m"
TG = "\033[32m"
CC = "\033[0m"


def find_dark_settings(filelist):
    exp_set = set()
    for filename in filelist:
        with fits.open(filename) as hdus:
            hdr = hdus[0].header
            texp = hdr["EXPTIME"]  # exposure time in seconds
            gain = hdr["U_EMGAIN"]
            exp_set.add((texp, gain))

    return exp_set


parser = ArgumentParser(
    description="Go through directory and find which combinations of exposure times and EM gains were used. Use this at the end of an observing run to compile a list of dark frames to take."
)
parser.add_argument(
    "files",
    nargs="+",
    help="FITS files from which to scrape exposure times and EM gains",
)
parser.add_argument(
    "-p",
    "--progress",
    action="store_true",
    help="show progress bar while processing files",
)


def main():
    args = parser.parse_args()
    if args.progress:
        filelist = tqdm.tqdm(args.files)
    else:
        filelist = args.files

    exp_set = find_dark_settings(filelist)
    # sort set
    # prepare output
    lines = (
        f"{TB}Exp. time:{CC} {s[0]:6.3f} [s] / {s[0] * 1e6:8.0f} [us] {TG}EM Gain:{CC} {s[1]:3.0f}"
        for s in sorted(exp_set)
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
