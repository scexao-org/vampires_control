# Troubleshooting

## VCAM viewers are frozen

Sometimes the `vcam1` or `vcam2` viewers will freeze up. This seems to be related to the PyRO server the cameras and devices use for communicating between computers over the network. When the viewers freeze, this does not mean the framegrabbers have stopped. In other words, there is still data coming into the `vcam1` and `vcam2` SHMs, but we can no longer control the cameras. This means that data can still be saved, except when doing PDI (the HWP synchronizer interacts with the camera objects and will freeze up, too).


Sometimes the problem resolves itself after a long time (many minutes). I have also had luck with killing any existing streamFITSloggers for the vcams (e.g., run `vampires_stoplog --kill` or the `kill log` mprocs script), restarting the viewer(s), and then recreating the streamFITSlogger (i.e., `vampires_preplog` or the `prep log` mprocs script).

If those solutions don't work, try restarting BOTH the camera processes--

```
sc5 $ camstart vcam1
sc5 $ camstart vcam2
```

keep an eye on the camera tmuxes (`vcam1_ctrl` and `vcam2_ctrl`) to ensure the processes restart correctly. If they do not work, try running the `camstart` command again.
