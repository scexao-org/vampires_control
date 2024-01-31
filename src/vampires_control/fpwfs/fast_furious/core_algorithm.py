# setting the max number of processors that can be used.
import hcipy as hp
import numpy as np


def regularsplit(p):
    """
    Split array p by swapping the axis.

    seems to work for both real and complex arrays

    """

    Npix = int(np.sqrt(len(p)))

    grid = p.grid.copy()

    # reshape p for even and odd decomposition
    p = np.reshape(p, (Npix, Npix))

    # decomposing in even and odd parts
    p_e = (p + np.flip(np.flip(p, axis=1), axis=0)) / 2
    p_o = (p - np.flip(np.flip(p, axis=1), axis=0)) / 2

    # going back to field
    p_e = hp.Field(p_e.ravel(), grid)
    p_o = hp.Field(p_o.ravel(), grid)

    return p_e, p_o


def fouriersplit(p, fourier_transform):
    """Decomposes a given (complex) array p into its odd and even constituents using FT symmetry

    NB - Can be extended to arbitrary complex array

    Based on the code of M. Wilby.

    Parameters
    ----------
    p : Field
        temp
    fourier_transform : FourierTransform
        temp

    Returns
    -------
    p_e
        temp
    p_o
        temp
    """

    P_r = fourier_transform.forward(
        (p.real).astype(np.complex128)
    )  # Split by real/imaginary part of input
    P_i = fourier_transform.forward((1j * p.imag).astype(np.complex128))

    p_e = fourier_transform.backward(P_r.real + 1j * P_i.imag)  # Even complex array
    p_o = fourier_transform.backward(1j * P_r.imag + P_i.real)  # Odd complex array

    return p_e, p_o


def solve_yv(p, a, strehl, fourier_transform, epsilon=1e-2):
    """Estimates the odd component and the absolute value of the even component.

    Based on the algorithm of C.U. Keller (ref) and the code of M. Wilby (ref).

    Parameters
    ----------
    p : Field
        temp
    a : Wavefront
        temp
    strehl : float
        temp
    y : Wavefront
        temp
    fourier_transform : FourierTransform
        temp
    epsilon : float
        temp

    Returns
    -------
    y
        temp
    v_abs
        temp
    """
    # first we find the even and odd parts of the data
    p_e, p_o = fouriersplit(p, fourier_transform)  # regularsplit(p)#

    # finding the odd part of the phase
    y = hp.Wavefront(a.electric_field * p_o / (2 * a.power + epsilon))

    # finding the absolute value of the even part
    v_abs = hp.Wavefront(
        np.sqrt(np.abs(p_e - (strehl * a.power + y.power))) / np.sqrt(p.grid.weights)
    )

    return y, v_abs


def sign_v(p_1, p_2, phi_d, y, A, propagator, fourier_transform, correction_factor, wavelength):
    """Estimates the sign of the even component.

    Based on the algorithm of C.U. Keller (ref) and the code of M. Wilby (ref).

    Parameters
    ----------
    p_1 : Field
        temp
    p_2 : Field
        temp
    phi_d : Field
        temp
    y : Wavefront
        temp
    A : Field
        temp
    propagator : Propagator
        temp
    fourier_transform : FourierTransform
        temp
    propagator : float
        temp

    Returns
    -------
    v_sign
        temp
    """

    # first we find the even arts of the data
    p_e_1, _ = fouriersplit(p_1, fourier_transform)  # regularsplit(p_1)#
    p_e_2, _ = fouriersplit(p_2, fourier_transform)  # regularsplit(p_2)#

    # finding the phase diversity electric field
    p_d = propagator(hp.Wavefront(A * phi_d, wavelength=wavelength))

    # correcting the Fourier transform for the math of F&F
    p_d.electric_field *= np.exp(1j * np.pi / 2)

    # scaling to the correct intensity
    p_d.electric_field /= correction_factor

    # splitting that into the even and odd parts
    v_d, y_d = fouriersplit(p_d, fourier_transform)  # regularsplit(p_d.electric_field)#

    v_d = hp.Wavefront(v_d)
    y_d = hp.Wavefront(y_d)

    # finding v
    v = (
        (
            p_e_2
            - p_e_1
            - (v_d.power + y_d.power + 2 * y.electric_field * y_d.electric_field * p_1.grid.weights)
        )
        / (2 * v_d.electric_field * np.sqrt(p_1.grid.weights))
    ) / np.sqrt(p_1.grid.weights)

    # only using the sign
    v_sign = np.sign(v)

    return v_sign


