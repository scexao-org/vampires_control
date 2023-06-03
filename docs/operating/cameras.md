# Cameras

VAMPIRES uses two [Hamamatsu ORCA-Quest](https://www.hamamatsu.com/us/en/product/cameras/qcmos-cameras/C15550-20UP.html) [[manual](https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/static/sys/en/manual/C15550-20UP_IM_En.pdf)] CMOS detectors for its science cameras. There is also a UNKNOWN FLEA camera used for the pupil return beam (LOWFS beam).

## Initialization and Viewers

Each camera has its own framegrabber and viewer class which inherits a common interface from `camstack`. To start the camera framegrabber (which should not be done unless necessary)
```
cam-vcam1start # start vcam1
cam-vcam2start # start vcam2
cam-vpupcamstart # start vpupcam
```


Start each viewer from a separate terminal so their respective outputs are organized

**Main science viewers**
```
vcam1.py
```
```
vcam2.py
```
**Pupil return viewer**
```
vpupcam.py
```

## Readout Modes

VAMPIRES has two readout modes: "SLOW" and "FAST". The main differences are the maximum framerate and read noise. The slow mode uses the extra readout time to reduce the jitter in the ADC conversion, which enables sensitivity low enough for photon number resolving.

| mode | framerate (Hz) | bias (adu) | read noise (e-) | gain (e- / adu) |
|:----:|---------------:|-----------:|----------------:|----------------:|
| FAST | 500            | 200        | 0.45            | 0.11            |
| SLOW | 60             | 200        | 0.21            | 0.11            |


```{admonition} Framegrabber reset
:class: warning

When you change the readout mode the camera framegrabber has to reset, so you'll have to wait for it to restart before acquisition can resume.
```

```
set_readout <mode>
```

## Camera Modes

VAMPIRES has three camera modes to accommadate the different crops required for the multiband imaging mode

### Standard

This is the standard 3"x3" FOV crop

```
set_mode standard
```

### MBI
This is a 12"x6" crop that accommadates the four 3"x3" fields produced in the multi-band imaging (MBI) mode.


```
set_mode mbi
```

### MBI Reduced

This field crops out the 625nm field so that the maximum readout speed of the detector can still reach ~500 fps while still imaging three 3"x3" FOVs.

```
set_mode mbi-reduced
```

## Exposure time

To set the camera exposure time


```
set_tint <tint>
```

## Camera Triggering

The cameras are synchronized using a hardware micro-controller ([Metro M4 Express](https://learn.adafruit.com/adafruit-metro-m4-express-featuring-atsamd51)). This controller also synchronizes the AFLC when it is enabled. The state diagram for the camera trigger is as follows:

### AFLC Disabled

```
vampires_trigger --no-flc enable
```

```{graphviz}
digraph {
    "trigger cameras" -> {
        "wait for camera 1 ready";
        "wait for camera 2 ready";
    } -> 
    "AND" ->
    "trigger cameras";
}
```

### AFLC Enabled

```{admonition} Warning: AFLC Aging
:class: warning

We want to limit the usage of the AFLC to minimize aging effcts, so when the cameras are not acquiring we recommend leaving it disabled.
```

```
vampires_trigger --flc enable
```

```{graphviz}
digraph {
    "trigger AFLC" -> 
    "delay 20 us" ->
    "trigger cameras" -> {
        "wait for camera 1 ready";
        "wait for camera 2 ready";
    } -> 
    "AND" ->
    "trigger AFLC";
}
```

## (Advanced) Crop location

TODO

## Miscellaneous

