from argparse import ArgumentParser




class VAMPIRESFocus(ConexDevice, ZMQPlugin):

    def __init__(self, *args, **kwargs):

        self.argparser = ArgumentParser("VAMPRIES Focus")
        self.argparser.add_argument("-w", "--wait", action="store_true", help="Block until motion is completed")
        self.argparser.add_argument("")

        super().__init__(*args, **kwargs)


    def handle_message(self, message):
        pass

focus = ConexDevice(
    "focus",
    DEVICE_MAP["focus_stage"],
    keyword="focus_stage",
    unit="mm",
    shorthands=["f"],
    argname="pos",
)