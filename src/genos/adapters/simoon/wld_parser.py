"""Simoon .wld file parser.

Format per room:
    #<vnum>
    <name>~
    <description (multi-line)>
    ~
    <zone_num> <flags> <sector>
    [D<dir>
     <exit_desc>~
     <keyword>~
     <door_flags> <key_vnum> <dest_room>
    ]...
    [E
     <keywords>~
     <description>~
    ]...
    S

Differences from tbaMUD:
  - Room stats line is 3 fields (not 7+)
  - Flags are plain integers (not asciiflag)
  - No T (trigger) lines
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import Exit, ExtraDescription, Room

logger = logging.getLogger(__name__)

_ENCODING = "euc-kr"


def parse_wld_file(filepath: str | Path) -> list[Room]:
    """Parse a single .wld file and return a list of Room objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding=_ENCODING, errors="replace")
    return parse_wld_text(text, str(filepath))


def parse_wld_text(text: str, source: str = "<string>") -> list[Room]:
    """Parse .wld format text into Room objects."""
    rooms: list[Room] = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if not line.startswith("#"):
            i += 1
            continue

        vnum_str = line[1:].strip()
        if vnum_str == "$" or vnum_str.startswith("$"):
            break

        try:
            vnum = int(vnum_str)
        except ValueError:
            i += 1
            continue

        i += 1
        room, i = _parse_single_room(vnum, lines, i, source)
        if room:
            rooms.append(room)

    return rooms


def _parse_single_room(
    vnum: int, lines: list[str], i: int, source: str
) -> tuple[Room | None, int]:
    """Parse a single room block starting after the #vnum line."""
    room = Room(vnum=vnum)

    # Name (until ~)
    room.name, i = _read_tilde_string(lines, i)

    # Description (until ~)
    room.description, i = _read_tilde_string(lines, i)

    # Room stats line: zone_num flags sector (3 fields)
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 3:
            room.zone_number = int(parts[0])
            room.room_flags = _parse_flags(parts[1])
            room.sector_type = int(parts[2])

    # Parse optional sections: D (exits), E (extra descs), S (end)
    while i < len(lines):
        line = lines[i].rstrip()

        if line == "S":
            i += 1
            break

        if line.startswith("D"):
            direction = int(line[1:].strip())
            i += 1
            exit_obj, i = _parse_exit(direction, lines, i)
            if exit_obj:
                room.exits.append(exit_obj)

        elif line == "E":
            i += 1
            ed, i = _parse_extra_desc(lines, i)
            if ed:
                room.extra_descriptions.append(ed)

        else:
            i += 1

    return room, i


def _parse_exit(
    direction: int, lines: list[str], i: int
) -> tuple[Exit | None, int]:
    """Parse an exit block (after D<dir> line)."""
    exit_obj = Exit(direction=direction, destination=-1)

    # Exit description (until ~)
    exit_obj.description, i = _read_tilde_string(lines, i)

    # Keywords (until ~)
    exit_obj.keyword, i = _read_tilde_string(lines, i)

    # door_flags key_vnum destination
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 3:
            exit_obj.door_flags = int(parts[0])
            exit_obj.key_vnum = int(parts[1])
            exit_obj.destination = int(parts[2])

    return exit_obj, i


def _parse_extra_desc(
    lines: list[str], i: int
) -> tuple[ExtraDescription | None, int]:
    """Parse an extra description block (after E line)."""
    ed = ExtraDescription()
    ed.keywords, i = _read_tilde_string(lines, i)
    ed.description, i = _read_tilde_string(lines, i)
    return ed, i


def _parse_flags(flag_str: str) -> list[int]:
    """Parse a flag field (plain integer or asciiflag) into bit position list."""
    return _int_to_flag_list(_flag_to_int(flag_str))


def _flag_to_int(flag_str: str) -> int:
    """Convert a flag string to int. Supports plain integers and asciiflag."""
    if not flag_str or flag_str == "0":
        return 0
    try:
        return int(flag_str)
    except ValueError:
        pass
    # asciiflag: a-z = bits 0-25, A-Z = bits 26-51
    result = 0
    for ch in flag_str:
        if ch.islower():
            result |= 1 << (ord(ch) - ord('a'))
        elif ch.isupper():
            result |= 1 << (26 + ord(ch) - ord('A'))
    return result


def _int_to_flag_list(value: int) -> list[int]:
    """Convert an integer bitvector to a list of set bit positions."""
    flags = []
    bit = 0
    while value > 0:
        if value & 1:
            flags.append(bit)
        value >>= 1
        bit += 1
    return flags


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
