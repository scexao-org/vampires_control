import os
import warnings
from datetime import datetime, timezone

import click
import numpy as np
import paramiko
import sep
from astropy.nddata import Cutout2D
from pyMilk.interfacing.isio_shmlib import SHM

from .centroid import dft_centroid
from .synthpsf import create_synth_psf


def find_peak(image, xc, yc, boxsize, oversamp=8):
    """
    usage: peak = find_peak(image, xc, yc, boxsize)
    finds the subpixel peak of an image

    image: an image of a point source for which we would like to find the peak
    xc, yc: approximate coordinate of the point source
    boxsize: region in which most of the flux is contained (typically 20)
    oversamp: how many times to oversample the image in the FFT interpolation in order to find the peak

    :return: peak of the oversampled image

    Marcos van Dam, October 2022, translated from IDL code of the same name
    """

    boxhalf = np.ceil(boxsize / 2.0).astype(int)
    boxsize = 2 * boxhalf
    ext = np.array(boxsize * oversamp, dtype=int)

    # need to deconvolve the image by dividing by a sinc in order to "undo" the sampling
    fftsinc = np.zeros(ext)
    fftsinc[0:oversamp] = 1.0

    sinc = (
        boxsize
        * np.fft.fft(fftsinc, norm="forward")
        * np.exp(
            1j * np.pi * (oversamp - 1) * np.roll(np.arange(-ext / 2, ext / 2), int(ext / 2)) / ext
        )
    )
    sinc = sinc.real
    sinc = np.roll(sinc, int(ext / 2))
    sinc = sinc[int(ext / 2) - int(boxsize / 2) : int(ext / 2) + int(boxsize / 2)]
    sinc2d = np.outer(sinc, sinc)

    # define a box around the center of the star
    blx = np.floor(xc - boxhalf).astype(int)
    bly = np.floor(yc - boxhalf).astype(int)

    # make sure that the box is contained by the image
    blx = np.clip(blx, 0, image.shape[0] - boxsize)
    bly = np.clip(bly, 0, image.shape[1] - boxsize)

    # extract the star
    subim = image[blx : blx + boxsize, bly : bly + boxsize]

    # deconvolve the image by dividing by a sinc in order to "undo" the pixelation
    fftim1 = np.fft.fft2(subim, norm="forward")
    shfftim1 = np.roll(fftim1, (-boxhalf, -boxhalf), axis=(1, 0))
    shfftim1 /= sinc2d  # deconvolve

    zpshfftim1 = np.zeros((oversamp * boxsize, oversamp * boxsize), dtype="complex64")
    zpshfftim1[0:boxsize, 0:boxsize] = shfftim1

    zpfftim1 = np.roll(zpshfftim1, (-boxhalf, -boxhalf), axis=(1, 0))
    subimupsamp = np.fft.ifft2(zpfftim1, norm="forward").real

    peak = np.nanmax(subimupsamp)

    return peak


def measure_strehl_otf(image, psf_model):
    im_mtf = np.abs(np.fft.fft2(image))
    psf_mtf = np.abs(np.fft.fft2(psf_model))

    im_mtf_norm = im_mtf / np.max(im_mtf)
    psf_mtf_norm = psf_mtf / np.max(psf_mtf)

    im_volume = np.mean(im_mtf_norm)
    psf_volume = np.mean(psf_mtf_norm)
    return im_volume / psf_volume


def measure_strehl(image, psf_model, pos=None, phot_rad=0.5, peak_search_rad=0.1, pxscale=5.9):
    ## Step 1: find approximate location of PSF in image
    refined_center = dft_centroid(image, psf_model, center=pos)

    ## Step 2: Calculate peak flux with subsampling and flux
    aper_rad_px = phot_rad / (pxscale * 1e-3)
    image_flux, image_fluxerr, _ = sep.sum_circle(
        image.astype("=f4"),
        (refined_center[1],),
        (refined_center[0],),
        aper_rad_px,
        err=np.sqrt(np.maximum(image, 0)),
    )
    peak_search_rad_px = peak_search_rad / (pxscale * 1e-3)
    image_peak = find_peak(image, refined_center[0], refined_center[1], peak_search_rad_px)

    ## Step 3: Calculate flux of PSF model
    # note: our models are alrady centered
    model_center = np.array(psf_model.shape[-2:]) / 2 - 0.5
    # note: our models have zero background signal
    model_flux, model_fluxerr, _ = sep.sum_circle(
        psf_model.astype("=f4"),
        (model_center[1],),
        (model_center[0],),
        aper_rad_px,
        err=np.sqrt(np.maximum(psf_model, 0)),
    )
    model_peak = find_peak(psf_model, model_center[0], model_center[1], peak_search_rad_px)

    ## Step 4: Calculate Strehl via normalized ratio
    image_norm_peak = image_peak / image_flux[0]
    model_norm_peak = model_peak / model_flux[0]
    strehl = image_norm_peak / model_norm_peak
    return strehl


