import pandas as pd
import pytest

from luxdatareader import read_file, supported_formats

DF = pd.DataFrame({"name": ["a", "b", "c"], "value": [1, 2, 3]})


def test_csv(tmp_path):
    p = tmp_path / "data.csv"
    DF.to_csv(p, index=False)
    pd.testing.assert_frame_equal(read_file(p), DF)


def test_semicolon_delimiter_detected(tmp_path):
    p = tmp_path / "data.txt"
    DF.to_csv(p, index=False, sep=";")
    pd.testing.assert_frame_equal(read_file(p), DF)


def test_tsv(tmp_path):
    p = tmp_path / "data.tsv"
    DF.to_csv(p, index=False, sep="\t")
    pd.testing.assert_frame_equal(read_file(p), DF)


def test_compressed_csv(tmp_path):
    p = tmp_path / "data.csv.gz"
    DF.to_csv(p, index=False)
    pd.testing.assert_frame_equal(read_file(p), DF)


def test_json_and_jsonl(tmp_path):
    p = tmp_path / "data.json"
    DF.to_json(p, orient="records")
    pd.testing.assert_frame_equal(read_file(p), DF)

    p = tmp_path / "data.jsonl"
    DF.to_json(p, orient="records", lines=True)
    pd.testing.assert_frame_equal(read_file(p), DF)


def test_pickle(tmp_path):
    p = tmp_path / "data.pkl"
    DF.to_pickle(p)
    pd.testing.assert_frame_equal(read_file(p), DF)


def test_excel(tmp_path):
    pytest.importorskip("openpyxl")
    p = tmp_path / "data.xlsx"
    DF.to_excel(p, index=False)
    pd.testing.assert_frame_equal(read_file(p), DF)


def test_parquet(tmp_path):
    pytest.importorskip("pyarrow")
    p = tmp_path / "data.parquet"
    DF.to_parquet(p)
    pd.testing.assert_frame_equal(read_file(p), DF)


@pytest.mark.parametrize(
    "writer",
    [
        lambda df, p: df.to_csv(p, index=False),
        lambda df, p: df.to_json(p, orient="records"),
        lambda df, p: df.to_pickle(p),
    ],
)
def test_no_extension_sniffed(tmp_path, writer):
    p = tmp_path / "mystery"
    writer(DF, p)
    pd.testing.assert_frame_equal(read_file(p), DF)


def test_sniffed_parquet_without_extension(tmp_path):
    pytest.importorskip("pyarrow")
    p = tmp_path / "mystery"
    DF.to_parquet(p)
    pd.testing.assert_frame_equal(read_file(p), DF)


def test_kwargs_forwarded(tmp_path):
    p = tmp_path / "data.csv"
    DF.to_csv(p, index=False)
    assert list(read_file(p, usecols=["value"]).columns) == ["value"]


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        read_file("does/not/exist.csv")


def test_empty_unknown_file(tmp_path):
    p = tmp_path / "empty.bin"
    p.write_bytes(b"")
    with pytest.raises(ValueError):
        read_file(p)


def test_supported_formats():
    assert ".csv" in supported_formats()
    assert ".parquet" in supported_formats()
