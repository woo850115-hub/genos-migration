"""Simoon help file parser - thin wrapper for EUC-KR encoding."""

from __future__ import annotations

from pathlib import Path

from genos.adapters.circlemud.help_parser import parse_help_dir as _parse_help_dir
from genos.adapters.circlemud.help_parser import parse_help_file as _parse_help_file
from genos.uir.schema import HelpEntry

_ENCODING = "euc-kr"


def parse_help_dir(help_dir: str | Path) -> list[HelpEntry]:
    """Parse all Simoon help files with EUC-KR encoding."""
    return _parse_help_dir(help_dir, encoding=_ENCODING)


def parse_help_file(filepath: str | Path) -> list[HelpEntry]:
    """Parse a single Simoon .hlp file with EUC-KR encoding."""
    return _parse_help_file(filepath, encoding=_ENCODING)