def take_dark(data_shm_name: str, n=100):
    data_shm = SHM(data_shm_name)
    dark_shm = SHM(f"{data_shm_name}_dark", (data_shm.shape, "f4"))
    data = data_shm.multi_recv_data(n, outputFormat=n)
    mean_frame = np.nanmedian(data, axis=0)
    dark_shm.set_data(mean_frame.astype("f4"))


def get_mbi_cutout(data, camera: int, field: str, reduced: bool = False):
    hy, hx = np.array(data.shape[-2:]) / 2 - 0.5
    # use cam2 as reference
    match field:
        case "F610":
            x = hx * 0.25
            y = hy * 1.5
        case "F670":
            x = hx * 0.25
            y = hy * 0.5
        case "F720":
            x = hx * 0.75
            y = hy * 0.5
        case "F760":
            x = hx * 1.75
            y = hy * 0.5
        case _:
            msg = f"Invalid MBI field {field}"
            raise ValueError(msg)
    if reduced:
        y *= 2
    # flip y axis for cam 1 indices
    if camera == 1:
        y = data.shape[-2] - y
    return Cutout2D(data, position=(x, y), size=500, mode="partial")


def measure_strehl_mbi(image, cam: int, pxscale: float = 5.9, **kwargs):
    filters = ("F610", "F670", "F720", "F760")
    results = {}
    for _i, filt in enumerate(filters):
        psf = create_synth_psf(filt, 201, pixel_scale=pxscale)
        cutout = get_mbi_cutout(image, cam, filt)
        results[filt] = measure_strehl(cutout.data, psf, pxscale=pxscale, **kwargs)
        print(f"{filt}: measured Strehl {results[filt]*100:.01f}%")
    return results


def measure_strehl_shm(shm_name: str, psf=None, nave=10, pxscale=5.9, **kwargs):
    shm = SHM(shm_name)
    # dark_shm = SHM(f"{shm_name}_dark")
    # dark = dark_shm.get_data()
    shmkwds = shm.get_keywords()

    frames = shm.multi_recv_data(nave, output_as_cube=True)
    image = np.mean(frames.astype("f4") - 200, axis=0)
    if shm.shape[0] > 1000 and shm.shape[1] > 2000:
        return measure_strehl_mbi(image, cam=shmkwds["U_CAMERA"], pxscale=pxscale, **kwargs)

    curfilt = shmkwds["FILTER01"].strip()

    # return image
    if psf is None:
        psf = create_synth_psf(curfilt, 201, pixel_scale=pxscale)
    if shmkwds["U_CAMERA"] == 1:
        psf = np.flipud(psf)
    return measure_strehl(image, psf, pxscale=pxscale, **kwargs)


@click.command("vampires_strehl")
@click.argument("stream", type=click.Choice(["vcam1", "vcam2"]))
def vampires_strehl(stream: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        measure_strehl_shm(stream)


@click.command("vampires_strehl_monitor")
@click.argument("stream", type=click.Choice(["vcam1", "vcam2"]))
def vampires_strehl_monitor(stream: str):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()
    client.connect(
        "scexao5",
        username="scexao",
        disabled_algorithms={"pubkeys": ("rsa-sha2-256", "rsa-sha2-512")},
    )
    while True:
        stdin, stdout, stderr = client.exec_command(
            f"/home/scexao/miniforge3/envs/vampires_control/bin/vampires_strehl {stream}"
        )
        output = "".join(stdout.readlines())
        os.system("cls" if os.name == "nt" else "clear")
        print(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%s"))
        print()
        print(output)


if __name__ == "__main__":
    vampires_strehl()
