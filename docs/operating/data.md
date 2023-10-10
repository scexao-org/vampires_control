# Data Acquisition

## Data Flowchart

The VAMPIRES cameras operate predominantly through `scexao5`, however the network architecture is slightly more complicated

```{graphviz}
digraph {
    node [shape=box]
    "vcam1" -> "scexao5" [label="CXP"];
    "vcam2" -> "scexao5" [label="CXP"];
    "vpupcam" -> "sonne" [label="USB"];
    "sonne" -> "scexao6" [label="0MQ"];
    "scexao5" -> "scexao6" [label="TCP"];
    "scexao5" -> "sonne" [label="0MQ"];
}
```

`scexao5` serves as the main entrypoint for controlling the camera processes (the `cam-vcamstart` scripts and tmux sessions) as well as the computer the data is initially saved to. Contrarily, the pupil camera is plugged directly into `sonne` over USB.

Once the shared memory streams for vcam1 and vcam2 are running on `scexao5` they will be transmitted over the network in two ways
1. 20 Gbps TCP link (fast)
2. 500 Mbps 0MQ link (slow)

The TCP links are able to transmit the full-speed data streams from `scexao5` to `scexao6` so that any code running on `scexao6` can operate in real-time. The 0MQ links are throttled to 20 FPS to conserve some network bandwidth- these are only appropriate for simple control scripts (like autofocus) or for camera viewers. 