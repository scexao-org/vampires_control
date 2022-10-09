#!/usr/bin/env python

##############################################
#  _   _____   __  ______  _______  ________ #
# | | / / _ | /  |/  / _ \/  _/ _ \/ __/ __/ #
# | |/ / __ |/ /|_/ / ___// // , _/ _/_\ \   #
# |___/_/ |_/_/  /_/_/  /___/_/|_/___/___/   #
#                                            #
##############################################

###########################################################
# Created by Guillaume Schworer guillaume.schworer@obspm.fr#
# from bits of Frants Martinache's code                   #
###########################################################

##############################################
# Murdered by Miles Lucas mdlucas@hawaii.edu #
# use `vampires_control` instead             #
##############################################

from sys import argv

from vampires_control.devices.devices import (
    beamsplitter,
    focus,
    differential_filter,
    qwp_1,
    qwp_2,
    pupil_wheel,
)


class pycolor:
    header = "\033[95m"
    okblue = "\033[94m"
    okgreen = "\033[92m"
    warning = "\033[93m"
    fail = "\033[91m"
    endc = "\033[0m"


conexWait = True
conexAddress = {
    "1": [
        "/dev/serial/by-id/usb-Newport_CONEX-AGP_A6VMT5XJ-if00-port0",
        "1/4 wave plate 2",
    ],
    "2": ["/dev/serial/by-id/usb-Newport_CONEX-AGP_A6VRT271-if00-port0", "mask wheel"],
    "4": [
        "/dev/serial/by-id/usb-Newport_CONEX-AGP_A6WXETGZ-if00-port0",
        "1/4 wave plate 1",
    ],
    "5": [
        "/dev/serial/by-id/usb-Newport_CONEX-AGP_A6Z9D9VP-if00-port0",
        "Focusing stage",
    ],
    "8": [
        "/dev/serial/by-id/usb-Newport_CONEX-AGP_A60QBY6C-if00-port0",
        "Beamsplitter wheel",
    ],
    "9": [
        "/dev/serial/by-id/usb-FTDI_USB-RS422_Cable_FT0B42PZ-if00-port0",
        "Differential filter wheel",
    ],
}

DEVICE_MAP = {
    "1": qwp_2,
    "2": pupil_wheel.pupil_wheel,
    "4": qwp_1,
    "5": focus,
    "8": beamsplitter.beamsplitter_wheel,
    "9": differential_filter.diffwheel,
}
DEVICE_NAME = {
    "1": "qwp_2",
    "2": "pupil_wheel.pupil_wheel",
    "4": "qwp_1",
    "5": "focus",
    "8": "beamsplitter.beamsplitter_wheel",
    "9": "differential_filter.diffwheel",
}
COMMAND_MAP = {
    "1": "vampires_qwp 2",
    "2": "vampires_pupil wheel",
    "4": "vampires_qwp 1",
    "5": "vampires_focus",
    "8": "vampires_beamsplitter wheel",
    "9": "vampires_diffwheel wheel",
}


def main():
    # checks options and arguments
    if ("-h" in argv) or ("-H" in argv) or (len(argv) < 3) or (len(argv) > 5):
        argv.append("-h")
    if argv[-1][:2].upper() == "-H":
        print(
            f"\n{pycolor.fail}conex{pycolor.endc} [{pycolor.okblue}-h{pycolor.endc} (help)] {pycolor.okgreen}conexDeviceNumber command argument [{pycolor.okblue}-w{pycolor.endc} (wait until conex is in-place)]\n"
        )
        output = f"{pycolor.okgreen}conexDeviceNumber{pycolor.endc}:\n"
        for i in conexAddress.keys():
            output = (
                f"{output}{pycolor.warning}{i}{pycolor.endc}- {conexAddress[i][1]}\n"
            )
        print(output)
        print(
            f"{pycolor.okgreen}command{pycolor.endc}: (* no argument needed)\nRS*: Reset\nOR*: Home\nPA: Move absolute (deg)\nPR: Move relative (deg)\nTH*: Get target position\nTP*: Get current position\nST*: Stop motion\n"
        )
        quit()
    else:
        conexNumber = argv[1]
        device = DEVICE_MAP[conexNumber]
        devicename = DEVICE_NAME[conexNumber]
        conexCommand = argv[2].upper()
        # deprecation warnings
        newcmd = COMMAND_MAP[conexNumber]
        origcmd = " ".join(argv[1:])
        print(f"{pycolor.fail}DEPRECATION WARNING{pycolor.endc}")
        print(
            f"Please use the new {pycolor.okblue}vampires_control{pycolor.endc} scripts"
        )
        print(f"Instead of\n\n\t{pycolor.okgreen}conex {origcmd}{pycolor.endc}\n")
        if conexCommand == "OR":
            try:
                conexArgument = argv[3].lower()
                if conexArgument == "-w":
                    print(f"use\n\n\t{pycolor.okgreen}{newcmd} home -w{pycolor.endc}\n")
                    device.home(wait=True)
                else:
                    print(f"use\n\n\t{pycolor.okgreen}{newcmd} home{pycolor.endc}\n")
                    device.home()
            except:
                print(f"use\n\n\t{pycolor.okgreen}{newcmd} home{pycolor.endc}\n")
                device.home()
        elif conexCommand == "RS":
            print(f"use\n\n\t{pycolor.okgreen}{newcmd} reset{pycolor.endc}\n")
            device.reset()
        elif conexCommand == "TH":
            print(f"use\n\n\t{pycolor.okgreen}{newcmd} target{pycolor.endc}\n")
            print(device.target_position())
        elif conexCommand == "TP":
            print(f"use\n\n\t{pycolor.okgreen}{newcmd} status{pycolor.endc}\n")
            print(device.true_position())
        elif conexCommand == "ST":
            print(f"use\n\n\t{pycolor.okgreen}{newcmd} stop{pycolor.endc}\n")
            device.stop()
        elif conexCommand == "PA":
            conexArgument = float(argv[3])
            try:
                conexArgument2 = argv[4].lower()
                if conexArgument2 == "-w":
                    print(
                        f"use\n\n\t{pycolor.okgreen}{newcmd} goto {conexArgument} -w{pycolor.endc}\n"
                    )
                    device.move_absolute(conexArgument, wait=True)
                else:
                    print(
                        f"use\n\n\t{pycolor.okgreen}{newcmd} goto {conexArgument}{pycolor.endc}\n"
                    )
                    device.move_absolute(conexArgument)
            except:
                print(
                    f"use\n\n\t{pycolor.okgreen}{newcmd} goto {conexArgument}{pycolor.endc}\n"
                )
                device.move_absolute(conexArgument)
        elif conexCommand == "PR":
            conexArgument = float(argv[3])
            try:
                conexArgument2 = argv[4].lower()
                if conexArgument2 == "-w":
                    print(
                        f"use\n\n\t{pycolor.okgreen}{newcmd} nudge {conexArgument} -w{pycolor.endc}\n"
                    )
                    device.move_relative(conexArgument, wait=True)
                else:
                    print(
                        f"use\n\n\t{pycolor.okgreen}{newcmd} nudge {conexArgument}{pycolor.endc}\n"
                    )
                    device.move_relative(conexArgument)
            except:
                print(
                    f"use\n\n\t{pycolor.okgreen}{newcmd} nudge {conexArgument}{pycolor.endc}\n"
                )
                device.move_relative(conexArgument)


if __name__ == "__main__":
    main()
