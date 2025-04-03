# Data Acquisition

## Data Flowchart

The VAMPIRES cameras operate predominantly through `scexao5`, however the network architecture is slightly more complicated

```{graphviz}
digraph {
    node [shape=box]
    "vcam1" -> "scexao5" [label="CXP"];
    "vcam2" -> "scexao5" [label="CXP"];
    "vpupcam" -> "sonne" [label="USB"];
    "sonne" -> "scexao6" [label="ZMQ"];
    "scexao5" -> "scexao6" [label="TCP"];
    "scexao5" -> "sonne" [label="ZMQ"];
}
```

`scexao5` serves as the main entrypoint for controlling the camera processes (the `camstart` scripts and tmux sessions) as well as the computer the data is initially saved to. Contrarily, the pupil camera is plugged directly into `sonne` over USB.

Once the shared memory streams for vcam1 and vcam2 are running on `scexao5` they will be transmitted over the network in two ways
1. 20 Gbps TCP link (fast)
2. 500 Mbps ZMQ link (slow)

The TCP links are able to transmit the full-speed data streams from `scexao5` to `scexao6` so that any code running on `scexao6` can operate in real-time. The ZMQ links are throttled to 20 FPS to conserve some network bandwidth- these are only appropriate for simple control scripts (like autofocus) or for camera viewers. 

(logging)=
## Logging FITS files

To log FITS files with full headers, you will need to set up a `milk-streamFITSlog` process on `scexao5`. The recommended interface is to call
```
sonne $ vampires_preplog
```
this will launch an interactive process to set up logging for the VAMPIRES cameras. 
```{admonition} Warning: File size
:class: warning

Be careful to not save too many frames to each data cube-- when individual data cube sizes grow too large simple tasks (loading into DS9 or as a numpy array) become annoyingly slow. This is exacerbated in multiband imaging mode, which produces 280 MB/s per camera. We aim for file sizes around 1-2 GB, max, which corresponds to the following cube lengths
| Crop | Max. frames | File size |
| - | - | - |
| `STANDARD` | 2000 | 1.1 GB |
| `MBI` | 250 | 1.2 GB |
| `MBI_REDUCED` | 500 | 1.2 GB |
```

Once this process is finished, you should launch an FPS control from `scexao5`
```
scexao5 $ FPS_FILTSTRING_NAME="streamFITSlog-vcam" milk-fpsCTRL
```
you should see one or two processes, depending on how many cameras you're logging. The left three numbers should all be green. If the right of those three numbers is gray, press `SHIFT + R` over the process to start it. 

### Option 1: Using VAMPIRES scripts

If you are using both cameras, you'll want to using scripts that psuedo-simulatneously trigger both cameras' logger processes. This is enabled with the following VAMPIRES scripts:
* `vampires_startlog`
* `vampires_pauselog`
* `vampires_pauselog --wait`
* `vampires_stoplog`
* `vampires_stoplog --kill`

### Option 2: Directly using fpsCTRL

If you are only logging one camera it is usually simple enough to initiate camera acquisition directly through `fpsCTRL`. To initiate logging, press the right arrow to go into the camera's logger process and then arrow down to the `saveON` option. The space bar will enable and disable the process. If a FITS cube has not been filled when `saveON` is disabled the file will be truncated; to finish the last cube arrow down and enable the `lastCubeON` option, instead.

If you change camera crops or if you want to change the number of frames per cube, you will need to restart the logger process. This is because the data buffer used for the FITS file needs to be reallocated when the memory footprint changes. To restart the process, go back to the main `fpsCTRL` menu and do `CTRL+R`, then adjust the cube size, then go back and `SHIFT+R` the process.


## Watching FITS files

To confirm each FITS file gets written appropriately, there is a tool which watches directories for new FITS files and shows a quick file summary. To run this script, call `fitswatcher` with a glob over the directories to watch--

```
scexao5 $ fitswatcher -n 3 <dir>/vcam*
```
the `-n` flag will show the specified number of files per folder in the TUI, by default 2.

```{admonition} Tip: Tonight's folder
:class: tip

If you are logging data to gen2 for nightly observing, the following one-liner should work to set up `fitswatcher` for VAMPIRES

    scexao5 $ fitswatcher -n 3 /mnt/fuuu/ARCHIVED_DATA/$(date -u +'%Y%m%d')/vcam*

```

```
╭─ FITS Watcher - 2024-06-13T00:11:20.347365 ────────────────────────────────╮
│ /mnt/fuuu/20240611/vcam1/ - 8 FITS files (29 GB)                           │
│   vcam1_00:00:03.628172287.fits - (1000, 1104, 2228) 4919 MB | DARK scexao │
│   vcam1_23:59:49.294402958.fits - (249, 1104, 2228) 1225 MB | DARK scexao  │
│   vcam1_23:59:34.528434921.fits - (611, 1104, 2228) 3006 MB | DARK scexao  │
│                                                                            │
│ /mnt/fuuu/20240611/vcam2/ - 7 FITS files (29 GB)                           │
│   vcam2_00:00:05.715949178.fits - (1000, 1104, 2232) 4928 MB | DARK scexao │
│   vcam2_23:59:56.721432449.fits - (248, 1104, 2232) 1222 MB | DARK scexao  │
│   vcam2_23:59:35.200653725.fits - (581, 1104, 2232) 2863 MB | DARK scexao  │
╰────────────────────────────────────────────────────────────────────────────╯
```