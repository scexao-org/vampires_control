import time
from dataclasses import dataclass

import click
import hcipy as hp
import numpy as np
import tqdm.auto as tqdm
from astropy.nddata import Cutout2D
from pyMilk.interfacing.isio_shmlib import SHM

from vampires_control.filters import get_filter_info_dict
from vampires_control.synthpsf import generate_pupil_field

from .core_algorithm import ff_iteration


@dataclass
class FastAndFurious:
    shm_name: str
    niter: int = 200
    gain: float = 0.3
    leakage: float = 0.999
    boost: float = 10
    basis: str | None = "zernike"
    num_modes: int = 50
    crop_size: int = 51  # px
    epsilon: float = 1e-3
    pixel_scale: float = 6.03  # mas/px
    pupil_angle: float = -41  # deg
    diameter: float = 7.8
    dm_shm_name: str = "dm00disp04"
    cmd_shm_name: str = "dm00disp07"

    def __post_init__(self):
        self.dark_shm_name = f"{self.shm_name}_dark"
        self.shm = SHM(self.shm_name)
        self.dark_shm = SHM(self.dark_shm_name)
        self.dark_frame = self.dark_shm.get_data()
        self.dm_shm = SHM(self.dm_shm_name)
        self.dm_cmd_shm = SHM(self.cmd_shm_name)

    def take_image(self, nframes=10):
        frames = self.shm.multi_recv_data(nframes, output_as_cube=True)
        calib_frames = frames - self.dark_frame
        mean_frame = np.mean(calib_frames, axis=0)
        # centroid and crop
        max_idx = np.unravel_index(np.argmax(mean_frame), mean_frame.shape)
        crop_frame = Cutout2D(mean_frame, (max_idx[1], max_idx[0]), self.crop_size)
        return crop_frame.data

    def prepare_fields(self):
        # generating the grids
        self.aperture = generate_pupil_field(angle=self.pupil_angle)
        self.pupil_grid = self.aperture.grid
        rad_pix = np.deg2rad(self.pixel_scale / 3.6e6)  # mas/px -> rad/px
        self.focal_grid = hp.make_uniform_grid(
            (self.crop_size, self.crop_size), (self.crop_size * rad_pix, self.crop_size * rad_pix)
        )

        # generating the propagator
        self.propagator = hp.FraunhoferPropagator(self.pupil_grid, self.focal_grid)

        # fourier transform
        self.fourier_transform = hp.make_fourier_transform(self.focal_grid, q=1, fov=1)

    def prepare_modal_basis(self):
        if self.basis == "zernike":
            self.mode_basis = hp.make_zernike_basis(
                self.num_modes, self.diameter, self.pupil_grid, 4
            )
        elif self.basis == "disk_harmonics":
            # loading the mode basis
            self.mode_basis = hp.make_disk_harmonic_basis(
                self.pupil_grid, self.num_modes, self.diameter
            )
        elif self.basis == "fourier":
            # calculating the number of modes along one axis
            Npix_foc_fourier_modes = int(np.sqrt(self.num_modes))

            fourier_grid = hp.make_uniform_grid(
                [Npix_foc_fourier_modes, Npix_foc_fourier_modes],
                [
                    2 * np.pi * Npix_foc_fourier_modes / self.diameter,
                    2 * np.pi * Npix_foc_fourier_modes / self.diameter,
                ],
            )

            self.mode_basis = hp.make_fourier_basis(self.pupil_grid, fourier_grid)

            # the number of modes could be changed so we have to reset.
            self.num_modes = len(self.mode_basis)
        elif self.basis is None:
            self.mode_basis = None
        else:
            msg = f"Invalid modal decomposition {self.basis!r}"
            raise ValueError(msg)

        if self.basis is None:
            self.mode_coefficients = None
        else:
            self.mode_coefficients = np.zeros((self.niter, len(self.mode_basis)))

    def run(self, nframes=10):
        shmkwds = self.shm.get_keywords()
        curfilt = shmkwds["FILTER01"].strip()
        filt, filt_info = get_filter_info_dict(curfilt)
        wavelength = filt_info["WAVEAVE"] * 1e-9  # nm -> m

        self.prepare_fields()
        self.prepare_modal_basis()

        # initial phase of DM
        phase_DM = np.zeros(np.prod(self.dm_shm.shape), dtype=self.dm_shm.nptype)
        # current diversity is still zero
        phase_diversity_i_rad = np.zeros_like(phase_DM)

        # fourier transform of aperture
        model_psf = self.propagator(hp.Wavefront(self.aperture, wavelength=wavelength))
        model_psf.total_power = 1
        # correcting the Fourier transform for the math of F&F
        model_psf.electric_field *= np.exp(1j * np.pi / 2)

        # taking the first image
        image = self.take_image(nframes)

        # generating the first reference image
        data_ref = hp.Field(image.ravel(), self.focal_grid)

        # initial dm command, i.e. current DM command
        dm_command = self.dm_shm.get_data()

        # ----------------------------------------------------------------------
        # running the loop
        # ----------------------------------------------------------------------

        # arrays for time and strehl measurements
        delta_times = np.zeros(self.niter)
        strehl_estimates = np.zeros(self.niter)

        # arrays for focal plane and DM command measurement
        focal_plane = np.zeros((self.niter, *self.focal_grid.shape), dtype=image.dtype)
        DM_commands = np.zeros((self.niter, *self.dm_shm.shape), dtype=self.dm_shm.nptype)
        DM_introduced = self.dm_cmd_shm.get_data()
        phase_estimate = np.zeros_like(DM_commands)

        # the teak to valley of the DM command introduced as aberration
        np.max(DM_introduced) - np.min(DM_introduced)  # micron

        # iterating the algorithm
        pbar = tqdm.trange(self.niter, desc="F&F")
        for i in pbar:
            time_1 = time.perf_counter()

            time_1_acq = time.perf_counter()
            # for the first image we dont have any diversity image
            if i == 0:
                # generating the new measurement.
                data = data_ref.copy()
            else:
                # taking new data
                data = hp.Field(self.take_image(nframes).ravel(), self.focal_grid)
            time_2_acq = time.perf_counter()
            pbar.write(f"image acquisition took {time_2_acq - time_1_acq} s")

            # saving the relevant data
            focal_plane[i, :, :] = data.shaped
            DM_commands[i, :, :] = self.dm_shm.get_data()

            time_1_ff = time.perf_counter()
            # doing fast and furious iteration
            if self.basis is None:
                phase_diversity_i_rad = ff_iteration(
                    data,
                    data_ref,
                    -phase_diversity_i_rad,
                    self.aperture,
                    model_psf,
                    self.propagator,
                    self.fourier_transform,
                    mode_basis=self.basis,
                    epsilon=self.epsilon,
                )
            else:
                phase_diversity_i_rad, modal_coeffs = ff_iteration(
                    data,
                    data_ref,
                    -phase_diversity_i_rad,
                    self.aperture,
                    model_psf,
                    self.propagator,
                    self.fourier_transform,
                    mode_basis=self.basis,
                    epsilon=self.epsilon,
                )

                self.mode_coefficients[i, :] = modal_coeffs

            time_2_ff = time.perf_counter()

            # saving the current phase estimate
            phase_estimate[i, :, :] = phase_diversity_i_rad.shaped

            pbar.write(f"F&F iteration took {time_2_ff - time_1_ff} s")

            # simple strehl estimate
            strehl_estimates[i] = np.max(data / np.sum(data)) / np.max(model_psf.power)

            pbar.write(f"Strehl estimate is {strehl_estimates[i] * 100:.01f}%")

            # multiplying this phase with gain and leak factor
            phase_diversity_i_rad *= self.gain

            # converting the measured phase to from radians to microns
            phase_diversity_i_mu = phase_diversity_i_rad * wavelength * 1e6 / (2 * np.pi)

            # applying the leakage to the previous DM command
            dm_command *= self.leak_factor

            # Adding the new estimate to the DM command.
            # also boosting the signal to account for the gain loss
            # dm_command += self.boost * self.make_dm_command(phase_diversity_i_mu)
            dm_command += self.boost * (-phase_diversity_i_mu / 2)

            # pushing the phase towards the dm
            self.dm_shm.set_data(
                dm_command.astype(self.dm_shm.nptype)
            )  # commands are in micrometers
            time.sleep(0.001)

            # setting the new reference image
            data_ref = data.copy()

            time_2 = time.perf_counter()
            delta_times[i] = time_2 - time_1


@click.command("fast_furious")
@click.option("-c", "--camera", type=int, default=1)
@click.option("-n", "--num-frames", type=int, default=10)
def main(camera: int, num_frames: int):
    if camera == 1:
        shm = "vcam1"
    elif camera == 2:
        shm = "vcam2"
    ff = FastAndFurious(shm)
    ff.run(num_frames)


if __name__ == "__main__":
    main()
