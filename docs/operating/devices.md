# Device Control

VAMPIRES interacts with many devices, some of which are connected locally, some of which run on other SCExAO computers, and others interface with external facility instruments. The majority of the device control code is at https://github.com/scexao-org/device_control.


## Interacting with devices

We aim to provide an interface to the VAMPIRES devices that can be scripted using python or from the command line. Either way should work effortlessly when connected to a computer with `device_control` installed, using sockets where necessary to communicate over the network.

Use the following code snippet to connect to a device using python
```python
from swmain.network.pyroclient import connect
from scxconf.pyrokeys import VAMPIRES
device = connect(VAMPIRES.<DEVICE>)
```
for example, to connect to the focus stage

```python
fcs = connect(VAMPIRES.FOCUS)
fcs.get_position()
```

## Filters

Filter options:
1. Open
2. 625-50
3. 675-50
4. 725-50
6. 750-50
7. 775-50 

```
vampires_filter <filtname>
```

## Field Stop / Focal Plane Mask

Field stop options:
1. Field stop
2. CLC-2
3. CLC-3
4. CLC-5
5. CLC-7
6. DGVVC


```
vampires_fieldstop <posn>
```

## Mask Wheel

Mask wheel options:
1. Open
2. SAM-7
3. SAM-9
4. SAM-18
5. Open
6. SAM-Ann
7. Mirror
8. Open
9. LyotStop-L
10. ND10
11. ND25
12. LyotStop-M
13. LyotStop-S

```
vampires_mask <mask>
```

## Differential Wheel

Differential wheel options
1. Open / Open
2. SII / Continuum
3. H-alpha / Continuum
4. Open / Open
5. Continuum / SII
6. Continuum / H-alpha

```
vampires_diff <posn>
```

## Beamsplitter Wheel

Beamsplitter wheel options
1. Polarizing beamsplitter
2. Open
3. Non-polarizing beamsplitter

```
vampires_bs <posn>
```

## MBI Wheel

MBI wheel options
1. Dichroics
2. Mirror

## Focus Stages

Focus position options
1. Dual-cam
2. Single-cam
3. Defocus
4. Pupil

There are two focus stages in VAMPIRES, the first is the absolute focus, which controls the objective lens focusing the collimated beam into the beamsplitter cube. It should affect both camera's focii. The second is the differential focus, which is a motorized stage on camera 1. The `Defocus` mode uses the differential focus to add (TODO) waves of defocus on camera 1 for phase-diversity focal plane wavefront sensing.

```
    vampires_focus <configuration>
    vampires_focus lens <args>
    vampires_focus cam <args>
```

## AFLC Stage

The AFLC can be retracted for slow polarimetry mode or to otherwise remove it from the beam.

```
vampires_flc <state>
```


## QWPs

The quarter wave plates can be accessed separately with

```
vampires_qwp 1
vampires_qwp 2
```


