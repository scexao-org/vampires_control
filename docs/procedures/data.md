# Post-observing Data Management

There are a few pre-processing steps we take before uploading data to the STARS2 archive. These only need to be ran if data is going to be archived. If you need to synchronize polarimetry data the first step is necessary, too.

1. Synchronization and Consolidation
2. Assign FRAME IDs
3. Compress


## Synchronization and Consolidation

The VAMPIRES cameras produce two independent data streams, even when using the external trigger. The external trigger ensures the cameras will expose at the same time, but the actual arrival time as recorded by the framegrabber is not synchronized (and in fact there are some static offsets due to computer resource sharing). We must manually take the two data streams and synchronize each frame based on the framegrabber timestamp (the `.txt` file that gets saved by Milk).

```
sc5 $ tmux new -s vamp_syncdeint
sc5 $ cd /mnt/fuuu/ARCHIVED_DATA/<date>
sc5 $ scxkw-vamp-syncdeint .
```

This will alter the folder layout and will create a bunch of intermediate files. Once completed, you can view the summary of the syncrhonization with

```
sc5 $ scxkw-vamp-summary .
```

you should check this log  for anything unexpected-- if you expected synchronized and deinterleaved data there should be a minimum of frames that are labeled "vcam1/vcam2" only or that are dubious. If you did not take synchrnoized data then you should not expect "vsync" frames to appear, etc.

Once satisfied, the `.fitsframes` files must be consolidated with their OG FITS files, which is very slow

```
sc5 $ scxkw-fitsframe-consolidate .
```

## Frame IDs


## Compression


## Creating Manifest and Uploading to STARS2

