"""Parser for CircleMUD/tbaMUD help files (lib/text/help/*.hlp).

Format per entry:
    KEYWORD1 KEYWORD2 ...

    Help text body spanning
    multiple lines...
    #<level>

- First line is space-separated keywords (case-insensitive)
- Blank line separates keywords from body
- '#<number>' terminates the entry; number is min_level required to see it
  (0 = mortal, 31+ = immortal)
- The index file lists which .hlp files to load, terminated by '$'
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import HelpEntry

logger = logging.getLogger(__name__)


def parse_help_dir(help_dir: str | Path, encoding: str = "utf-8") -> list[HelpEntry]:
    """Parse all help files listed in the index file."""
    help_dir = Path(help_dir)
    index_file = help_dir / "index"

    if not index_file.exists():
        # Fallback: just glob all .hlp files
        hlp_files = sorted(help_dir.glob("*.hlp"))
        entries: list[HelpEntry] = []
        for f in hlp_files:
            entries.extend(parse_help_file(f, encoding=encoding))
        return entries

    text = index_file.read_text(encoding=encoding, errors="replace")
    entries = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or line == "$":
            break
        hlp_path = help_dir / line
        if hlp_path.exists():
            entries.extend(parse_help_file(hlp_path, encoding=encoding))
        else:
            logger.warning("Help file listed in index not found: %s", hlp_path)
    return entries


def parse_help_file(filepath: str | Path, encoding: str = "utf-8") -> list[HelpEntry]:
    """Parse a single .hlp file into HelpEntry objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding=encoding, errors="replace")
    return _parse_help_text(text)


def _parse_help_text(text: str) -> list[HelpEntry]:
    """Parse help entries from raw text content."""
    entries: list[HelpEntry] = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        # Skip leading blank lines
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break

        # First non-blank line is keywords
        keyword_line = lines[i].strip()
        i += 1

        # Collect body until we hit #<number> or #<end>
        body_lines: list[str] = []
        min_level = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Check for terminator: # followed by digits
            if stripped.startswith("#"):
                rest = stripped[1:]
                # Pure # with no digits = level 0 terminator
                if not rest:
                    i += 1
                    break
                # #<digits> = min_level terminator
                try:
                    min_level = int(rest)
                    i += 1
                    break
                except ValueError:
                    # Not a terminator, just a regular line starting with #
                    pass

            body_lines.append(line)
            i += 1

        keywords = keyword_line.split()
        body = "\n".join(body_lines).strip()

        if keywords:
            entries.append(HelpEntry(
                keywords=keywords,
                min_level=min_level,
                text=body,
            ))

    return entries
