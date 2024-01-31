import numpy as np
import scipy
from pyMilk.interfacing.isio_shmlib import SHM

from .synthpsf import create_synth_psf


def rebin(array, factor, func=None):
    from numpy.lib.stride_tricks import as_strided

    dim = array.ndim
    if np.isscalar(factor):
        factor = dim * (factor,)
    elif len(factor) != dim:
        msg = f"Length of factor must be {len(factor)!r} must be {dim!r}"
        raise ValueError(msg)

    for f in factor:
        if f != int(f):
            msg = f"Factor must be an int or tuple of ints, got {f!r}"
            raise ValueError(msg)

    new_shape = []
    new_strides = []
    for sh, st, f in zip(array.shape, array.strides, factor, strict=True):
        new_shape.append(sh // f)
        new_strides.append(st * f)
    new_shape.extend(factor)
    new_strides.extend(array.strides)

    new_array = as_strided(array, shape=new_shape, strides=new_strides)
    return np.mean(new_array, axis=tuple(range(-dim, 0)))


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


def measure_strehl(im, psf0, pos=None, photometryradius=0.5, peakradius=0.1, pixelscale=6.035e-3):
    # if the position of the star is not provided, then define it to be the location of the maximum value of the image
    if pos is None:
        # find the location of the maximum value of the image
        # maxloc = np.where(im == np.amax(im))
        maxloc = np.where(im == np.nanmax(im))
        xc = maxloc[0][0]
        yc = maxloc[1][0]
    else:
        xc = pos[0]
        yc = pos[1]

    # compute the center more accurately
    sz = im.shape
    x, y = np.meshgrid(np.arange(sz[0]) - yc, np.arange(sz[1]) - xc)
    peakradius_pixels = int(2 * np.ceil(0.5 * peakradius / pixelscale))
    central_region = np.sqrt(x**2 + y**2) < peakradius_pixels
    # xc,yc = scipy.ndimage.center_of_mass(im*central_region)
    cntl_rgn = im * central_region
    cntl_rgn[np.isnan(cntl_rgn)] = 0.0
    xc, yc = scipy.ndimage.center_of_mass(cntl_rgn)

    # calculate the flux of the image
    x, y = np.meshgrid(np.arange(sz[0]) - yc, np.arange(sz[1]) - xc)
    central_region = np.sqrt(x**2 + y**2) < photometryradius / pixelscale
    # flux = np.sum(im*central_region)
    flux = np.nansum(im * central_region)

    peak = find_peak(im, xc, yc, peakradius_pixels)

    # now repeat for the diffraction-limited PSF
    maxloc0 = np.where(psf0 == np.amax(psf0))
    xc0 = maxloc0[0][0]
    yc0 = maxloc0[1][0]

    sz0 = psf0.shape
    x, y = np.meshgrid(np.arange(sz0[0]) - yc0, np.arange(sz0[1]) - xc0)
    central_region = np.sqrt(x**2 + y**2) < peakradius_pixels
    xc0, yc0 = scipy.ndimage.center_of_mass(
        psf0 * central_region
    )  # more accurate center coordinates

    x, y = np.meshgrid(np.arange(sz0[0]) - yc0, np.arange(sz0[1]) - xc0)
    central_region0 = np.sqrt(x**2 + y**2) < photometryradius / pixelscale
    flux0 = np.sum(psf0 * central_region0)

    peak0 = find_peak(psf0, xc0, yc0, peakradius_pixels)
    strehl = (peak / flux) / (peak0 / flux0)

    return strehl


def take_dark(data_shm_name: str, n=100):
    data_shm = SHM(data_shm_name)
    dark_shm = SHM(f"{data_shm_name}_dark", (data_shm.shape, "f4"))
    mean_frame = data_shm.multi_recv_data(n, outputFormat=n).mean(axis=0)
    dark_shm.set_data(mean_frame.astype("f4"))


def measure_strehl_shm(shm_name: str, nave=10, **kwargs):
    shm = SHM(shm_name)
    dark_shm = SHM(f"{shm_name}_dark")
    dark = dark_shm.get_data()
    shmkwds = shm.get_keywords()
    curfilt = shmkwds["FILTER01"].strip()
    psf = create_synth_psf(curfilt)

    frames = shm.multi_recv_data(nave, outputFormat=2)
    image = np.mean(frames - dark, axis=0)
    return measure_strehl(image, psf)
