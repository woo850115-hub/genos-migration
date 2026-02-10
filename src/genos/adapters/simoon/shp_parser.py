"""Simoon .shp file parser — thin wrapper over circlemud shp_parser.

The Simoon shop format is identical to CircleMUD v3.0,
only the file encoding differs (EUC-KR instead of UTF-8).
"""

from __future__ import annotations

from pathlib import Path

from genos.adapters.circlemud.shp_parser import parse_shp_text
from genos.uir.schema import Shop

_ENCODING = "euc-kr"


def parse_shp_file(filepath: str | Path) -> list[Shop]:
    """Parse a single .shp file (EUC-KR) and return a list of Shop objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding=_ENCODING, errors="replace")
    return parse_shp_text(text, str(filepath))
