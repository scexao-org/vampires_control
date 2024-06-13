(mbi)=
# Multiband Imaging

## Inserting

To set up VAMPIRES for multiband imaging (MBI) first insert the MBI dichroics--

```
$ vampires_mbi dichroics &
```
and make sure the VAMPIRES filter wheel is open
```
$ vampires_filter open
```

```{admonition} ⏳ Slow

The MBI stage moves slowly (1.5 deg/s) which requires 120s to rotate between the MBI dichroics and the mirror.
```

then, set the [camera crop](camera_crops)
```
sonne $ set_crop mbi
```

## Removing

To return back to standard imaging mode, simply remove the MBI dichroics and revert the camera crops

```
$ vampires_mbi mirror &
```
```
sonne $ set_crop standard
```

## MBI Reduced

The "reduced" MBI mode is one which crops out the F610 field for speed or spectral concerns (e.g., source is significantly dimmer at 600 nm and it is hard to get good dynamic range in all fields). Since this is just cropping, you only need to adjust the camera crops to enable reduced mode

```
sonne $ set_crop mbi_reduced
```

you should see the top-left frame go black in the camera viewers when the cameras process restarts.

## (Advanced) MBI Hotspotting

the location of the MBI PSFs is used for both the camera viewers as well as the WCS information in the headers. TODO

1. Insert MBI dichroics and prepare crop
2. Use `hotspot` script
```
sonne $ hotspot vcam1 -r
sonne $ hotspot vcam2 -r
```
3. For each camera
    1. Load the files saved to `~/src/vampires_control/data/crops/<date>_<cam>_mbi_config.toml` and `~/src/vampires_control/data/crops/<date>_<cam>_mbir_config.toml`
    2. Manually edit the camstack class `camstack/cams/vampires.py:VCAM1` (or VCAM2) and update the crop and hotspot class variables for the MBI and MBIR crops

