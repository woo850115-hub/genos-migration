"""Parse 3eyes help files (help/help.{n}).

Each file is a single help entry in EUC-KR encoding.
The first line (after stripping) is used as the keyword/title.
The rest of the file is the help body text.
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import HelpEntry

logger = logging.getLogger(__name__)

_ENCODING = "euc-kr"


def parse_help_file(filepath: Path) -> HelpEntry | None:
    """Parse a single help file into a HelpEntry."""
    try:
        text = filepath.read_text(encoding=_ENCODING, errors="replace").strip()
    except Exception as e:
        logger.warning("Error reading %s: %s", filepath, e)
        return None

    if not text:
        return None

    lines = text.split("\n", 1)
    keyword_line = lines[0].strip().rstrip(":")
    body = lines[1].strip() if len(lines) > 1 else ""

    # Extract keywords: split on whitespace, take meaningful tokens
    keywords = [k.strip() for k in keyword_line.split() if k.strip()]
    if not keywords:
        keywords = [filepath.stem]

    return HelpEntry(
        keywords=keywords,
        min_level=0,
        text=body,
    )


def parse_all_help(help_dir: Path) -> list[HelpEntry]:
    """Parse all help files in the help directory.

    Entries with empty keywords (all keywords are whitespace-only) are
    filtered out as they produce invalid SQL inserts.
    """
    entries: list[HelpEntry] = []
    for fpath in sorted(help_dir.glob("help.*")):
        entry = parse_help_file(fpath)
        if entry is not None:
            # Filter out entries where all keywords are empty/whitespace
            real_keywords = [k for k in entry.keywords if k.strip()]
            if not real_keywords:
                logger.debug("Skipping help entry with empty keywords: %s", fpath)
                continue
            entries.append(entry)
    return entries
