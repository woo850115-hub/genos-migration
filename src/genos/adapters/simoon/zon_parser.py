"""Simoon .zon file parser.

Format:
    #<zone_vnum>
    <name>~
    <builders>~
    <top> <lifespan> <reset_mode>
    <reset commands...>
    S

Differences from tbaMUD:
  - Zone params line is 3 fields: top lifespan reset_mode (not bot top lifespan reset_mode flags ...)
  - bot is inferred as zone_vnum * 100
  - No zone_flags, min_level, max_level
  - Reset command format is same as tbaMUD
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import Zone, ZoneResetCommand

logger = logging.getLogger(__name__)

_ENCODING = "euc-kr"


def parse_zon_file(filepath: str | Path) -> list[Zone]:
    """Parse a single .zon file and return a list of Zone objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding=_ENCODING, errors="replace")
    return parse_zon_text(text, str(filepath))


def parse_zon_text(text: str, source: str = "<string>") -> list[Zone]:
    """Parse .zon format text into Zone objects."""
    zones: list[Zone] = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if not line.startswith("#"):
            i += 1
            continue

        vnum_str = line[1:].strip()
        if vnum_str.startswith("$"):
            break

        try:
            vnum = int(vnum_str)
        except ValueError:
            i += 1
            continue

        i += 1
        zone, i = _parse_single_zone(vnum, lines, i, source)
        if zone:
            zones.append(zone)

    return zones


def _parse_single_zone(
    vnum: int, lines: list[str], i: int, source: str
) -> tuple[Zone | None, int]:
    """Parse a single zone block."""
    zone = Zone(vnum=vnum)

    # Zone name~
    zone.name, i = _read_tilde_string(lines, i)

    # Builders~ (often <NONE!>~)
    zone.builders, i = _read_tilde_string(lines, i)

    # Zone params line: top lifespan reset_mode (3 fields)
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 3:
            zone.top = int(parts[0])
            zone.lifespan = int(parts[1])
            zone.reset_mode = int(parts[2])
            # bot is inferred from zone vnum
            zone.bot = vnum * 100

    # Reset commands until 'S'
    while i < len(lines):
        line = lines[i].rstrip()

        if line == "S" or line.startswith("$"):
            i += 1
            break

        if not line or line.startswith("*"):
            i += 1
            continue

        cmd = _parse_reset_command(line)
        if cmd:
            zone.reset_commands.append(cmd)
        i += 1

    return zone, i


def _parse_reset_command(line: str) -> ZoneResetCommand | None:
    """Parse a single zone reset command line."""
    if "\t" in line:
        cmd_part, comment = line.split("\t", 1)
    else:
        cmd_part = line
        comment = ""

    parts = cmd_part.split()
    if not parts:
        return None

    cmd_char = parts[0]
    if cmd_char not in ("M", "O", "G", "E", "P", "D", "R", "T", "V"):
        return None

    cmd = ZoneResetCommand(command=cmd_char, comment=comment.strip())

    try:
        if len(parts) >= 2:
            cmd.if_flag = int(parts[1])
        if len(parts) >= 3:
            cmd.arg1 = int(parts[2])
        if len(parts) >= 4:
            cmd.arg2 = int(parts[3])
        if len(parts) >= 5:
            cmd.arg3 = int(parts[4])
        if len(parts) >= 6:
            cmd.arg4 = int(parts[5])
    except ValueError:
        pass

    return cmd


def _read_tilde_string(lines: list[str], i: int) -> tuple[str, int]:
    """Read lines until a line ending with ~ is found."""
    parts: list[str] = []
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.rstrip().endswith("~"):
            content = line.rstrip()[:-1]
            parts.append(content)
            break
        parts.append(line.rstrip("\n"))
    return "\n".join(parts).strip(), i
