# Polarimetry

There are two polarimetry modes supported by VAMPIRES
* "SLOW" mode, which uses the facility HWP, only (double-difference)
* "FAST" mode, which uses the achromatic FLC and the facility HWP (triple-difference)

Both modes have been tested, successfully, on sky. Using FAST mode should theoretically allow better cancellation of fast atmospheric speckles, but at the cost of some overhead, slightly lower throughput, and more complex data-analysis. Furthermore, the FLC cannot be used for exposure times longer than 1 second, so long-exposure imaging should use "SLOW" mode.

(slow_pol)=
## Setup: Slow Mode

1. Set up the WPU
In the `garde` VNC find a terminal and launch the WPU
```
garde $ obsSTARTgen2sum
```
1. Insert the HWP "Stage (1/2-Waveplate) -> Select Operation -> Move in -> Move / Exec"
2. (Optional) Enable HWP ADI synchronization, if desired "Rotator (1/2-Waveplate) -> Select Operation -> Sync mode ADI -> Move / Exec"

After the WPU is set up, make sure VAMPIRES is prepared for dual-cam imaging using the polarizing beamsplitter
```
$ vampires_bs pbs
$ vampires_focus standard
```
There is no difference between standard and MBI imaging- follow [the MBI instructions](mbi) for instructions.

Make sure the QWP daemon is running, too!

## Setup: Fast Mode

All of the setup procedures are the same as [slow mode](slow_pol), with the additional requirements to set up the FLC

1. Insert the FLC
```
$ vampires_flc in
```
2. Prepare the VAMPIRES trigger

```
$ vampires_trig set -f
```

The FLC will start switching as soon as the `-f` flag is enabled, even if the micro-controller is not enabled for triggering. You can confirm the switching by inserting the SCExAO polarizer:
```
scexao2 $ polarizer
```
if you don't see obvious switching, the FLC controller may have lost power (rare, but has happened). This requires manually checking the box and power switch at the summit. Don't forget to remove the polarizer afterwards!

## Operating

At this point you need to prepare both cameras for [logging](logging). If the fpsCTRL process is not running, the acquisition daemon **will not save any data** without showing any errors.

### Triggering

VAMPIRES needs to use an external hardware trigger to ensure both cameras acquire frames simultaneously. **If triggering is not enabled, the data will not be reducible.** If triggering is not enabled, the post-observing data management procedure will fail to deinterleave FLC states, too.

To prepare the [camera trigger](trigger) use the VCAM1 or VCAM2 camera viewers
```
CTRL + E        Enable camera external trigger mode
CTRL + T        Enable micro-controller
```
to stop triggering, use
```
SHIFT + T       Disable micro-controller
```
and to switch back to internal camera triggers
```
SHIFT + E       Disable camera external trigger mode
```

### HWP Modulation

The WPU HWP is modulated using the `hwpsync` script. There are two primary modes- one which synchronizes the HWP rotation to CHARIS frames, and one which synchronizes to a timer. Obviously, if you are not using CHARIS you will have to use the timer, and if you are using CHARIS you will need to sync to the CHARIS frames.

```{admonition} Picking times and cube sizes
:class: tip

We want to switch the HWP as fast as possible without significant losses in duty cycle from signalling overheads and HWP rotation delays. In addition, we want to avoid the field rotating significantly during a single HWP cycle (four HWP positions). This is important for coronagraphic observations since the satellite spots will rotate and will not cancel out as efficiently. Depending on the declination of the target and the rotation requirements, we recommend switching the HWP at least once every 60 seconds.

When synchronizing to CHARIS, usually the CHARIS exposure time is sufficiently long for syncing with the HWP. If taking short, 5 second exposures you can opt to take two or three CHARIS frames per HWP angle to slightly improve observing efficiency.

When not synchronizing to CHARIS, I usually opt to switch the HWP every 10-60 seconds, depending on my framerate. In an ideal world, there is only one VAMPIRES data cube per HWP angle, so if you're taking data at 10 Hz with 250 frames per cube, you can set the timer to ~20 seconds-- the FITS logger will truncate a cube if it is told to stop logging before a full cube has been acquired, and  it's better to truncate a cube slightly smaller than to overflow and end up with many cubes with only a few frames over the night. If you're taking data at high-framerates this cannot be avoided.
```

