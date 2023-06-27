import time
from datetime import datetime
from pathlib import Path

from camstack.core.tmux import find_or_create_remote
from swmain.redis import update_keys

DATA_DIR_BASE = Path("/mnt/tier0/")


def start_acq_one_camera(base_dir: Path, cam_num: int, num_per_cube: int):
    tmux = find_or_create_remote(f"vcam{cam_num}_log", "scexao@scexao6")
    save_dir = base_dir / f"vcam{cam_num}"
    tmux.send_keys(f"mkdir -p {save_dir.absolute()}")
    tmux.send_keys(f"milk-logshim vcam{cam_num} {num_per_cube} {save_dir.absolute()} &")


def kill_acq_one_camera(cam_num):
    tmux = find_or_create_remote(f"vcam{cam_num}_log", "scexao@scexao6")
    tmux.send_keys(f"milk-logshimoff vcam{cam_num}")
    time.sleep(4)
    tmux.send_keys(f"milk-logshimkill vcam{cam_num}")


def start_acquisition(
    num_per_cube,
    cams=None,
    base_dir=DATA_DIR_BASE / datetime.utcnow().strftime("%Y%m%d"),
):
    print(f"Saving data to base directory {base_dir}")
    if cams is None or cams == 1:
        start_acq_one_camera(base_dir, 1, num_per_cube)
        update_keys(U_VLOG1=str(True))
    if cams is None or cams == 2:
        start_acq_one_camera(base_dir, 2, num_per_cube)
        update_keys(U_VLOG2=str(True))


def stop_acquisition(cams=None):
    print(f"Stopping data acquisition")
    if cams is None or cams == 1:
        kill_acq_one_camera(1)
        update_keys(U_VLOG1=str(False))
    if cams is None or cams == 2:
        kill_acq_one_camera(2)
        update_keys(U_VLOG2=str(False))
