# Calibration Procedures

Procedures for VAMPIRES calibrations.

## On-sky Calibrations

In general, on-sky calibrations are reserved for stellar calibrators and are up to the observer to specify since they ultimately come out of their time budget.

### Photometric Standards

We recommend scheduling a photometric standard for each filter used if you are concerned with uncertainties <(TODO UNKNOWN)%. Otherwise, the zero points measured during ~yearly calibrations can be used. If using a coronagraph with satellite spots, we recommend scheduling a "ladder sequence", where the coronagraph mask is removed to calibrate the photometry of satellite spots.

### Astrometric Standards

TODO

### Sky Frames
One may consider taking sky frames as a proxy for dark frames considering the sky-background is below the noise floor in the optical. For more information on this case, see the _dark frame_ section below.

To take sky frames use
```
acquire <nframes> [<ncubes>] -T sky
```
which automatically sets the acquisition time and saves with the `DATA-TYP` of `SKYFLAT`.

## Daytime Calibrations

Daytime calibrations are usually taken the evening before observations, exclusively from the observer's on-sky time. For the CMOS detectors in VAMPIRES, it is important to consider the relevant noise sources when choosing which calibrations necessary for a given observation. 

### Bias Frames
Based on the detector specification of 0.45/0.25 e- RMS read noise (fast/slow mode), 0.1 e-/ADU gain, and 6 e-/px/ks dark current, the detectors are read-noise limited for observations <10 s. In this case, the difference between a dark frame and a bias frame is negligible, so one can choose to take bias frames with minimum exposure time ahead of time or dark frames matched to the science exposure times. Because dark frames implicitly include the bias signal, we recommend only taking bias frames for observations 0.2 s < tint < 10 s, where the time to take dark frames (1000 frames @ 0.2 s = ~4 min) becomes annoying, but still is below the dark noise regime (>10s).


To take bias frames use
```
vampires acq bias <nframes> [<ncubes>]
```
which automatically sets the fastest readout speed for the given mode, moves the mirror into the beam, and saves with the `DATA-TYP` of `BIAS`.

### Dark Frames
For most observations, where tint < 0.2 s < or tint > 10s (see _Bias Frames_ for more information), taking dark frames matched to each readout mode and exposure time is sufficient for bias and dark calibration. TODO: Give a recommendation for the number of dark frames based on noise properties.


To take dark frames use
```
vampires acq dark <nframes> [<ncubes>] [-t <tint>]
```
which automatically sets the acquisition time, moves the mirror into the beam, and saves with the `DATA-TYP` of `DARK`.

### Flat Frames
Fixed pattern noise dominates CMOS detectors and therefore flat frames are critical. Flat frames are matched to each readout mode, filter, and general optical layout (including polarizing optics and coronagraphs). For nights where both the polarizaing and non-polarizaing beamsplitters will be in use, for example, different flats ought to be taken. For the set of flats, make sure to take corresponding bias/dark frames matched to the readout modes and exposure times.


To take flat frames use
```
vampires acq flat <nframes> [<ncubes>] [-t <tint>] [-f <filter>]
```
which automatically sets the acquisition time, sets the filter, and saves with the `DATA-TYP` of `FLAT`.

### 😎 Polarized Flat Frames
For polarimetric observations (i.e., when the polarizing beamsplitter is in) it is important to take flat frames with a continously modulated polarized signal (e.g., a continuously rotating HWP or LP). AO188 uses a continuously rotating HWP, for which flat frames should be taken with a long enough exposure time to fully average over the polarization angles.

### Distortion Maps
Pinhole mask calibrations can be taken if requested, which allow precise astrometric calibration matched to each optical setup (i.e., filter, coronagraph) when used in conjunction with _Astrometric Calibrators_ taken on ~yearly time scales.


To take pinhole frames use
```
vampires acq comparison <nframes> [<ncubes>] [-t <tint>] [-f <filter>]
```
which automatically sets the acquisition time, sets the filter, and saves with the `DATA-TYP` of `COMPARISON`.

## Monthly/Per-run Calibrations

### Focus Measurements

Whenever there are significant optical changes, cranings, or otherwise before each observing run a focus measurement should be made. The automated parts of focusing perform the following:
1. Set the absolute focus stage using the camera 2 image
2. Fix the absolute focus stage and measure the camera 1 focus using the camera focus stage.

Assuming an F-ratio of F/21.3 the amount of distance to defocus ± λ/10 is 0.23 - 0.28 mm, so you shouldn't need better precision than ~0.2 mm on focus sweeps.

