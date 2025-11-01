# WTXmeso

Data loading functions for (West Texas Mesonet)[https://www.mesonet.ttu.edu/] data.

Does not provide any a

## Usage instructions

### Step 1: create a `Reader` object
```python
from wtxmeso import *
reader = Reader("./stationinfo.xlsx", "all")
```

A station information Excel spreadsheet file (likely called something like `stationinfo.xlsx` or `stationfile.xls`) should be provided to the `Reader` on initialization to load all relevant station metadata.

The columns to be loaded when reading files should be specified in one of the following ways:
- A string (`"all"`, `"atmospheric"`, or `"agricultural"`) specifying whether the data has just the 16 agricultural columns, just the 10 agricultural columns, or all 26
- A list of either:
    - Integers representing the column IDs to be included (as identified in [header.csv](./wtxmeso/data/header.csv))
    - Strings representing the exact column names to be included (e.g. `"2m Temp"`, `"barometric pressure"`, etc.)

Note that if passing a list of column IDs or names, the first three (1,2,3 or `"UTC Date"`, `"UTC Time"`, `"Station ID"`) must be passed along with the specific measurements. The order of the list should be exactly the order of the columns in the data files.

### Step 2: load data
To use the above `Reader` object to load the data from a directory located at `datapath` containing data CSV/TXT files (with filenames corresponding to the station base ID):
```python
data = reader.read_directory(datapath)
```

The above `read_directory` function call returns a dictionary mapping 4-letter station IDs (str) to dataframes (Pandas DataFrame objects).

If the filenames do not correspond to the 4-letter station IDs, or you otherwise wish to individually read in, specific files may be loaded using `reader.read_file(path, name=None)`. If the optional argument `name` is omitted, it will be inferred from the file name.

All dataframes which have been loaded may also be accessed (even without storing the return value in a variable like `data` above) by reading them from the stations:

```python
for s in reader.stations:
    df = s.df # All data loaded from s
    # ... do something with df ...
```

`reader.stations` is a list of `Station` objects, which each contain station metadata read from the station info Excel file as well as any data associated with that station which has been read in. An alternative view into these same `Station` objects is `reader.stations_map`, a dictionary mapping 4-letter station IDs (str) to their corresponding `Station` objects.

For a `Station`, the `data` attribute contains a list of all loaded dataframes corresponding to that station. The `df` attribute, on access, returns a new dataframe which is a concatenation of all of these loaded dataframes (or `None` if the station has no associated data).

`Station`s are uniquely read & stored in a `Reader` object; typically a single `Reader` should be used across code rather than several.

### Other notes
A `Reader` has an attribute `units`, which is a dictionary mapping column names to their units (as specified in )
