"""Simoon command parser - thin wrapper for EUC-KR encoding + no min_match."""

from __future__ import annotations

from pathlib import Path

from genos.adapters.circlemud.cmd_parser import parse_cmd_file as _parse_cmd_file
from genos.uir.schema import Command

_ENCODING = "euc-kr"


def parse_cmd_file(filepath: str | Path) -> list[Command]:
    """Parse Simoon cmd_info[] with EUC-KR encoding, no min_match field."""
    return _parse_cmd_file(filepath, encoding=_ENCODING, has_min_match=False)
