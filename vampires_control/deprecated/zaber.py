#! /usr/bin/env python

##############################################
#  _   _____   __  ______  _______  ________ #
# | | / / _ | /  |/  / _ \/  _/ _ \/ __/ __/ #
# | |/ / __ |/ /|_/ / ___// // , _/ _/_\ \   #
# |___/_/ |_/_/  /_/_/  /___/_/|_/___/___/   #
#                                            #
##############################################

###########################################################
# Created by Guillaume Schworer guillaume.schworer@obspm.fr#
# from Frants Martinache's code                           #
###########################################################


from sys import argv
from serial import Serial as serialSerial
import os
import time
from numpy import zeros, sum, arange, sort

brate = 9600  # baud rate for Zaber actuators
timeout = 15  # time out for read from zabers
zabdevice = "/dev/serial/by-id/usb-FTDI_USB_Serial_Converter_FTG4YSH7-if00-port0"
encoding = "latin-1"


class pycolor:
    header = "\033[95m"
    okblue = "\033[94m"
    okgreen = "\033[92m"
    warning = "\033[93m"
    fail = "\033[91m"
    endc = "\033[0m"


zabMapping = {
    1: "right/left mask wheel",
    2: "up/down mask wheel",
    3: "focus camera",
    4: "not connected",
    5: "not connected",
}


def step2zaberByte(nstep):
    step = nstep  # local version of the variable
    zbytes = [0, 0, 0, 0]  # series of four bytes for Zaber
    if step < 0:
        step += 256**4
    for i in range(3, -1, -1):
        zbytes[i] = int(step / 256**i)
        step -= zbytes[i] * 256**i
    return zbytes


def zaberByte2step(zb):
    if len(zb) < 4:
        return
    nstep = zb[3] * 256**3 + zb[2] * 256**2 + zb[1] * 256 + zb[0]
    if zb[3] > 127:
        nstep -= 256**4
    return nstep


def mode2Byte(nmode):
    mode = nmode  # local version of the variable
    zbytes = zeros(16).astype(int)  # series of 16 bytes for Zaber modes
    for i in range(15, -1, -1):
        zbytes[i] = mode / 2**i
        mode -= zbytes[i] * 2**i
    return zbytes


def Byte2mode(nbytes):
    return sum([nbytes[i] * 2**i for i in range(len(nbytes))])


def zab_cmd(cmd):
    nl = []
    instr = list(map(int, cmd.split(" ")))
    for c in instr:
        if c == 255:
            nl.extend([c, c])
        else:
            nl.append(c)
    buf = "".join(map(chr, nl))
    return buf


def make_them_astro(on=True):
    val = 0
    if on:
        val = 1
    for i in list(zabMapping.keys()):
        bits = mode2Byte(command(int(i), 53, 40))
        bits[3] = val
        bits[14] = val
        bits[15] = val
        dummy = command(i, 40, Byte2mode(bits))
    print(f"{pycolor.warning}Astro mode is {'on' if on else 'off'}{pycolor.endc}")


def set_speed():
    dummy = command(1, 42, 3400)
    dummy = command(2, 42, 1000)
    dummy = command(3, 42, 3400)
    dummy = command(4, 42, 1500)
    dummy = command(5, 42, 3400)
    print(f"{pycolor.warning}Set speed to safe values{pycolor.endc}")


def command(idn, cmd, arg, timeout=timeout):
    global ser
    args = " ".join(map(str, step2zaberByte(arg)))
    full_cmd = "%s %d %s" % (idn, cmd, args)
    dummy = (
        ser.readlines()
    )  # flush all stored results tracking manual movement (command 10)
    print(dummy)
    print(f"full command: {full_cmd}")
    print(f"encoded: {zab_cmd(full_cmd).encode()}")
    ecmd = zab_cmd(full_cmd).encode()
    ser.write(ecmd)
    start = time.time()
    dummy = []
    if cmd == 0:
        return
    while dummy == []:
        time.sleep(0.1)
        lines_bytes = ser.readlines()
        lines_str = map(lambda l: l.decode(encoding), lines_bytes)
        dummy = list(map(ord, "".join(lines_str)))[
            :6
        ]  # read all lines, in case the character chr(10)='\n' is within the answer
        if time.time() - start > timeout:
            print(f"{pycolor.warning}Answer timed out{pycolor.endc}")
            return
    return zaberByte2step(dummy[2:])  # returns the result


