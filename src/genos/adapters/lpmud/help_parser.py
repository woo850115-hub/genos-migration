"""Parse .help files from 도움말/ directory into UIR HelpEntry objects."""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import HelpEntry

from .lpc_parser import strip_help_color_codes

logger = logging.getLogger(__name__)


def parse_all_help(
    help_dir: Path,
    encoding: str = "euc-kr",
) -> list[HelpEntry]:
    """Parse all .help files in the help directory."""
    entries: list[HelpEntry] = []

    if not help_dir.is_dir():
        return entries

    for help_file in sorted(help_dir.glob("*.help")):
        try:
            entry = _parse_help_file(help_file, encoding)
            if entry:
                entries.append(entry)
        except Exception as e:
            logger.debug("Error parsing help %s: %s", help_file, e)

    return entries


def _parse_help_file(filepath: Path, encoding: str) -> HelpEntry | None:
    """Parse a single .help file."""
    raw = filepath.read_bytes()
    text = raw.decode(encoding, errors="replace")

    # Keyword is the filename without extension
    keyword = filepath.stem

    # Strip color codes
    text = strip_help_color_codes(text).strip()

    if not text:
        return None

    return HelpEntry(
        keywords=[keyword],
        text=text,
    )
