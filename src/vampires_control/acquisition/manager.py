import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Literal

from paramiko import AutoAddPolicy, SSHClient
from pyMilk.interfacing.fps import FPS
from swmain.redis import RDB
from datetime import datetime, timezone

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


class CamLogManager:
    DATA_DIR_BASE = Path("/mnt/fuuu/")
    ARCHIVE_DATA_DIR_BASE = Path("/mnt/fuuu/ARCHIVED_DATA")
    COMPUTER = "scexao5"
    BASE_COMMAND = ("milk-streamFITSlog", "-cset", "q_asl")

    def __init__(self, shm_name: str):
        self.shm_name = shm_name
        fps_name = f"streamFITSlog-{self.shm_name}"
        self.fps = FPS(fps_name)

    @classmethod
    def create(cls, shm_name, num_frames: int, num_cubes=-1, folder=None):
        # if archive:
        #     save_dir = cls.ARCHIVE_DATA_DIR_BASE
        # else:
        #     save_dir = cls.DATA_DIR_BASE
        path = Path(folder) / shm_name
        # print(f"Saving data to directory {folder.absolute()}")
        cmd = [
            "ssh",
            f"scexao@{cls.COMPUTER}",
            *cls.BASE_COMMAND,
            "-z",
            str(num_frames),
            "-D",
            str(path.absolute()),
        ]
        if num_cubes > 0:
            cmd.extend(("-c", f"{num_cubes}"))
        cmd.extend((shm_name, "pstart"))
        subprocess.run(cmd, check=True, capture_output=True)
        time.sleep(0.5)
        return cls(shm_name)

    def start_acquisition(self):
        # start logging
        self.fps.set_param("saveON", True)
        self.update_keys(logging=True)

    def pause_acquisition(self, wait_for_cube=False):
        # pause logging
        if wait_for_cube:
            # allow cube to fill up
            self.fps.set_param("lastcubeON", True)
            self.wait_for_acquire()
        else:
            # truncate cube immediately
            self.fps.set_param("saveON", False)
        self.update_keys(logging=False)

    def wait_for_acquire(self):
        _wait_delay = 0.1
        while self.fps.get_param("saveON"):
            time.sleep(_wait_delay)

    def kill_process(self):
        command = ["ssh", f"scexao@{self.computer}", *self.base_command, self.shm_name, "kill"]
        subprocess.run(command, check=True, capture_output=True)
        self.update_keys(logging=False)

    def acquire_cubes(self, num_cubes: int):
        # assert we start at 0 filecnt
        self.fps.set_param("filecnt", 0)
        self.fps.set_param("maxfilecnt", num_cubes)
        self.start_acquisition()
        self.wait_for_acquire()

    def update_keys(self, logging: bool):
        pass


class VCAMLogManager(CamLogManager):
    COMPUTER = "scexao5"

    def __init__(self, cam_num: Literal[1, 2], **kwargs):
        shm_name = f"vcam{cam_num:d}"
        super().__init__(shm_name, **kwargs)


    @classmethod
    def create(cls, cam_num: Literal[1, 2], num_frames: int, num_cubes=-1, folder=None):
        shm_name = f"vcam{cam_num:d}"
        # if archive:
        #     save_dir = cls.ARCHIVE_DATA_DIR_BASE
        # else:
        #     save_dir = cls.DATA_DIR_BASE
        path = Path(folder) / shm_name
        # print(f"Saving data to directory {folder.absolute()}")
        cmd = [
            "ssh",
            f"scexao@{cls.COMPUTER}",
            *cls.BASE_COMMAND,
            "-z",
            str(num_frames),
            "-D",
            str(path.absolute()),
        ]
        if num_cubes > 0:
            cmd.extend(("-c", f"{num_cubes}"))
        cmd.extend((shm_name, "pstart"))
        subprocess.run(cmd, check=True, capture_output=True)
        time.sleep(0.5)
        return cls(cam_num)