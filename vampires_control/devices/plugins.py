import zmq
import logging
from scxkw.redisutil.typed_db import Redis
from scxkw.config import REDIS_DB_HOST, REDIS_DB_PORT
from warnings import warn

class ZMQPlugin:
    """
        ZMQPlugin

    This plugin provides an interface for automatically creating a ZMQ request server for a device or script.
    """

    def __init__(self, /, host, port, help_msg=None, **kwargs):
        self.host = host
        self.port = port
        self.address = f"tcp://{self.host}:{self.port}"
        self.help_msg = help_msg if help_msg is not None else ""
        self.logger = logging.getLogger(__class__.__name__)

    def handle_message(slef, message: str):
        raise NotImplementedError("handle_message must be implemented by sub-classes")

    def launch_server(self):
        context = zmq.Context()
        # create reply request socket
        socket = context.socket(zmq.REP)
        socket.bind(self.address)

        # begin receiving requests
        while True:
            message = socket.recv()
            self.logger.debug(f"message received: {message}")
            response = self.handle_message(str(message, "ascii"))

            socket.send_string(response)


def scxkw(func, key):
    """
        @scxkw(key)

    Decerator for getter functions to easily allow interfacing with the redis database
    """
    rdb = Redis(host=REDIS_DB_HOST, port=REDIS_DB_PORT)

    if not rdb.exists(key):
        warn(f"{key} does not exist in the redis database")
        return func

    def wrapped_func(*args, **kwargs):
        value = func(*args, **kwargs)
        with rdb.pipeline() as pipe:
            pipe.hset(key, value)
            pipe.execute()
        return value

    return wrapped_func
