
# Instrument Calibration Procedures

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
