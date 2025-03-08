import warnings

import matplotlib.pyplot as plt
import numpy as np
import sep
from astropy.modeling import fitting, models
from astropy.nddata import Cutout2D
from matplotlib import colors
from skimage.registration import phase_cross_correlation


def guess_mbi_centroid(frame, field, camera=1):
    hy, hx = np.array(frame.shape) / 2 - 0.5
    # use cam2 as reference
    if field == "F610":
        x = hx * 0.25
        y = hy * 1.5
    elif field == "F670":
        x = hx * 0.25
        y = hy * 0.5
    elif field == "F720":
        x = hx * 0.75
        y = hy * 0.5
    elif field == "F760":
        x = hx * 1.75
        y = hy * 0.5
    else:
        msg = f"Invalid MBI field {field}"
        raise ValueError(msg)
    # flip y axis for cam 1 indices
    if camera == 1:
        y = frame.shape[-2] - y
    inds = cutout_slice(frame, window=500, center=(y, x))
    cutout = frame[inds]
    cy, cx = np.unravel_index(np.nanargmax(cutout), cutout.shape)

    return cy + inds[0].start, cx + inds[1].start


def cutout_slice(frame, window, center=None):
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
    if center is None:
        center = np.array(frame.shape) / 2 - 0.5
    half_width = np.asarray(window) / 2
    Ny, Nx = frame.shape[-2:]
    lower = np.maximum(0, np.round(center - half_width), dtype=int, casting="unsafe")
    upper = np.minimum((Ny, Nx), lower + np.asarray(window), dtype=int, casting="unsafe")
    return np.s_[lower[0] : upper[0], lower[1] : upper[1]]


@models.custom_model
def EllMoffat(x, y, x0=0, y0=0, alpha=2, gammax=2, gammay=2, bkg=0, amp=1, theta=0):
    costh = np.cos(theta)
    sinth = np.sin(theta)
    # x^2 term
    A = (costh / gammax) ** 2 + (sinth / gammay) ** 2
    # y^2 term
    B = (sinth / gammax) ** 2 + (costh / gammay) ** 2
    # xy term
    C = 2 * sinth * costh * (1 / gammax**2 - 1 / gammay**2)
    dx = x - x0
    dy = y - y0
    model = bkg + amp * (1 + A * dx**2 + B * dy**2 + C * dx * dy) ** (-alpha)
    return model


def _get_fwhm(self) -> dict[str, float]:
    corr_fact = 2 * np.sqrt(2 ** (1 / self.alpha) - 1)
    fwhmx = self.gammax * corr_fact
    fwhmy = self.gammay * corr_fact
    rms = np.sqrt(np.mean(fwhmx**2 + fwhmy**2 + fwhmx * fwhmy))
    return dict(x=fwhmx, y=fwhmy, rms=rms)


def _get_flux(self, data):
    fwhms = self.get_fwhm()
    sep_xs = (self.x0,)
    sep_ys = (self.y0,)
    _data = data.byteswap().newbyteorder()
    if fwhms["x"] > fwhms["y"]:
        a = fwhms["x"]
        b = fwhms["y"]
        theta = self.theta
    else:
        a = fwhms["y"]
        b = fwhms["x"]
        theta = self.theta + np.pi / 2
    if theta > np.pi / 2:
        theta -= np.pi
    flux, fluxerr, flag = sep.sum_ellipse(
        _data, sep_xs, sep_ys, a, b, theta, gain=0.1, mask=~np.isfinite(_data)
    )
    return flux, fluxerr


EllMoffat.get_fwhm = _get_fwhm
EllMoffat.get_flux = _get_flux

ELL_MOFFAT = EllMoffat()
ELL_MOFFAT.amp.min = 0
ELL_MOFFAT.alpha.min = 0
ELL_MOFFAT.gammax.min = 0.5
ELL_MOFFAT.gammax.max = 20
ELL_MOFFAT.gammay.min = 0.5
ELL_MOFFAT.gammay.max = 20
ELL_MOFFAT.theta.min = -np.pi / 4
ELL_MOFFAT.theta.max = np.pi / 4


