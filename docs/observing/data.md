# Post-observing Data Management

All VAMPIRES data is pre-processed with a uniform pipeline before transferring to the local SCExAO data archive (currently `scexao6`). The pipeline has the following steps:

1. Synchronization, deinterleaving, and consolidation
1. Fix headers
1. (Archive-only) Assign frame IDs
1. Compress
1. Copy to scexao6 archive
1. (Archive-only) Generate manifest

These steps have been combined into a convenience scripts that can be run from scexao5.

By default, all VAMPIRES data will be processed daily using cronjob scripts and should not require manual intervention. However, any steps can be ran manually at any time (e.g., to quickly begin processing data).

To view the status of the VAMPIRES archival data
```bash
sc5 $ vamp_archive_table | head
scexao5_path                      utc_date    processed  processed_timestamp  transferred_to_scexao6  transferred_timestamp  safe_on_scexao6  safe_timestamp
/mnt/fuuu/ARCHIVED_DATA/20250603  2025-06-03  True                            True                                           True             2025-11-14T20:38:15
/mnt/fuuu/ARCHIVED_DATA/20250605  2025-06-05  True                            True                                           True             2025-06-26T21:54:55
/mnt/fuuu/ARCHIVED_DATA/20250606  2025-06-06  True       2025-06-26T21:50:20  True                                           True             2025-11-13T00:00:00
/mnt/fuuu/ARCHIVED_DATA/20251004  2025-10-04  True                            True                                           True             2025-11-14T20:19:46
/mnt/fuuu/ARCHIVED_DATA/20251005  2025-10-05  True                            True                                           True             2025-11-14T20:12:06
/mnt/fuuu/ARCHIVED_DATA/20251006  2025-10-06  True                            True                                           True             2025-11-14T20:12:52
/mnt/fuuu/ARCHIVED_DATA/20251009  2025-10-09  True                            True                                           True             2025-11-11T01:22:03
/mnt/fuuu/ARCHIVED_DATA/20251106  2025-11-06  True       2025-11-07T01:51:53  True                    2025-11-07T02:51:24    True             2025-11-14T20:15:09
```
and to see the status of the VAMPIRES engineering data
```bash
sc5 $ vamp_process_table | head
scexao5_path        utc_date    processed  processed_timestamp  transferred_to_scexao6  transferred_timestamp  safe_on_scexao6  safe_timestamp
/mnt/fuuu/20240124  2024-01-24  True       2025-11-17T20:07:20  True                    2025-11-17T20:07:22    False
/mnt/fuuu/20240131  2024-01-31  False                           False                                          False
/mnt/fuuu/20240201  2024-02-01  False                           False                                          False
/mnt/fuuu/20240204  2024-02-04  False                           False                                          False
/mnt/fuuu/20240205  2024-02-05  True       2025-11-17T20:07:31  True                    2025-11-17T20:07:32    False
/mnt/fuuu/20240207  2024-02-07  False                           False                                          False
/mnt/fuuu/20240210  2024-02-10  False                           False                                          False
/mnt/fuuu/20240212  2024-02-12  False                           False                                          False
/mnt/fuuu/20240213  2024-02-13  False                           False                                          False
```


To view and edit the cron schedule, see
```bash
$ crontab -e
```

## Manual Execution

The most straightforward way to immediately process new data is to run a script which scans through all available data folders and automatically launches the appropriate processing script inside a tmux session. For archival data, this script is
```bash
sc5 $ scxkw-vamp-archive-processor
```
and for engineering data the script is
```bash
sc5 $ scxkw-vamp-process-processor
```

### Restoring folder

if something goes wrong in this process and you need to recover, there is another script that restores the working directory to its original state (this will delete the vgen2 folder!)

```
sc5 $ scxkw-vamp-restore-folder <folder>
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

