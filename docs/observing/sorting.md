# Sorting, Selecting, and Processing VAMPIRES Data

VAMPIRES data is most efficiently organized through SQL-esque filtering and grouping based on the FITS headers for each file. The following is a guide for sorting and selecting VAMPIRES data for various scenarios. The code snippets will be written using Python's pandas library as well as sqlite-compatible SQL.

## Primer: Scraping Headers

To begin, we'll talk about how to scrape VAMPIRES data headers and quickly summarize them in preparation for the tutorials below. All these examples will assume you are working on `scexao6`.

First off we're going to make a user data folder to copy our data to for more efficient processing. Canonically you should be using `/mnt/userdata/<username>`, however if this disk is full you can also use `/mnt/tier1/<username>_userdata`. Change directories into this folder and use the following helper script to parse headers from any FITS file:

```bash
sc6 $ scxkw-header-table /mnt/sdata/<date>/ARCHIVED/vgen2/VMP*.fits.fz
```
by default this will output a CSV file to `header_table.csv`, but you can add a custom filename with the `-o/--output` flag:
```bash
sc6 $ scxkw-header-table -o 20251004_table.csv /mnt/sdata/20251004/ARCHIVED/vgen2/VMP*.fits.fz
```

Now, let's load the table into a pandas `DataFrame`

```python
import pandas as pd

table = pd.read_csv("header_table.csv")
```

If you prefer using sqlite, you can load the CSV table into memory and launch the interpreter with

```
sc6 $ sqlite3
```
```sql
.mode csv
.import header_table.csv headers
```

```{admonition} Tip: Multiple Nights
:class: tip

In order to scrape multiple nights' headers, simply concatenate the headers

    sc6 $ for d in ("20251004", "20251005", "20251006); do scxkw-header-table -o $d_headers.csv $d; done
    sc6 $ cat 202510*_headers.csv > 202510_combined_headers.csv
```

## Primer: Objects and Data Types

To summarize the data, we can quickly group it all by data type, object name, and camera, as well as printing the total number of files for each grouping.

In pandas
```python
table.value_counts(["OBJECT", "DATA-TYP", "OBS-MOD", "U_CAMERA"])
```
```
OBJECT    DATA-TYP  OBS-MOD   U_CAMERA
HR8206    OBJECT    IMAG_MBI  1           536
HIP99770  STANDARD  IMAG_MBI  1            44
BD254655  STANDARD  IMAG_MBI  1            38
HR8206    DARK      IMAG_MBI  1            21
BD254655  OBJECT    IMAG_MBI  1            13
```
## Filter for given objects

If you just want all the data for a given list of objects (and you weren't doing PDI), you can filter with `DATA-TYP` and `OBJECT` keywords

In pandas
```python
sub_table = table.query("`DATA-TYP` in ('OBJECT', 'STANDARD') and OBJECT in ('HR8206', 'HIP99770')")
```

## Filter for calibration files

To get all the calibration files for the night, just sort by `DATA-TYP`

Using pandas
```python
calib_table = table.query("`DATA-TYP` in ('DARK', 'SKYFLAT', 'FLAT', 'COMPARISON')")
```

## Filter data for PDI

Synchronized and deinterleaved data needs a little more filtering to discard the frames which could not be synchronized correctly.

Using pandas
```python
pdi_table = table.query("`DATA-TYP` == 'OBJECT' and OBJECT in ('ABAUR', 'HD34700') and U_SYNC and U_FLC != 'D'")
```

## Prepare filelist

Once you've filtered the data you should save the list of file paths to a text file.

```{admonition} Tip: Combining Tables
:class: tip

To combine two tables, say the subtable for your objects and the calibration files, merge them with

    comb_table = pd.concat((sub_table, calib_table))
```

Using pandas
```python
paths = "\n".join(str(p) for p in sub_table["path"])
with open("filelist.txt", "w") as fh:
    fh.write(paths); fh.write("\n")
```

## Decompressing and sorting data

Now that you have a list of the files you want to process, activate the `dpp` conda environment

```bash
sc6 $ conda activate dpp
```

and now use `dpp sort` to copy and decompress the data read in from the filelist

```bash
sc6 (dpp) $ dpp sort --decompress --copy $(< filelist.txt)
```

## Data processing

The rest of the data processing is explained in the [VAMPIRES DPP documentation](https://scexao-org.github.io/vampires_dpp/quickstart.html)
