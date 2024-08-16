# Autofocusing

VAMPIRES has two focus stages
1. The linear stage that the objective lens is mounted on
2. The linear stage that VCAM1 is mounted on

In general, you need to use both stages to optimize focus for both cameras. The standard procedure for "dual-cam" focusing is
1. Focus VCAM2 by optimizing the position of the objective lens stage
2. Focus VCAM1 by optimizing the position of the camera stage
this order is required because the lens focus stage is the only way to change the focus of VCAM2 given its fixed mount.

There is an automated utility for dual-cam focusing that will take multiple frames of data, average them together, compute a focusing metric, and performs a simple grid-search to optimize the position. Currently the focusing metric is the Strehl ratio. In our testing searching +-1 mm from a decent starting point is sufficient to find an optimum- we fit a quadratic polynomial to interpolate the best focus position from the scan.

## Standard procedure

The default setup for VAMPIRES is dual-cam mode which has the configuration names "STANDARD" for the lens stage and "DUAL" for the camera stage
```
sonne $ vampires_focus standard
sonne $ vampires_camfocus dual
```
from here run
```
sonne $ vampires_autofocus lens -c 2
```
and then save the outputs if everything looks good
```
sonne $ vampires_focus --save 1
```
and now do the same for the converse stage-
```
sonne $ vampires_autofocus cam -c 1
sonne $ vampires_camfocus --save 1
```

## Narrowband filters
If using the narrowband filters a small focus shift is introduced, so a separate lens stage config, "SDI", is used.
```
sonne $ vampires_diff 2
sonne $ vampires_focus sdi
sonne $ vampires_camfocus dual
```
In theory the differential focus should not change with the introduction of the differential narrowband filters, so only the lens stage needs optimized- the following will only use the VCAM1 image to focus the lens
```
sonne $ vampires_autofocus lens -c 1
sonne $ vampires_focus --save 2
```

## Visible bench pickoffs
Similar to the narrowband filter case, if any FIRST/VisPL pickoffs are in there is another focus shift that can be optimized by the lens stage only. Currently only one configuration for the VisPL pickoff is set
```
sonne $ vampires_focus vpl
sonne $ vampires_camfocus dual
sonne $ vampires_autofocus lens -c 1 
sonne $ vampires_focus --save 4
```

## Single-cam focus (no beamsplitter)

For the case of observations that do not want to use the beamsplitter we move the camera stage to accommadate the large focus shift from the 25 mm thick beamsplitter
```
sonne $ vampires_bs open
sonne $ vampires_focus standard
sonne $ vampires_camfocus single
sonne $ autofocus lens -c 1
sonne $ vampires_camfocus --save 2
```

## Pupil mode

The image created by the pupil lens is very defocused- it is actually impossible to get a focused image on VCAM2. The setup is
```
sonne $ vampires_focus pupil
sonne $ vampires_camfocus pupil
```
which puts the lens stage at its minimum (0 mm). There is no automated script for focusing the pupil image, it must be done by hand. Once satisfied, save the position with
```
sonne $ vampires_focus --save 3
sonne $ vampires_camfocus --save 3
```

