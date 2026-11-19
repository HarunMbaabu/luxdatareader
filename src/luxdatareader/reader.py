"""Read any tabular file into a pandas DataFrame without specifying its type."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

import pandas as pd

PathLike = str | os.PathLike

# Compression suffixes pandas can decompress on its own (compression="infer").
_COMPRESSION_SUFFIXES = {".gz", ".bz2", ".zip", ".xz", ".zst", ".tar"}


def _read_delimited(path: PathLike, **kwargs: Any) -> pd.DataFrame:
    """CSV/TSV/TXT reader that detects the delimiter unless one is given."""
    if "sep" not in kwargs and "delimiter" not in kwargs:
        kwargs["sep"] = None  # let pandas' python engine sniff it
        kwargs.setdefault("engine", "python")
    return pd.read_csv(path, **kwargs)


def _read_json(path: PathLike, **kwargs: Any) -> pd.DataFrame:
    """JSON reader that falls back to JSON Lines when needed."""
    try:
        return pd.read_json(path, **kwargs)
    except ValueError:
        if "lines" in kwargs:
            raise
        return pd.read_json(path, lines=True, **kwargs)


def _read_html(path: PathLike, **kwargs: Any) -> pd.DataFrame:
    """Return the first table found in an HTML file (pass match= to choose)."""
    return pd.read_html(path, **kwargs)[0]


# Extension -> reader. Readers accept (path, **kwargs) and return a DataFrame.
READERS: dict[str, Callable[..., pd.DataFrame]] = {
    ".csv": _read_delimited,
    ".tsv": lambda p, **kw: pd.read_csv(p, **{"sep": "\t", **kw}),
    ".tab": lambda p, **kw: pd.read_csv(p, **{"sep": "\t", **kw}),
    ".txt": _read_delimited,
    ".dat": _read_delimited,
    ".psv": lambda p, **kw: pd.read_csv(p, **{"sep": "|", **kw}),
    ".json": _read_json,
    ".jsonl": lambda p, **kw: pd.read_json(p, **{"lines": True, **kw}),
    ".ndjson": lambda p, **kw: pd.read_json(p, **{"lines": True, **kw}),
    ".xlsx": pd.read_excel,
    ".xlsm": pd.read_excel,
    ".xlsb": pd.read_excel,
    ".xls": pd.read_excel,
    ".ods": pd.read_excel,
    ".parquet": pd.read_parquet,
    ".pq": pd.read_parquet,
    ".feather": pd.read_feather,
    ".arrow": pd.read_feather,
    ".orc": pd.read_orc,
    ".pkl": pd.read_pickle,
    ".pickle": pd.read_pickle,
    ".html": _read_html,
    ".htm": _read_html,
    ".xml": pd.read_xml,
    ".h5": pd.read_hdf,
    ".hdf": pd.read_hdf,
    ".hdf5": pd.read_hdf,
    ".dta": pd.read_stata,
    ".sas7bdat": pd.read_sas,
    ".xpt": pd.read_sas,
    ".sav": pd.read_spss,
    ".zsav": pd.read_spss,
}


def supported_formats() -> list[str]:
    """Return the file extensions read_file() understands."""
    return sorted(READERS)


def _detect_extension(path: Path) -> str | None:
    """Get the meaningful extension, skipping a compression suffix (data.csv.gz -> .csv)."""
    suffixes = [s.lower() for s in path.suffixes]
    while suffixes and suffixes[-1] in _COMPRESSION_SUFFIXES:
        suffixes.pop()
    if suffixes and suffixes[-1] in READERS:
        return suffixes[-1]
    return None


def _sniff_content(path: Path) -> str | None:
    """Guess the format from the file's first bytes when the extension is missing or unknown."""
    with open(path, "rb") as f:
        head = f.read(2048)

    if head.startswith(b"PAR1"):
        return ".parquet"
    if head.startswith(b"ARROW1"):
        return ".feather"
    if head.startswith(b"ORC"):
        return ".orc"
    if head.startswith(b"\x89HDF"):
        return ".h5"
    if head.startswith(b"\xd0\xcf\x11\xe0"):  # legacy OLE2 Excel
        return ".xls"
    if head.startswith(b"PK"):  # zip container: xlsx/ods, or a zipped csv
        return ".xlsx" if b"xl/" in head or b"[Content_Types]" in head else None
    if head.startswith(b"\x80"):  # pickle protocol 2+
        return ".pkl"

    text = head.decode("utf-8", errors="ignore").lstrip("﻿").lstrip()
    if text.startswith(("{", "[")):
        return ".json"
    if text.lower().startswith(("<!doctype html", "<html")):
        return ".html"
    if text.startswith("<"):
        return ".xml"
    if text:
        return ".csv"  # plain text: read as delimited, delimiter is auto-detected
    return None


def read_file(path: PathLike, **kwargs: Any) -> pd.DataFrame:
    """Read any supported file into a DataFrame, detecting the format automatically.

    The format is chosen from the file extension (compression suffixes like
    ``.gz`` are handled), and if the extension is missing or unknown, from the
    file's contents. Extra keyword arguments are passed to the underlying
    pandas reader, e.g. ``read_file("book.xlsx", sheet_name="Sales")``.

    Args:
        path: Path to the file.
        **kwargs: Options forwarded to the pandas reader.

    Returns:
        A pandas DataFrame.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the format can't be determined.
        ImportError: If the format needs an optional dependency that isn't installed.
    """
    path = Path(path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"No such file: {path}")

    ext = _detect_extension(path) or _sniff_content(path)
    if ext is None:
        raise ValueError(
            f"Could not determine the format of {path.name!r}. "
            f"Supported extensions: {', '.join(supported_formats())}"
        )

    try:
        return READERS[ext](path, **kwargs)
    except ImportError as e:
        raise ImportError(
            f"Reading {ext} files needs an extra package: {e}. "
            "Install everything with: pip install 'luxdatareader[all]'"
        ) from e
