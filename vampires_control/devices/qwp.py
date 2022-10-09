from argparse import ArgumentParser
import json


from plugins import ZMQPlugin
from drivers.conex import ConexDevice


class VAMPIRESQWP(ConexDevice, ZMQPlugin):
    def __init__(self, *args, offset=0, **kwargs):
        self.offset = offset

        # set up argument parser
        self.argparser = ArgumentParser("VAMPIRES QWP", allow_abbrev=True)
        self.argparser.add_argument(
            "-w", "--wait", action="store_true", help="Block until motion is completed"
        )

        return super().__init__(*args, **kwargs)

    def target_position(self):
        val = super().target_position()
        return val + self.offset

    def true_position(self):
        cmd = f"1TP?\r\n".encode()
        self.logger.debug(f"TRUE POSITION command: {cmd}")
        self.serial.write(cmd)
        retval = self.serial.read(1024).decode("utf-8")
        self.logger.debug(f"returned value: {retval}")
        # cut off leading command
        value = float(retval[3:])
        value += self.offset
        if self.keyword is not None:
            VAMPIRES[self.keyword] = value
        return value

    def move_absolute(self, value: float, **kwargs):
        real_value = value - self.offset
        return super().move_absolute(real_value, **kwargs)

    def help_message(self):
        cmds = [self.name, *self.shorthands]
        helpstr = f"""
qwp,q

Commands:
    qwp,q {{1,2}} ([st]atus|[h]ome|[r]eset|[g]oto|[n]udge) [<angle>]  [-w | --wait]

Options:
    -h --help   Display this message
    -w --wait   Block until motion is completed, if applicable
        """
        return helpstr

    def handle_message(self, message):
        pass
