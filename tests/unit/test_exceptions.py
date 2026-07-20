from pathlib import Path

from solgreen.importer.exceptions import (
    CorruptFileError,
    HeaderMismatchError,
    ImportError,
    UnsupportedFormatError,
)


def test_unsupported_format_error_contains_path_and_columns(tmp_path: Path) -> None:
    path = tmp_path / "x.csv"
    exc = UnsupportedFormatError(path, ("a", "b", "c"))
    assert exc.path == path
    assert exc.observed_columns == ("a", "b", "c")
    assert "x.csv" in str(exc)
    assert isinstance(exc, ImportError)


def test_corrupt_file_error_carries_reason(tmp_path: Path) -> None:
    path = tmp_path / "broken.xlsx"
    exc = CorruptFileError(path, "zip header invalid")
    assert exc.path == path
    assert exc.reason == "zip header invalid"
    assert "broken.xlsx" in str(exc)


def test_header_mismatch_error_lists_missing_and_unexpected(tmp_path: Path) -> None:
    path = tmp_path / "flow.csv"
    exc = HeaderMismatchError(path, missing=("SoC(%)",), unexpected=("foo",))
    assert exc.missing == ("SoC(%)",)
    assert exc.unexpected == ("foo",)
    assert "missing=" in str(exc)
    assert "unexpected=" in str(exc)