### 😎 Polarimetric Calibrations

Polarimetric calibrations should be taken close to PDI runs or when significant changes occur to the optics between AO188 and VAMPIRES. These calibrations can be done using the AO188 flat lamp and WPU, which requires summit access and, of course, access to AO188.

#### AO188 Calibrations

These are the standard polarimetric calibrations which use varying HWP and image rotator angles with a polarized input to modulate the polarized signal. These should be taken for each filter

#### QWP Calibrations

TODO 

## Advanced Calibrations

These calibrations are highly specialized and/or should only need to be done once.

### Focus Measurements

On-sky focus curves calibrate the _offset_ between the internal source focus and the on-sky focus. Assuming the standard pre-observing focusing is achieved using the internal source, we hope this offset is stable and requires minimal on-sky time.

### Detecter Calibration

Until stability can be measured, frequent photon transfer calibration simultaneously monitors the sensors for systematic defects as well as the detector gain, read noise, and dark current. The latter will be used to monitor changes over time and can be used for improved exposure time calculations. Photon transfer curves can be taken in two parts: at any time in any configuration, a dark measurement can be taken with long exposures, then the traditional photon transfer curve must be taken when behind AO188 with its flat lamp, which requires summit access.

#### Dark Transfer Curve (DTC) 

TODO

#### Photon Transfer Curve (PTC)

TODO

#### (Advanced) Photon Counting Histogram (PCH)

The detector properties can be measured from the histograms of low-signal inputs, where a comb of Poisson peaks is convolved with the read noise. This is much easier to achieve in the slow readout mode, with its 0.25 e- RMS read noise. For this measurement, the electron quanta (number of input electrons) should be close to ~1-5 e-, which corresponds to 210 - 250 ADU (with 200 ADU bias value included). TODO

### 😎 FLC Orientation Calibration

TODO

Basically put a linear polarizer in front of the FLC position (e.g., between FIRST pickoff and collimating lens). Without the FLC, determine LP axis by rotating and minimizing signal on one of the cameras. Then, orient LP to maximize light on camera 1. After that, place FLC in beam in relaxed state. Rotate in tube while keeping the light on camera 1 maximized. Verify with FLC switching that light appears to modulate between cameras.

### 😎 Telescope Diattenuation Calibration

TODO

### Zero-point Measurements

TODO

### Coronagraph Measurements

The visible Lyot coronagraph has a few measurements that only need to be calibrated once, such as the IWA or Lyot throughput.

#### Inner Working Angle / Throughput

The inner working angle (IWA) can be measured by offsetting the focal plane mask stage and measuring the relative throughput of calibration source. This can be done in any filter.
1. Start by finding exposure settings so the source is not saturating
2. For each focal plane mask (CLC2, CLC3, CLC5, and CLC7)
    1. Center the focal plane mask behind the source and record the center
    2. Offset the mask to the left/right or up/down so the star is PSF is fully exposed
    3. Step with the field stop stage and form a trace across the focal plane mask. The actual mask sizes are ~40 - 140 um, so adjust your step sizes accordingly. We recommend tracing all the way across the mask so both edges can be seen, letting you estimate the IWA from the diameter. 

Then, measure the flux in this data as a function of field stop position. Using a matched filter can help alleviate the truncation of the PSF by the windowing.  Interpolate the flux curve to find estimate the IWA as the point with 50% throughput. 

#### Lyot stop throughput

The Lyot stop geometric throughput is measured via the ratio of light transmitted by an unobscured aperture (i.e., the SCExAO pupil) versus the Lyot stop. This can be done using the internal source in any filter as long as there is access to a pupil-viewing mode. If you are using the reflected pupil beam (LOWFS beam), you can measure the flux from the `mirror` in the pupil wheel versus the Lyot stop. The throughput is `(1 - lyot_flux) / mirror_flux` (because we are measuring the _rejected_ light). If you are using a pupil-imaging lens, compare the flux between an unobscured beam and the Lyot stop, using `lyot_flux / open_flux` for the throughput.

![Screen Shot 2023-03-27 at 22 21 18](https://user-images.githubusercontent.com/14099459/228174682-5c825d51-4167-482c-98b5-3cb0b186113d.png)

### Sparse Aperture Mask Throughputs

For each of the aperture masks, the relative throughput can be measured as long as there is access to a pupil-viewing mode. The procedure is the same as for the [Lyot stop throughput](https://github.com/scexao-org/scexao-wiki/wiki/NewVAMPIRES:Calibrations#lyot-stop-throughput).