def ff_iteration(
    data_i,
    data_ref,
    phi_i,
    aper,
    model_psf,
    propagator,
    fourier_transform,
    mode_basis=None,
    epsilon=1e-2,
):
    """Calculates the wavefront estimate for one iteration of the Fast&Furious algorithm.

    Based on the algorithm of C.U. Keller (ref) and the code of M. Wilby (ref).

    Parameters
    ----------
    data_i : Field
        Image with the phase diversity.
    data_ref : Field
        Image without the phase diversity.
    phi_i : Field
        The previous DM command that will be used as diversity. Expected as phase in radians.
    aper : Field
        The aperture of the telescope in use.
    model_psf : Wavefront
        Nominal focal plane electric field of the given aperture when no aberrations present.
    propagator : Propagator
        The propagator that will transform from the pupil plane to the focal plane.
    fourier_transform : FourierTransform
    mode_basis : ModeBasis
        The mode basis on which the output phase will be projected and reconstructed. This is
        convenient with spatial filtering.
    epsilon : float
        Parameter for regularization when calculating y, the odd component.

    Returns
    -------
    phi_FF
        Field with the phase estimate after this F&F iteration.
    """
    # copying the input to make sure we do not mess with it too much
    data_i = data_i.copy()
    data_ref = data_ref.copy()

    # circular aperture to make phases nice
    circ_aper = hp.circular_aperture(7.8)(aper.grid)  # aper > 0

    # the correction factor to correct all the field with
    correction_factor = 1  # np.sqrt(a.total_power)

    # making sure that the power of a is 1 (MUST BE SET AFTER FOURIER TRANSFORM!)
    # a.total_power = 1

    # scaling epsilon with max of a
    epsilon *= np.max(model_psf.power)

    # rescaling data such that the sum = 1
    data_i *= model_psf.power.max() / data_i.max()

    # rescaling reference data in the same way
    data_ref *= model_psf.power.max() / data_ref.max()

    # Estimate for noise level by looking at the pixels in the corners
    max_pix = 10
    std_noise = np.array(
        [
            data_i.shaped[:max_pix, :max_pix],
            data_i.shaped[:max_pix, -max_pix:],
            data_i.shaped[-max_pix:, :max_pix],
            data_i.shaped[-max_pix:, -max_pix:],
        ]
    )

    # correction for any PSF structure??
    std_noise -= np.median(data_i)

    # Bringing it to contrast units
    std_noise /= np.max(data_i)

    std_noise = np.std(std_noise)

    # simple estimate of the current strehl ratio
    strehl = 1  # np.max(data_i) / np.max(a.power)

    # Calculate odd/even focal-plane terms using the reference data
    y, v_abs = solve_yv(data_ref, model_psf, strehl, fourier_transform, epsilon)

    # finding the sign of v
    if np.any(phi_i):
        # If there is phase diversity info we can give a good estimate of the sign
        v_sign = sign_v(
            data_ref,
            data_i,
            phi_i,
            y,
            aper,
            propagator,
            fourier_transform,
            correction_factor,
            model_psf.wavelength,
        )
    else:
        # Phase diversity info not available - take signs of reference field
        v_sign = np.sign(model_psf.electric_field)

    # Combining all the information on v.
    v = hp.Wavefront(v_sign * v_abs.electric_field, wavelength=model_psf.wavelength)

    # adding both components together to get the total electric field estimate
    tot = hp.Wavefront(v.electric_field - 1j * y.electric_field, wavelength=model_psf.wavelength)

    # Finding the eventual DM command
    phi_FF = propagator.backward(tot).imag * circ_aper  # * aper

    if mode_basis is not None:
        # decompose measured phase on mode basis
        modal_coeffs = modal_decomposition(phi_FF, mode_basis)

        # reconstructing the phase excluding any measured piston tip/tilt
        phi_FF = hp.Field(
            np.sum(modal_coeffs[:, np.newaxis] * np.array(mode_basis), axis=0), aper.grid
        )

    # removing pistion
    phi_FF[circ_aper == 1] -= np.mean(phi_FF[circ_aper == 1])

    phi_FF *= circ_aper  # aper

    if mode_basis is None:
        modal_coeffs = None
    return phi_FF, modal_coeffs


def modal_decomposition(phase, basis):
    # decomposes a wavefront on a certain basis.
    coeffs = np.dot(hp.inverse_truncated(basis.transformation_matrix), phase)
    return coeffs
