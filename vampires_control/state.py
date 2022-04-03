

import json
from pathlib import Path
from scxkw.redisutil.typed_db import Redis
from scxkw.config import REDIS_DB_HOST, REDIS_DB_PORT
from warnings import warn

LOCAL_STATE_FILE = Path("/etc/vampires-control/vampires_state.json")

class VAMPIRES:
    """
    VAMPIRES state structure.

    This class acts as middleware between the top-level VAMPIRES commands (e.g., `vampires_beamsplitter`) and the serial or library commands. As middleware, it performs logging, updating of a local JSON state file, and updating of the SCExAO redis database.
    """

    def __init__(self, local_state=LOCAL_STATE_FILE, redis_host=REDIS_DB_HOST, redis_port=REDIS_DB_PORT):
        self.local_state_file = local_state
        with open(self.local_state_file) as fh:
            self.state_dict = json.load(fh)
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.rdb = Redis(host=self.redis_host, port=self.redis_port)

    def __getitem__(self, key):
        return self.state_dict[key]

    def __setitem__(self, key, value):
        self.state_dict[key] = value
        with open(self.local_state_file, "w") as fh:
            json.dump(self.state_dict, fh)
        if not self.rdb.exists(key):
            warn(f"{key} does not exist in the redis database")
            return
        with self.rdb.pipeline() as pipe:
            pipe.hset(key, value)
            pipe.execute()

    def __repr__(self):
        return repr(self.state_dict)

    def update(self):
        with open(self.local_state_file) as fh:
            self.state_dict = json.load(fh)
