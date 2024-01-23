# Cameras

VAMPIRES uses two [Hamamatsu ORCA-Quest](https://www.hamamatsu.com/us/en/product/cameras/qcmos-cameras/C15550-20UP.html) [[manual](https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/static/sys/en/manual/C15550-20UP_IM_En.pdf)] CMOS detectors for its science cameras. There is also a UNKNOWN FLEA camera used for the pupil return beam (pupil cam).

## Initialization and Viewers

Each camera has its own framegrabber and viewer class which inherits a common interface from `camstack`.

### VCAM1 and VCAM2
```{admonition} SSH for VNC
:class: tip

Make sure to forward your display over SSH if running from the VAMPIRES VNC

    $ ssh -Y sc5
```

To start the camera framegrabber (which should not be done unless necessary)
```
scexao5 $ camstart vcam1 # start vcam1
scexao5 $ camstart vcam2 # start vcam2
```

and to start the pygame viewers
```
scexao5 $ vcam1 & # cam 1 viewer
scexao5 $ vcam2 & # cam 2 viewer
```

```{admonition} Raw SHM Viewer
:class: info

If you want to see the raw data (useful to see MBI frames without cropping), use one of the generic viewers with the appropriate SHM name (`vcam1`/`vcam2`)

    scexao5 $ anycam vcam1 # pygame viewer
    scexao5 $ shmImshow.py vcam1 # qt viewer
```

### VPUPCAM

```
sonne $ camstart vpupcam # start vpupcam
```

```
sonne $ vpupcam &
```

## Camera Crops and Modes

VAMPIRES has two readout modes: "Slow" and "Fast". The main differences are the maximum framerate and read noise. The slow mode uses the extra readout time to reduce the jitter in the ADC conversion, which enables sensitivity low enough for photon number resolving. The noise characteristics of the cameras are only related to the readout mode. The timing characteristics, however, are dependent on the camera crop and trigger modes with a somewhat complicated relationship that also depends on the readout mode.


| Mode | Cam | Gain (e-/adu) | RN (e-) | DC (e-/px/s) |
| - | - | - |- | - |
| Fast | 1 | 0.103 | 0.403 | 3.6e-3 |
| Fast | 2 | 0.103 | 0.399 | 3.5e-3 |
| Slow | 1 | 0.105 | 0.245 | 3.6e-3 |
| Slow | 2 | 0.105 | 0.220 | 3.5e-3 |

### Photon Transfer Curves

These photon transfer curves were fit with the use of frame-differencing to remove the fixed pattern noise. The bias is not estimated from any light frames, but from a bias frame directly after fitting the gain.

```{image} ptc_fast.png
:width: 800 px
```

```{image} ptc_slow.png
:width: 800 px
```

**Note:** The minimum detector integration time determines the saturation limit for VAMPIRES. In fast readout mode, the minimum is the minimum for four rows to read out. At this speed, that means there is an extreme rolling shutter effect, so each group of four rows will be simultaneous but no group of 4 will overlap in time.

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
sonne $ set_mode standard
```

There are also some reduced crop sizes
```
sonne $ set_mode twoarc # 2" x 2" FOV
sonne $ set_mode onearc # 1" x 1" FOV
sonne $ set_mode halfarc # 0.5" x 0.5" FOV
```

### MBI
This is a 12"x6" crop that accommadates the four 3"x3" fields produced in the multi-band imaging (MBI) mode.


```
sonne $ set_mode mbi
```

### MBI Reduced

This field crops out the 625nm field so that the maximum readout speed of the detector can still reach ~500 fps while still imaging three 3"x3" FOVs.

```
sonne $ set_mode mbi-reduced
```

### Pupil

This crop is like the standard crop but larger to accommadate the size of the full pupil when imaged with the pupil-imaging lens. Note that currently it is only possible to get a focused pupil image on VCAM1.

```
sonne $ set_mode pupil
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
    node [shape=box]
    "trigger cameras" -> {
        "wait for camera 1 ready";
        "wait for camera 2 ready";
    } ->
    "logical AND" ->
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
    node [shape=box]
    "trigger cameras A" -> {
        "wait for camera 1 ready A";
        "wait for camera 2 ready A";
    } ->
    "logical AND A" ->
    "delay half_width A" ->
    "trigger AFLC high" ->
    "delay half_width B" ->
    "trigger cameras B" -> {
        "wait for camera 1 ready B";
        "wait for camera 2 ready B";
    } ->
    "logical AND B" ->
    "trigger AFLC low" ->
    "trigger cameras A";
}
```

## (Advanced) Crop location

TODO

## Miscellaneous

