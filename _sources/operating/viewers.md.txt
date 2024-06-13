# Camera Viewers

## VCAM1 and VCAM2

```
scexao5 $ vcam1 &
scexao5 $ vcam2 &
```
**Help Message**
```
VAMPIRES Camera Viewer
=======================================
h           : display this help message
x, ESC      : quit viewer

Camera controls:
(Note: these get applied to both cameras.
 if you press ALT, will only apply to one camera)
--------------------------------------------------
CTRL  + j         : Increase exposure time
CTRL  + k         : Decrease exposure time
CTRL  + e         : Enable hardware trigger
SHIFT + e         : Disable hardware trigger
CTRL  + t         : Enable micro-controller trigger
SHIFT + t         : Disable micro-controller trigger
CTRL  + f         : Switch to SLOW readout mode
SHIFT + f         : Switch to FAST readout mode

Display controls:
--------------------------------------------------
c         : display cross
SHIFT + c : display centered cross
d         : subtract dark frame
CTRL + d  : take dark frame
r         : subtract reference frame
CTRL + r  : take reference frame
p         : display compass
i         : display scale bar
l         : linear/non-linear display
m         : cycle colormaps
v         : start/stop accumulating and averaging frames
z         : zoom/unzoom on the center of the image
SHIFT + z : unzoom image (cycle backwards)
ARROW     : steer crop
CTRL + z  : reset zoom and crop

Pupil mode:
--------------------------------------------------
CTRL  + p : toggle pupil lens

Focus controls:
--------------------------------------------------
CTRL  + u : Nudge focus by  0.005 mm
CTRL  + i : Nudge focus by -0.005 mm
SHIFT + u : Nudge focus by  0.1 mm
SHIFT + i : Nudge focus by -0.1 mm

Cam focus controls:
--------------------------------------------------
CTRL  + l : Nudge cam focus by  0.01 mm
CTRL  + ; : Nudge cam focus by -0.01mm
SHIFT + l : Nudge cam focus by  0.1 mm
SHIFT + ; : Nudge cam focus by -0.1 mm

MBI wheel controls:
--------------------------------------------------
CTRL  + [] : Nudge wheel 0.005 deg CCW / CW
SHIFT + [] : Nudge wheel 0.2 deg CCW / CW
CTRL  + m  : Insert MBI dichroics
SHIFT + m  : Remove MBI dichroics
ALT   + m  : Save current angle to last configuration

Field stop controls:
--------------------------------------------------
CTRL  + 7     : Fieldstop
CTRL  + 8     : CLC-2
CTRL  + 9     : CLC-3
CTRL  + 0     : CLC-5
CTRL  + -     : CLC-7
CTRL  + =     : DGVVC
CTRL  + ARROW : Nudge 0.001 mm in x (left/right) and y (up/down)
SHIFT + ARROW : Nudge 0.05 mm in x (left/right) and y (up/down)
CTRL  + o     : Offset fieldstop 0.5 mm; press again to return
CTRL  + s     : Save current position to last configuration

Filter controls:
--------------------------------------------------
CTRL + 1 : Open
CTRL + 2 : 625-50
CTRL + 3 : 675-60
CTRL + 4 : 725-50
CTRL + 5 : 750-50
CTRL + 6 : 775-50

Diff filter controls:
--------------------------------------------------
CTRL + SHIFT + 7 : Open / Open
CTRL + SHIFT + 8 : SII-Cont / SII
CTRL + SHIFT + 9 : Ha-Cont / Halpha
CTRL + SHIFT + 0 : Open / Open
CTRL + SHIFT + - : SII / SII-Cont
CTRL + SHIFT + = : Halpha / Ha-Cont

Field stop controls:
--------------------------------------------------
CTRL  + 7     : Fieldstop
CTRL  + 8     : CLC-2
CTRL  + 9     : CLC-3
CTRL  + 0     : CLC-5
CTRL  + -     : CLC-7
CTRL  + =     : DGVVC
CTRL  + ARROW : Nudge 0.001 mm in x (left/right) and y (up/down)
SHIFT + ARROW : Nudge 0.05 mm in x (left/right) and y (up/down)
CTRL  + .     : Nudge -0.05 mm in focus
CTRL  + ;     : Nudge 0.05 mm in focus
CTRL  + o     : Offset fieldstop 0.5 mm; press again to return
CTRL  + s     : Save current position to last configuration
```

## VPUPCAM

```
sonne $ vpupcam &
```

**Help Message**
```
VPUPCAM controls
=======================================
h           : display this help message
x, ESC      : quit vpupcam

Display controls:
---------------------------------------
c         : display cross
SHIFT + c : display centered cross
r         : subtract reference frame
CTRL + r  : take reference frame
p         : display pupil overlay
l         : linear/non-linear display
m         : cycle colormaps
v         : start/stop accumulating and averaging frames
z         : zoom/unzoom on the center of the image
SHIFT + z : unzoom image (cycle backwards)
ARROW     : steer crop
CTRL + z  : reset zoom and crop

Pupil wheel alignment:
-----------------------------------------------------
CTRL  + ARROW : Nudge wheel 0.01 mm in x (left/right)
                                   and y (up/down)
SHIFT + ARROW : Move wheel 1 mm in x (left/right)
                               and y (up/down)
CTRL  + []    : Nudge wheel 0.1 deg in theta (ccw/cw)
SHIFT + []    : Nudge wheel 1 deg in theta (ccw/cw)
CTRL  + S     : Save position to the last configuration

Pupil wheel masks:
----------------------------------
CTRL  + 1         : Open (0 deg)
CTRL  + 2         : SAM-7
CTRL  + 3         : SAM-9
CTRL  + 4         : Open (73 deg)
CTRL  + 5         : SAM-18
CTRL  + 6         : SAM-Ann
CTRL  + 7         : Mirror
CTRL  + 8         : Open (164 deg)
CTRL  + 9         : LyotStop-L
CTRL  + 0         : RAP
CTRL  + -         : ND10
CTRL  + =         : ND25
CTRL  + SHIFT + 7 : LyotStop-M
CTRL  + SHIFT + 8 : LyotStop-S
```

## Others

anycam is a base PyGame viewer tool-- all of the VAMPIRES PyGame viewers are subclasses of the anycam class. Therefore, anycam is only useful if you need to see a raw image stream, without any of the cropping automated into the VCAM viewers.
```
$ anycam vcam1 &
```

shmImshow uses a QT viewer that is dynamically resizable, zoomable, and with an adjustable color scale
```
$ shmImshow.py vcam1 &
```


## FAQ

### 1. The crop is all weird!

After setting a new crop, the state of the camera viewers can become corrupted and steering the image with the arrow keys will mess with the displayed image showing very off-center PSFs or multiple copies of the same PSF in MBI mode. To fix this, reset the crop and steering- `CTRL+Z`, then any arrow key, then `CTRL+Z`.

### 2. The cameras froze!

The easiest fix is to restart the camera processes, which will reset your crops and the camera PyRO instance

```
scexao5 $ camstart vcam1
scexao5 $ camstart vcam2
```