def mian():
    # checks options
    modeAstro = None
    safeSpeed = None
    giveAllPositions = None
    inputNum = None
    if ("-h" in argv) or ("-H" in argv) or (len(argv) < 2) or (len(argv) > 8):
        argv.append("-h")
    if argv[-1][:2].upper() == "-H":
        print(
            f"\n{pycolor.fail}zab{pycolor.endc} [{pycolor.okblue}-h{pycolor.endc} (help)] {pycolor.okgreen}zabNumer commandNumer argument{pycolor.endc} [{pycolor.okblue}-t{pycolor.endc}='timeout' (15sec)] [{pycolor.okblue}-a{pycolor.endc}='on|off' set mode astro] [{pycolor.okblue}-s{pycolor.endc} set safe speeds] [{pycolor.okblue}-p{pycolor.endc} show all positions]\n"
        )
        output = f"{pycolor.okgreen}zabNumer{pycolor.endc}:\n"
        for i in sort(list(zabMapping.keys())):
            output += f"{pycolor.warning}{i}{pycolor.endc}-{zabMapping[i]}\n"
        print(output)
        print(
            f"{pycolor.okgreen}commandNumer{pycolor.endc}: (* no argument needed)\n0*: Reset\n1*: Home\n2: Rename (new zaber number)\n20: Move absolute (step)\n21: Move relative (+/-step)\n42: Set speed (speed)\n44: Set maximum position (step)\n53: Query command value (command number)\n60*: Get position\n"
        )
        quit()

    for arg in argv[1:]:
        if arg[0] == "-":
            if arg[1].upper() == "T":
                try:
                    timeout = min(60, float(arg[arg.find("=") + 1 :]))
                except:
                    print(f"{pycolor.fail}Fail: can't read -t={pycolor.endc}")
                    quit()
            elif arg[1].upper() == "A":
                try:
                    modeAstro = str(arg[arg.find("=") + 1 :])
                except:
                    print(f"{pycolor.fail}Fail: can't read -a={pycolor.endc}")
                    quit()
                if modeAstro[:3].upper() == "OFF":
                    modeAstro = False
                else:
                    modeAstro = True
            elif arg[1].upper() == "P":
                giveAllPositions = True
            elif arg[1].upper() == "S":
                safeSpeed = True
        else:
            if inputNum == None:
                zabNumber = int(arg)
                inputNum = 1
            elif inputNum == 1:
                zabCommand = int(arg)
                inputNum = 2
            elif inputNum == 2:
                zabArgument = int(arg)

    # connection
    try:
        ser = serialSerial(zabdevice, brate, timeout=0.5)
    except:
        print(f"{pycolor.fail}Fail: Can't connect to Zabers{pycolor.endc}")
        quit()
    dummy = ser.readlines()  # flushes
    print(dummy)
    if modeAstro is not None:
        make_them_astro(on=modeAstro)
    if safeSpeed is not None:
        set_speed()
    if giveAllPositions is not None:
        for i in list(zabMapping.keys()):
            print(
                f"{pycolor.warning}{zabMapping[i]}{pycolor.endc}: {str(command(i, 60, 0, timeout))}"
            )
    if inputNum is not None:
        try:
            zabCommand
        except:
            print(f"{pycolor.fail}Fail: incomplete input{pycolor.endc}")
            ser.close()
            quit()
        try:
            zabArgument
        except:
            zabArgument = 0
        if int(zabNumber) not in list(zabMapping.keys()):
            print(f"{pycolor.fail}Fail: zaber number unknown{pycolor.endc}")
            ser.close()
            quit()
        print(command(zabNumber, zabCommand, zabArgument, timeout))
    ser.close()
