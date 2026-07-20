from pathlib import Path


class ImportError(Exception):
    pass


class UnsupportedFormatError(ImportError):
    def __init__(self, path: Path, observed_columns: tuple[str, ...]) -> None:
        self.path = path
        self.observed_columns = observed_columns
        super().__init__(
            f"Unsupported format in {path.name}: "
            f"{len(observed_columns)} columns, none matched a known signature."
        )


class CorruptFileError(ImportError):
    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Corrupt file {path.name}: {reason}")


class HeaderMismatchError(ImportError):
    def __init__(self, path: Path, missing: tuple[str, ...], unexpected: tuple[str, ...]) -> None:
        self.path = path
        self.missing = missing
        self.unexpected = unexpected
        super().__init__(
            f"Header mismatch in {path.name}: missing={list(missing)}, unexpected={list(unexpected)}"
        )
