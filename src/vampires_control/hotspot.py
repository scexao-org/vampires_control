import click
import numpy as np
from pyMilk.interfacing.isio_shmlib import SHM
from skimage.measure import centroid

MBI_ROUGH_HOTSPOTS = {
    "vcam1": {"770": (1900, 815), "720": (876, 832), "670": (310, 837), "620": (300, 280)},
    "vcam2": {"770": (1966, 334), "720": (845, 290), "670": (281, 273), "620": (259, 835)},
}


def cutout_slice(frame, window, center):
    """
    Get the index slices for a window with size `window` at `center`, clipped to the boundaries of `frame`

    Parameters
    ----------
    frame : ArrayLike
        image frame for bound-checking
    center : Tuple
        (y, x) coordinate of the window
    window : float,Tuple
        window length, or tuple for each axis

    Returns
    -------
    (ys, xs)
        tuple of slices for the indices for the window
    """
    half_width = np.asarray(window) / 2
    Ny, Nx = frame.shape[-2:]
    lower = np.maximum(0, np.round(center - half_width), dtype=int, casting="unsafe")
    upper = np.minimum((Ny - 1, Nx - 1), np.round(center + half_width), dtype=int, casting="unsafe")
    return np.s_[lower[0] : upper[0] + 1, lower[1] : upper[1] + 1]


# @click.command("hotspot")
# @click.argument("shm_name")
# @click.argument("mode", type=click.Choice(("MBI", "STANDARD"), case_sensitive=False))
def hotspot(shm_name: str, mode: str):
    shm = SHM(shm_name)
    data = shm.multi_recv_data(100, outputFormat=2)
    frame = np.median(data, axis=0, overwrite_input=True)
    print(frame.shape)

    if mode == "MBI":
        rough_spots = MBI_ROUGH_HOTSPOTS[shm_name.lower()]
        ctr = {}
        for field_name, ctr_guess in rough_spots.items():
            idxs = cutout_slice(frame, 100, ctr_guess[::-1])
            offset_ctr = centroid(frame[idxs])
            ctr[field_name] = offset_ctr + np.array((idxs[0].start, idxs[1].start))

    elif mode == "STANDARD":
        ctr = centroid(frame)

    return ctr


if __name__ == "__main__":
    click.echo(hotspot())
