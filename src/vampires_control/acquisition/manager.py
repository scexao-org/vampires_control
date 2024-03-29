import logging
import time

from paramiko import AutoAddPolicy, SSHClient
from swmain.redis import RDB

logger = logging.getLogger(__name__)


class CamManager:
    def __init__(self, shm_name, computer="scexao6", cset="aol0log", port=22):
        self.shm_name = shm_name
        self.computer = computer
        self.cset = cset
        self.base_command = f"milk-streamFITSlog -cset {self.cset}"
        self.should_be_alive = False

        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.client.load_system_host_keys()
        self.client.connect(
            self.computer,
            port=port,
            username="scexao",
            disabled_algorithms={"pubkeys": ("rsa-sha2-256", "rsa-sha2-512")},
        )

    def prepare(self):
        pass

    def send_command(self, cmd):
        logger.debug(f"command sent: '{cmd}'")
        _, stdout, stderr = self.client.exec_command(cmd)
        logger.debug(f"STDOUT: {stdout.read().decode()}")
        logger.debug(f"STDERR: {stderr.read().decode()}")

    def start_acquisition(self, num_cubes=None):
        cmd = self.base_command
        if num_cubes is not None:
            cmd += f" -c {num_cubes}"
        cmd += f" {self.shm_name} on"
        self.send_command(cmd)
        self.update_keys(logging=True)

    def pause_acquisition(self):
        cmd = f"{self.base_command} {self.shm_name} off"
        self.send_command(cmd)
        self.update_keys(logging=False)

    def kill_process(self):
        self.update_keys(logging=False)

    def update_keys(self, logging: bool):
        pass


class VCAMManager(CamManager):
    def __init__(self, cam_number, shm_name=None, computer="scexao5", cset="q_asl", **kwargs):
        self.cam_number = cam_number
        shm_name = f"vcam{cam_number}"
        super().__init__(shm_name, computer, cset, **kwargs)

    def update_keys(self, logging: bool):
        for _ in range(10):
            try:
                RDB.hset(f"U_VLOG{self.cam_number}", "value", logging)
                break
            except Exception:
                time.sleep(0.5)
