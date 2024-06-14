# Calibration Procedures

Procedures for VAMPIRES calibrations.

## Nightly / Pre-observing Calibrations

The following calibrations should be taken with every observation for each readout mode and crop planned during the observation. For all of these calibrations we recommend taking 1000 frames, minimum. Even in multiband mode, a single 1000-frame cube is okay; it will be a large file, but you only need to open it once to make the master calibration file.

### Flat frames

Flat frames are critical for calibrating CMOS images due to the variance in gain from pixel to pixel. Flat frames are not _strictly_ necessary for polarimetric differential imaging because the frame differencing will remove the fixed pattern noise, but we still recommend taking them for all observations.

```{admonition} Coronagraph masks
:class: warning

Because we align the coronagraph masks by moving the mask in the focal plane, it is difficult to take useful flats with the coronagraph mask in. We recommend taking standard flats with the fieldstop in addition to well-centered coronagraph mask flats.
```

To take flat frames, make sure the NsIR cal source is in- we recommend using **14V** and **3A** for the lamp settings. At these settings, there should be plenty of signal in any filter with 100 ms exposure times

```
sonne $ set_tint 0.1
sonne $ vampires_datatype flat
```

then [log the data to gen2](logging).

### Pinhole frames

Pinhole frames should be taken right after flats by inserting the pinhole mask

```
scexao2 $ src_fib pinhole &
```
and then defocusing the DM with `manual_zernike`
```
scexao2 $ manual_zernike &
```
To do this, manually adjust the focus slider to +60 nm (as a starting point)

The datatype for pinholes is `COMPARISON`

```
sonne $ vampires_datatype comparison
```

### Dark frames

For dark frames just match the exposure time of the flats and pinholes
```
sonne $ set_tint 0.1
```
and set the datatype
```
sonne $ vampires_datatype dark
```

## Post-observing Calibrations

### Dark frames

```{admonition} 🧪: Automatated script
There is a script for automatically logging all necessary dark frames AFTER an observation has completed. This is convenient to have a perfect match for all the science data, but be aware the script is somewhat experimental.
```
First, prepare VAMPIRES for darks by putting the pupil mirror in
```
$ vampires_mask mirror
```
then on `scexao5` activate the `vampires_control` environment
```
scexao5 $ conda activate vampires_control
```
and enter the night's saved data directory
```
scexao5 $ cd /mnt/fuuu/ARCHIVED_DATA/$(date -u +%Y%m%d)
```
and run the `vampires_autodarks` script
```
scexao5 $ vampires_autodarks -n 1000 .
```
feel free to change the number of frames per dark with the `-n` flag.

## On-sky Calibrations

In general, on-sky calibrations are reserved for stellar calibrators and are up to the observer to specify since they ultimately come out of their time budget.

### Sky Frames

Sky frames are not strictly necessary for all VAMPIRES observations-- we estimate that the sky background at its brightest is ~18 mag/sq.arcsec, which is not the limiting noise term for exposure times less than 1 second. One may consider taking sky frames as a proxy for dark frames, though. Sky frames have the data type `SKYFLAT`

```
sonne $ vampires_datatype skyflat
```

### Photometric Standards

We recommend scheduling a photometric standard for each filter used if you are concerned with photometric accuracy. If using a coronagraph with satellite spots, we recommend scheduling a "ladder sequence", where the coronagraph mask is removed to calibrate the photometry of satellite spots. Flux standard stars and ladder sequences have the data type `STANDARD`

```
sonne $ vampires_datatype standard
```

### Astrometric Standards

We recommend observing an astrometric standard if you are concerned with astrometric accuracy. We have a list of binary stars with high-precision orbital ephemerides which can be used for VAMPIRES observations. This calibration should only need to be done once per run, if desired. The data type for astrometric standards is the normal `OBJECT`

```
sonne $ vampires_datatype object
```