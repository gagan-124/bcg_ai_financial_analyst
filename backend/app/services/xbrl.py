from pathlib import Path


class XBRLService:
    """Service handling parsing, extraction, and normalization of XBRL SEC filings."""

    def __init__(self) -> None:
        pass

    def parse_filing(self, file_path: Path) -> dict:
        """Parse XBRL/XML SEC 10-K or 10-Q filing."""
        raise NotImplementedError("XBRL service implementation pending.")
