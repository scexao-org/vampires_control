# Frequently Asked Questions

## VCAM viewers are frozen

Sometimes the `vcam1` or `vcam2` viewers will freeze up. This seems to be related to the PyRO server the cameras and devices use for communicating between computers over the network. When the viewers freeze, this does not mean the framegrabbers have stopped. In other words, there is still data coming into the `vcam1` and `vcam2` SHMs, but we can no longer control the cameras. This means that data can still be saved, except when doing PDI (the HWP synchronizer interacts with the camera objects and will freeze up, too).

Sometimes the problem resolves itself after a long time (many minutes), but otherwise the solution to the problem is restarting BOTH the camera processes.

```
sc5 $ camstart vcam1
sc5 $ camstart vcam2
```

keep an eye on the camera tmuxes (`vcam1_ctrl` and `vcam2_ctrl`) to ensure the processes restart correctly. If they do not work, try running the `camstart` command again.

## Filtering VAMPIRES data

TODO

## Synchronizing the WPU logs


### Getting the logs
The WPU logs contain ground truth for the HWP and other optics within the WPU. The WPU logs are stored on `garde`in the folder
```
garde:/hiciao/log/
```
the logs are saved as `wpu<date>.log` where `<date>` is the HST date (not UTC). The `wpu.log` without a date is today's log. This means multiple log files are required for a full night of observing.

These logs are verbose, so there is a utility to extract the HWP and QWP positions, directly. Here is an example--

```
$ scp garde:/hiciao/log/wpu.log .
$ scxkw-wpu-parselog wpu.log
Saved HWP log to wpu.HWP.csv
Saved QWP log to wpu.QWP.csv
```

If we look at this table, it includes timing info, the position (what you want to interplate), and the synchronization mode.
```
$ head wpu.HWP.csv
t_hst,t_utc,stage,position,target,mode
2025-06-03 02:11:24-10:00,2025-06-03 12:11:24+00:00,HWP,0.00,0.0,SYNCHRO_OFF
2025-06-03 02:11:24-10:00,2025-06-03 12:11:24+00:00,HWP,0.00,0.0,SYNCHRO_OFF
2025-06-03 02:11:45-10:00,2025-06-03 12:11:45+00:00,HWP,0.00,0.0,SYNCHRO_OFF
2025-06-03 02:11:45-10:00,2025-06-03 12:11:45+00:00,HWP,0.00,0.0,SYNCHRO_OFF
```

### Imputing the logs

Now that there is a table with the HWP info, the FITS headers for any data can be fixed. The general approach is to create a nearest-neighbor interpoplator for the HWP position using the MJD as the abscissa.

```python
import pandas as pd
import numpy as np
from astropy.time import Time

table = pd.read_csv("wpu.HWP.csv")
# pandas loads the timestamps into a pandas datetime object
# let's convert to astropy to get the MJD
datetimes = pd.to_datetime(table["t_utc"])
table["t_mjd"] = Time(datetimes, format="datetime").mjd
# create our interpolator over the positions
def interpolate_wpu_log(mjd):
    # check if outside of bounds
    if mjd < np.min(table["t_mjd"]):
        return None
    elif mjd > np.max(table["t_mjd"]):
        return None
    # find nearest mjd
    diffs = table["t_mjd"] - mjd
    idx = np.argmin(np.abs(diffs))

    row = table.iloc[idx]
    return row
```

Now, let's load the data and interpolate the positions. We'll do this in a separate step from updating the headers.

```python
from glob import glob
from astropy.io import fits
import os
import tqdm

filenames = sorted(glob("vcam*.fits"))

report_rows = []
for fname in tqdm.tqdm(filenames):
    header = fits.getheader(fname)
    data_time = header["MJD"]

    wpu_info = interpolate_wpu_log(data_time)
    # assemble table row-by-row
    row = {
        "filename": os.path.abspath(fname),
        "t_mjd": data_time,
        "cur_ang": header["RET-ANG1"],
        "cur_pos": header["RET-POS1"],
        "cur_mode": header["RET-MOD1"]
    }
    # if wpu_info is None, that means we don't have info
    # this will just make the rows blank in the table, and we will drop them later
    if wpu_info is not None:
        row.update({
            "wpu_mjd": wpu_info["t_mjd"],
            "wpu_ang": wpu_info["target"],
            "wpu_pos": wpu_info["position"],
            "wpu_mode": wpu_info["mode"],
        })
    report_rows.append(row)

report = pd.DataFrame(report_rows)
# now let's save this to file for posterity
report.to_csv("wpu_update_report.csv", index=False)
```

Finally, once we've verified that all our changes are sensical, we can proceed to update the headers.

```{admonition} 🚨: Data Modification
:class: warning

If you are changing open use data the highest degree of care is necessary. Make sure no data is deleted and no telemetry is lost! Make backups of files, if space allows. Double and triple-check before you run anyything, especially any `rm` commands!
```

```python
# in case we've exited python, load the update report
report = pd.read_csv("wpu_update_report.csv")
# first, let's drop any rows that we didn't get HWP info for
to_update = report.dropna(axis=0)
# now, simply iterate through the files
for row in tqdm.tqdm(to_update.itertuples()):
    with fits.open(row.filename, "update") as hdul:
        comments = hdul[0].header.comments
        hdul[0].header["RET-ANG1"] = row.wpu_ang, comments["RET-ANG1"]
        hdul[0].header["RET-POS1"] = row.wpu_pos, comments["RET-POS1"]
        hdul[0].header["RET-MOD1"] = row.wpu_mode, comments["RET-MOD1"]
```
