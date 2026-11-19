# luxdatareader

A collection of Python utilities for working with data.

## `read_file`: read any file with one call

`read_file` wraps pandas and picks the right reader for you, so you don't have to specify the file type.

```python
from luxdatareader import read_file

df = read_file("sales.csv")
df = read_file("report.xlsx", sheet_name="Q3")  # extra options go to the pandas reader
df = read_file("events.jsonl")
df = read_file("data.csv.gz")                    # compressed files work too
df = read_file("mystery_file")                   # no extension: detected from content
```

How it decides the format:

1. From the file extension, ignoring compression suffixes (`.gz`, `.bz2`, `.zip`, `.xz`, `.zst`, `.tar`).
2. If the extension is missing or unknown, from the file's first bytes (Parquet, Feather, ORC, HDF5, Excel, pickle, JSON, HTML, XML, or plain text).

For CSV and TXT files the delimiter is detected automatically unless you pass `sep=`.

Supported extensions: `csv tsv tab txt dat psv json jsonl ndjson xlsx xlsm xlsb xls ods parquet pq feather arrow orc pkl pickle html htm xml h5 hdf hdf5 dta sas7bdat xpt sav zsav`. Call `supported_formats()` for the list.

Only load pickle files you trust: unpickling can run arbitrary code.

## Install

```bash
pip install -e .            # pandas only: CSV, JSON, pickle, Stata, SAS
pip install -e ".[all]"     # adds Excel, Parquet/Feather/ORC, XML, HTML, HDF5, SPSS
```

You can also install single extras: `excel`, `parquet`, `xml`, `html`, `hdf`, `spss`.

## Tests

```bash
pip install -e ".[all,dev]"
pytest
```

## License

MIT. See [LICENSE](LICENSE).
