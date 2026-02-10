"""Parse 3eyes monster talk/ddesc files.

Talk files (objmon/talk/{name}-{level}):
  Format: alternating keyword/response lines.
  keyword1
  response1
  keyword2
  response2
  ...

Ddesc files (objmon/ddesc/{name}_{level}):
  Entire file content is the detailed description.

File names encode the monster name and level, allowing merge
with parsed monster data by matching name + level.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_ENCODING = "euc-kr"


def parse_talk_file(filepath: Path) -> dict[str, str]:
    """Parse a talk file into a keyword→response dict."""
    try:
        text = filepath.read_text(encoding=_ENCODING, errors="replace").strip()
    except Exception as e:
        logger.warning("Error reading talk file %s: %s", filepath, e)
        return {}

    if not text:
        return {}

    lines = text.split("\n")
    talks: dict[str, str] = {}
    i = 0
    while i + 1 < len(lines):
        keyword = lines[i].strip()
        response = lines[i + 1].strip()
        if keyword:
            talks[keyword] = response
        i += 2
    return talks


def parse_ddesc_file(filepath: Path) -> str:
    """Parse a ddesc file — entire content is the detailed description."""
    try:
        return filepath.read_text(encoding=_ENCODING, errors="replace").strip()
    except Exception as e:
        logger.warning("Error reading ddesc file %s: %s", filepath, e)
        return ""


def parse_talk_filename(filename: str) -> tuple[str, int]:
    """Extract monster name and level from talk filename.

    Format: {name}-{level}  (e.g., '길라잡이-25')
    """
    parts = filename.rsplit("-", 1)
    if len(parts) == 2:
        try:
            return parts[0], int(parts[1])
        except ValueError:
            pass
    return filename, 0


def parse_ddesc_filename(filename: str) -> tuple[str, int]:
    """Extract monster name and level from ddesc filename.

    Format: {name}_{level}  (e.g., '검은_알_10')
    Note: name itself may contain underscores, so we split from the right.
    """
    parts = filename.rsplit("_", 1)
    if len(parts) == 2:
        try:
            return parts[0], int(parts[1])
        except ValueError:
            pass
    return filename, 0


def load_all_talks(talk_dir: Path) -> dict[str, dict[str, str]]:
    """Load all talk files. Returns {filename_key: {keyword: response}}."""
    result: dict[str, dict[str, str]] = {}
    if not talk_dir.is_dir():
        return result
    for fpath in talk_dir.iterdir():
        if fpath.is_file():
            talks = parse_talk_file(fpath)
            if talks:
                result[fpath.name] = talks
    return result


def load_all_ddescs(ddesc_dir: Path) -> dict[str, str]:
    """Load all ddesc files. Returns {filename_key: description}."""
    result: dict[str, str] = {}
    if not ddesc_dir.is_dir():
        return result
    for fpath in ddesc_dir.iterdir():
        if fpath.is_file():
            desc = parse_ddesc_file(fpath)
            if desc:
                result[fpath.name] = desc
    return result
