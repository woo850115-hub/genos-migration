"""Parser for CircleMUD/tbaMUD cmd_info[] array from src/interpreter.c.

tbaMUD format (6 fields):
    { "name", "min_match", POS_*, do_func, level, SCMD_* },

CircleMUD 3.0 / Simoon format (5 fields, no min_match):
    { "name", POS_*, do_func, level, subcmd },
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from genos.uir.schema import Command

logger = logging.getLogger(__name__)

# Match a cmd_info entry: { "name", ... },
# Captures everything between the braces
_ENTRY_RE = re.compile(
    r'\{\s*"([^"]*)"'   # field 1: command name
    r'\s*,\s*'
    r'(.*?)'            # remaining fields
    r'\s*\}',
    re.DOTALL,
)

# Position constants
_POS_MAP = {
    "POS_DEAD": 0, "POS_MORTALLYW": 1, "POS_INCAP": 2,
    "POS_STUNNED": 3, "POS_SLEEPING": 4, "POS_RESTING": 5,
    "POS_SITTING": 6, "POS_FIGHTING": 7, "POS_STANDING": 8,
}

# Level constants
_LEVEL_MAP = {
    "LVL_IMMORT": 101, "LVL_GOD": 110, "LVL_GRGOD": 112,
    "LVL_IMPL": 113, "LVL_BUILDER": 102,
    "LVL_BULSA": 113,  # Simoon-specific
    "LVL_ARCHWIZ": 112,  # Simoon-specific
}


def parse_cmd_file(
    filepath: str | Path,
    encoding: str = "utf-8",
    has_min_match: bool = True,
) -> list[Command]:
    """Parse cmd_info[] entries from an interpreter.c file."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding=encoding, errors="replace")
    return _parse_cmd_text(text, has_min_match=has_min_match)


def _parse_cmd_text(text: str, has_min_match: bool = True) -> list[Command]:
    """Parse cmd_info entries from raw C source text."""
    # Find the cmd_info[] array
    match = re.search(r'cmd_info\[\]\s*=\s*\{', text)
    if not match:
        logger.warning("cmd_info[] array not found")
        return []

    # Extract from array start to its closing. We find matching brace level.
    start = match.end()
    array_text = _extract_array_body(text, start)

    commands: list[Command] = []
    for m in _ENTRY_RE.finditer(array_text):
        name = m.group(1)
        rest = m.group(2)

        # Skip RESERVED entry
        if name == "RESERVED":
            continue

        cmd = _parse_entry(name, rest, has_min_match)
        if cmd:
            commands.append(cmd)

    return commands


def _extract_array_body(text: str, start: int) -> str:
    """Extract array body text, handling nested braces."""
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
        i += 1
    return text[start:i]


def _parse_entry(name: str, rest: str, has_min_match: bool) -> Command | None:
    """Parse remaining fields of a cmd_info entry."""
    # Remove inline comments
    rest = re.sub(r'/\*.*?\*/', '', rest, flags=re.DOTALL)

    # Split fields by comma
    fields = [f.strip() for f in rest.split(",") if f.strip()]

    try:
        if has_min_match:
            # tbaMUD: "min_match", POS_*, do_func, level, SCMD_*
            if len(fields) < 5:
                return None
            min_match = fields[0].strip('"')
            pos = _resolve_constant(fields[1], _POS_MAP)
            handler = fields[2].strip()
            level = _resolve_constant(fields[3], _LEVEL_MAP)
            subcmd = _resolve_constant(fields[4], {})
        else:
            # CircleMUD 3.0 / Simoon: POS_*, do_func, level, subcmd
            if len(fields) < 4:
                return None
            min_match = ""
            pos = _resolve_constant(fields[0], _POS_MAP)
            handler = fields[1].strip()
            level = _resolve_constant(fields[2], _LEVEL_MAP)
            subcmd = _resolve_constant(fields[3], {})
    except (ValueError, IndexError):
        logger.debug("Skipping unparseable cmd_info entry: %s", name)
        return None

    return Command(
        name=name,
        min_position=pos,
        min_level=level,
        min_match=min_match,
        handler=handler,
        subcmd=subcmd,
    )


def _resolve_constant(value: str, known: dict[str, int]) -> int:
    """Resolve a C constant to integer value."""
    value = value.strip()
    if value in known:
        return known[value]
    try:
        return int(value)
    except ValueError:
        # Unknown constant - return 0 as default
        return 0
