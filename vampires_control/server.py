import json
import socketserver
from socketserver import BaseRequestHandler

from .state import LOCAL_STATE_FILE

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 47653


class VAMPIRESHandler(BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print(f"{self.client_address[0]} received: {self.data}")

        command = str(self.data, "ascii")
        tokens = command.split()
        if tokens[0] == "get":
            with open(LOCAL_STATE_FILE) as fh:
                state = json.load(fh)
                value = state[tokens[1]]
            self.request.sendall(bytes(value, "ascii"))
