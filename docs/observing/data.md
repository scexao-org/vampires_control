# Post-observing Data Management

There are a few pre-processing steps we take before uploading data to the STARS2 archive. These only need to be ran if data is going to be archived. If you need to synchronize polarimetry data the first step is necessary, too.

1. Synchronization and consolidation
1. Fix headers
1. Assign frame IDs
1. Compress
1. Copy to scexao6 archive
1. Generate manifest and email Eric

These steps have been combined into a single script that is run from scexao5


```{admonition} Background execution
:class: important

The data archive procedure can take a long time, it is highly recommended to use a tmux session to allow detaching
```

```{admonition} Frame IDs
:class: warning

Ideally sequential VAMPIRES frame IDs are also in chronological order. If you are processing multiple folders, please process them in chronological order!
```

```
sc5 $ scxkw-vamp-archive <folder>
```

this will generate a manifest file automatically, which still requires emailing to Eric for processing into STARS2

```
sc5 $ echo -e "Dear Eric,\nAttached is a VMPA manifest for <date>. The IP of the machine the data is stored on is $(hostname -i).\n\nBest, SCExAO\n." | mail -s 'VMP manifest <date>' -A manifest_VMP_<date>.csv eric@naoj.org mdlucas@hawaii.edu
```


### Restoring folder

if something goes wrong in this process and you need to recover, there is another script that restores the working directory to its original state (this will delete the vgen2 folder!)

```
sc5 $ scxkw-vamp-archive-restore <folder>
```

## Advanced details

The following sections detail each step of the archival process.

### Synchronization and Consolidation

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

### Fix Headers

The FITS headers in the raw format contain floating point values that have more precision than expected based on the FITS dictionary for the instrument. To address this, run a simple script that ensures formatting is valid. This will not change any values, functionally, just the representation of the value in the FITS card.

```
sc5 $ cd /mnt/fuuu/ARCHIVED_DATA/<date>
sc5 $ scxkw-fix-headers vgen2
```

### Frame IDs

Frame IDs are designed to be sequential, and therefore if batch processing make sure to start with the oldest data, first.

```
sc5 $ cd /mnt/fuuu/ARCHIVED_DATA/<date>
sc5 $ scxkw-assign-frameids -f $(pwd) -v
```

### Compression

fpack compression should be done after all header manipulations are completed, because afterwards data access becomes much slower, by an order of magnitude. Note that the following runs a daemon which scans all `/mnt/fuuu/ARCHIVED_DATA/**/**/VMP*.fits` files to archive, so you don't need to run it in any particular directory, nor do you have control over which files get compressed.

```
sc5 $ scxkw-daemon-all select fpackthendie
```

### Creating Manifest and Uploading to STARS2

The final step is preparing a STARS manifest and sending to the STARS team (Eric Jeschke <eric@naoj.org>).

Begin by creating the manifest (make sure to edit the CSV name appropriately)

```
sc5 $ cd /mnt/fuuu/ARCHIVED_DATA/<date>
sc5 $ scxkw-g2archive-manifest -o manifest_VMP_<date>.csv -p VMP vgen2/VMPA*.fits.fz
```

```{admonition} Combining manifests

It is preferred to only send one manifest in the email to the STARS team, so if you have multiple manifest files, concatenate them first

    cat manifest_VMP_<date1>.csv manifest_VMP_<date2>.csv > manifest_VMP_combined.csv
```

after the manifest is created, you can manually send an email by downloading the CSV to your local computer, or you can send an unsigned email from scexao5, directly. Be sure to mention the IP of the machine the data is stored on.

```
sc5 $ echo -e "Dear Eric,\nAttached is a VMPA manifest for <date>. The IP of the machine the data is stored on is $(hostname -i).\n\nBest, SCExAO\n." | mail -s 'VMP manifest <date>' -A manifest_VMP_<date>.csv eric@naoj.org vdeo@naoj.org mdlucas@hawaii.edu
```

### Transferring Data to scexao6

Data needs to be copied to scexao6 for long-term storage and to make sure we don't run out of run on scexao5. This data transfer can be done efficiently over the 10-gig lan.

Target folder: `sc6:/mnt/tier1/2_ARCHIVED_DATA`


**From sc5:**
```
sc5 $ cd /mnt/fuuu/ARCHIVED_DATA
sc5 $ rsync -arxuhP -e "ssh -T -c aes128-ctr -o Compression=no -o ConnectTimeout=10 -x" --exclude=lost+found --exclude=vcam* <date> sc6l:/mnt/tier1/2_ARCHIVED_DATA/
```


**From sc6:**
```
sc6 $ cd /mnt/tier1/2_ARCHIVED_DATA
sc6 $ rsync -arxuhP -e "ssh -T -c aes128-ctr -o Compression=no -o ConnectTimeout=10 -x" --exclude=lost+found --exclude=vcam* sc5l:/mnt/fuuu/ARCHIVED_DATA/<date> .
```