#### CHARIS Synchronization

So, if synchronizing to CHARIS, make sure all the loggers are set up with an appropriate number of frames per cube based on the CHARIS exposure time. Then launch the HWP daemon with

```
scexao2 $ hwpsync cv[f]
```
where the `c` stands for CHARIS and the `v` stands for VAMPIRES. If using FastPDI, also add an `f`. To change the number of CHARIS frames per HWP position, use the `-n` flag.

```{admonition} CHARIS timing

Because `hwpsync` will move the HWP when started, you should wait to start the CHARIS exposures until right after the HWP is settled (about a second, depending on where it was, previously). Because VAMPIRES (and FastPDI) wait for the *end* of the CHARIS frame for signalling, there is no issue with starting their exposures before the CHARIS exposure.
```
#### State Diagram

```{graphviz}
digraph {
    node [shape=box]
    "Move HWP" -> {
        "Acquire VAMPIRES";
        "Acquire FastPDI";
        "Acquire CHARIS";
    } ->
    "Wait for end of CHARIS frame" ->
    "Pause all cameras" ->
    "Move HWP";
}
```
#### Timer Synchronization

Alternatively, a timer can be specified (in seconds) using VAMPIRES (`v`) and FastPDI (`f`)

```
scexao2 $ hwpsync v[f] -t 20
```

#### State Diagram

```{graphviz}
digraph {
    node [shape=box]
    "Move HWP" ->
    "Start timer" -> {
        "Acquire VAMPIRES";
        "Acquire FastPDI";
    } ->
    "Wait for end of timer" ->
    "Pause all cameras" ->
    "Move HWP";
}
```

### Polarimetric SDI

We can run the narrowband spectral differential imaging mode at the same time as the PDI loop. This requires triggering two CHARIS frames (or timers, if not using CHARIS) per HWP angle. During one of the frames, the differential filter wheel will be in state 1/2, then during the other frame the differential filter wheel will be in state 2/2. This way, both SDI states are recorded for each HWP angle, allowing full PDI reconstruction. To minimize differential wheel movements, the SDI states will proceed 1,2 -> 2,1 over different HWP angles (e.g., ABBA).

Example with CHARIS:
```
scexao2 $ hwpsync vc -n 2 --sdi Halpha 
```
Example without CHARIS:
```
scexao2 $ hwpsync v -t 30 -n 2 --sdi Halpha
```
#### State Diagram

```{graphviz}
digraph {
    node [shape=box]
    "Move HWP" -> {
        "Acquire VAMPIRES";
        "Acquire FastPDI";
        "Acquire CHARIS";
    } ->
    "Wait for end of CHARIS frame 1" ->
    "Pause VAMPIRES" ->
    "Move differential filter wheel" ->
    "Wait for end of CHARIS frame 2" ->
    "Pause all cameras" ->
    "Move HWP";
}
```
### Stopping the HWP daemon

While the `hwpsync` program is running, you can `CTRL + c` it to send a "last frame" command. This will wait for the next CHARIS frame/timer to finish, will stop all VAMPIRES and FastPDI logging, and then close the program. This is very convenient to use on the last iteration of a HWP sequence. CHARIS data acquisition still has to be stopped from Gen2.

In case you need to stop urgently, hit `CTRL + c` twice, which will stop all VAMPIRES and FastPDI logging immediately.

## Teardown

When closing up make sure to remove the WPU HWP
1. "Rotator (1/2-Waveplate) -> reset -> Move / Exec"
1. "Stage  (1/2-Waveplate) -> Select Operation -> Move out -> Move / Exec"

then shut down the WPU
```
garde $ stopOBS
```

If the VAMPIRES FLC was used, it should be removed as well
```
$ vampires_flc out
```
