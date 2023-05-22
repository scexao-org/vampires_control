import subprocess
import sys
import os


def main():
    args = [
        "g2cam",
        "--cam",
        "VAMPIRES",
        "--loglevel",
        "20",
        "--log",
        "g2cam.log",
        "--stderr",
        "--gen2host",
        "g2ins1.sum.subaru.nao.ac.jp",
        "--obcpnum",
        "31",
    ]
    root = os.path.dirname(__file__)
    subprocess.call(args, stdout=sys.stdout, stderr=sys.stderr, cwd=root)


if __name__ == "__main__":
    main()
