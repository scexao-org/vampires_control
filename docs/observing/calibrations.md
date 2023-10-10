# Calibration Procedures

Procedures for VAMPIRES calibrations.

## Nightly / Pre-observing Calibrations

The following calibrations should be taken with every observation for each readout mode and crop planned  during the observation.

### Flat frames

Flat frames are critical for calibrating CMOS images due to the variance in gain from pixel to pixel. Flat frames are not _strictly_ necessary for polarimetric differential imaging because the frame differencing will remove the fixed pattern noise, but we still recommend taking them for all observations.

```{admonition} Coronagraph masks
:class: warning

Because we align the coronagraph masks by moving the mask in the focal plane, it is difficult to take useful flats with the coronagraph mask in. We recommend taking standard flats with the fieldstop in and only using those.
```

To take flat frames, make sure the NsIR cal source is in- we recommend using **14V** and **3A** for the lamp settings. At these settings, there should be plenty of signal in any filter with 100 ms exposure times

```
sonne $ set_tint 0.1
sonne $ set_datatype flat
```

### Dark frames

For dark frames just match the exposure time of the flats and pinholes
```
sonne $ set_tint 0.1
```

## On-sky Calibrations

In general, on-sky calibrations are reserved for stellar calibrators and are up to the observer to specify since they ultimately come out of their time budget.

### Photometric Standards

We recommend scheduling a photometric standard for each filter used if you are concerned with uncertainties <5%. Otherwise, the zero points measured during ~yearly calibrations can be used. If using a coronagraph with satellite spots, we recommend scheduling a "ladder sequence", where the coronagraph mask is removed to calibrate the photometry of satellite spots.

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
