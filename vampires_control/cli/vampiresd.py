#!/usr/bin/env python
from docopt import docopt
from daemon import DaemonContext
import logging
from logging.config import dictConfig
from logging.handlers import TimedRotatingFileHandler, SysLogHandler
import zmq
from pathlib import Path
from vampires_control.server import DEFAULT_HOST, DEFAULT_PORT, handle_message

__doc__ = f"""
Usage:
    vampiresd [-h | --help] [--host <HOST>] [-p <PORT> | --port <PORT>]

Launch the VAMPIRES server daemon.

Options:
    -h --help           Print this message
    --host <HOST>       Change the port, default is {DEFAULT_HOST}
    -p --port <PORT>    Change the port, default is {DEFAULT_PORT}

"""

# set up logging
LOG_PATH = Path("/var/log/vampires/vampires.log").resolve()
DEBUG_LOG_PATH = Path("/var/log/vampires/vampires_debug.log").resolve()
# ensure directories exist
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s|%(levelname)s|%(name)s - %(message)s"}
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "when": "midnight",
                "utc": True,
                "backupCount": 9999,
                "level": logging.INFO,
                "filename": LOG_PATH,
                "formatter": "standard",
            },
            "debug": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "when": "midnight",
                "utc": True,
                "backupCount": 31,
                "level": logging.DEBUG,
                "filename": DEBUG_LOG_PATH,
                "formatter": "standard",
            },
            "stream": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": logging.INFO,
            },
        },
        "loggers": {
            "": {"handlers": ["file", "debug", "stream"], "level": logging.DEBUG}
        },
    }
)
# logging.basicConfig(level=logging.DEBUG, format="%(asctime)s|%(levelname)s|%(name)s - %(message)s", handlers=[SysLogHandler(), TimedRotatingFileHandler("/var/log/vampires/vampires.log", when="midnight", utc=True, backupCount=9999)])
logger = logging.getLogger("vampires")


def launch_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    context = zmq.Context()
    # create reply request socket
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{host}:{port}")

    # begin receiving requests
    while True:
        message = socket.recv()
        logger.debug(f"message received: {message}")
        response = handle_message(str(message, "ascii"))

        socket.send_string(response)


def main():
    args = docopt(__doc__)
    host = args["--host"] if args["--host"] is not None else DEFAULT_HOST
    port = int(args["--port"]) if args["--port"] is not None else DEFAULT_PORT

    logger.info(f"launching server on at {host}:{port}")
    # with DaemonContext():
    launch_server(host, port)

if __name__ == "__main__":
    main()