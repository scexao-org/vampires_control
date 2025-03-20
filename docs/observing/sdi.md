# Narrowband / SDI

Spectral differential imaging can be enabled in multiple ways

1. Simple dual-band imaging
2. Differential filter switching
3. Polarimetry

regardless, the following common procedure follows

## Focus offsets

The differential filters are in a F/21 powered beam which causes a focus offset. Because the filters are narrowband, it is necessary to check these offsets ahead of time with a laser source. The default offsets are applied to both focus stages with

    $ vampires_focus sdi

## Simple dual-band Imaging

Some observations don't require or benefit from the differential filter switching and instead leave a single filter in front each camera. For this operation, simply insert the differential filter set

**Diff wheel sets**
1. Open / Open
2. SII-Cont / SII
3. Ha-Cont / Halpha
4. Open / Open
5. SII / SII-Cont
6. Halpha / Ha-Cont

For example, to set Halpha filter in front of cam1 and Ha-Cont in front of cam2

    $ vampires_diff 6

and then prepare data logging as usual.

## Differential SDI

These observations require a daemon process to switch the differential filter wheel in between exposures, and is therefore a step more difficult than the simple dual-band imaging. Follow the same setup but instead of manually logging the data, use the `vampires_sdi_daemon` script on scexao5

    Usage: vampires_sdi_daemon [OPTIONS]

    Options:
    -m, --mode [Halpha|SII|both]
    -n, --num-cubes INTEGER
    -l, --max-loops INTEGER
    --help                        Show this message and exit.

where `num-cubes` is the number of cubes between filter swaps, `num-loops` sets an optional max number of loops (otherwise continues indefinitely), and `mode` tells whether to use Halpha, SII, or all filters.

    sc5 $ conda activate vampires_control
    sc5 (vampires_control) $ vampires_sdi_daemon

When using this script, you'll need to set the number of frames per cube to a reasonable value. For exmaple, if you set the integraiton time to 1 second and the number of frames per cube to 1,000, it will be 17 minutes for a single cube and therefore the filter will only switch every 17 minutes!

## Polarimetric SDI

Polarimetry is possible with SDI by treating each individual camera as a separate polarimeter. Because each camera has a different filter, there is no simultaneous cancellation from subtracting cam1 - cam2, so PDI is only enabled by switching orthogonal polarization states using the FLC or HWP. This is best accomplished in "fast" polarimetry mode so that every other exposure is in orthogonal polarization states, instead of relying only on the HWP with its slower switching time.

For polarimetric SDI without differential filter switching, follow the same setup as the "simple dual-cam imaging" above, combined with the appropriate polarimetry setup and use the `hwp_daemon` as normal.

For polarimetric SDI with differential filter switching, the filter wheel is controlled by the HWP daemon, so pass the extra flags

    sc2 $ hwp_daemon <options> --sdi=Halpha -n 2

In this mode, the differential filter wheel is switched once per HWP angle, which requries `-n 2` to specify "two cubes per HWP angle". 

## Checklist

Here is a checklist for SDI observations

**Pre-check:**
- []: Have you checked SDI focus offsets with the calibration source?
**Observing:**
- []: Is differential filter inserted?
- []: Are focus offsets applied?
- []: Change any detector settings
- []: Prepare data logging (vampires_preplog), remember cube size matters!
- []: If using differential switching, prepare a scexao5 terminal in the `vampires_control` environment to run the `vampires_sdi_daemon`
- []: If using polarimetry, prepare for PDI and use the `hwp_daemon` (with the `-n 2 --sdi=<mode>` flags, if desired)