LMLSQ_FITTER = fitting.LevMarLSQFitter()


def _fit_plot_callback(cutout, init_model, fit_model):
    fig, axes = plt.subplots(2, 2, sharex="all", sharey="all", figsize=(6, 6))
    bbox = cutout.bbox_original
    ys, xs = np.ogrid[cutout.slices_original[0], cutout.slices_original[1]]
    extent = [*bbox[1], *bbox[0]]
    im_kwargs = {
        "cmap": "bone",
        "norm": colors.LogNorm(vmin=np.nanmin(cutout.data), vmax=np.nanmax(cutout.data)),
        "extent": extent,
    }
    # top left: input data
    axes[0, 0].imshow(cutout.data, **im_kwargs)
    axes[0, 0].set_title("Data")
    # top right: init model
    axes[0, 1].imshow(init_model(xs, ys), **im_kwargs)
    axes[0, 1].set_title("Initial model")
    # bottom left: fit model
    model_image = fit_model(xs, ys)
    axes[1, 0].imshow(model_image, **im_kwargs)
    axes[1, 0].set_title("Fit model")
    # bottom right: fit residual
    resid = cutout.data - model_image
    axes[1, 1].imshow(
        resid, extent=extent, norm=colors.CenteredNorm(halfrange=np.nanmax(cutout.data)), cmap="bwr"
    )
    axes[1, 1].set_title("Residual")

    axes[0, 0].set_ylabel("y")
    axes[1, 0].set_ylabel("y")
    axes[1, 0].set_xlabel("x")
    axes[1, 1].set_xlabel("x")
    fig.tight_layout()
    return axes


def fit_moffat_psf(data, error=None, center=None, window=30, plot: bool = False) -> EllMoffat:
    if center is None:
        center = np.unravel_index(np.nanargmax(data), data.shape)

    cutout = Cutout2D(data, center[::-1], window, mode="partial")
    bbox = cutout.bbox_original
    model = ELL_MOFFAT
    model.x0 = center[-1]
    model.y0 = center[-2]
    model.amp = np.nanmax(cutout.data)
    model.x0.min = bbox[1][0]
    model.y0.min = bbox[0][0]
    model.x0.max = bbox[1][1]
    model.y0.max = bbox[0][1]
    if error is None:
        weights = None
    else:
        err_cutout = Cutout2D(error, center[::-1], window, mode="partial")
        weights = 1 / err_cutout.data

    ys, xs = np.mgrid[cutout.slices_original[0], cutout.slices_original[1]]
    fit_model = LMLSQ_FITTER(
        model, xs, ys, cutout.data, weights=weights, filter_non_finite=True, maxiter=1000
    )
    if plot:
        _fit_plot_callback(cutout, model, fit_model)
    return fit_model


def model_centroid(data, center=None, **kwargs):
    model = fit_moffat_psf(data, center=center, **kwargs)
    return (model.y0.value, model.x0.value)


def dft_centroid(data, psf, center=None, window=20):
    if center is None:
        center = np.unravel_index(np.nanargmax(data), data.shape)
    cutout_data = Cutout2D(data, center[::-1], window, mode="partial")
    psf_center = np.array(psf.shape[-2:]) / 2 - 0.5
    cutout_psf = Cutout2D(psf, psf_center[::-1], window, mode="partial")
    shift, _, _ = phase_cross_correlation(
        cutout_psf.data.astype("=f4"),
        cutout_data.data.astype("=f4"),
        upsample_factor=30,
        normalization=None,
    )
    refined_center = center + shift

    if np.any(np.abs(refined_center - center) > 10):
        msg = f"PSF centroid appears to have failed, got {refined_center!r}"
        warnings.warn(msg, stacklevel=2)
    return refined_center
