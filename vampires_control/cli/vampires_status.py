#!/usr/bin/env python
from docopt import docopt

from vampires_control.state import VAMPIRES

__doc__ = """
Usage:
    vampires_status [<key>] [-h | --help]

Options:
    -h --help   Print this screen
"""

def main():
    args = docopt(__doc__)
    if args["<key>"] is not None:
        print(VAMPIRES[args["<key>"]])
    else:
        out = "\n".join(f"{k}: {v}" for k, v in VAMPIRES.state_dict.items())
        print(out)

if __name__ == "__main__":
    main()