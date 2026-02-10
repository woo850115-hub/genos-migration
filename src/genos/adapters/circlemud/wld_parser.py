"""CircleMUD .wld file parser.

Format per room:
    #<vnum>
    <name>~
    <description (multi-line)>
    ~
    <zone_num> <flags> <sector> <tba_unlinked> <tba_previous> <tba_map_x> [tba_map_y]
    [D<dir>
     <exit_desc>~
     <keyword>~
     <door_flags> <key_vnum> <dest_room>
    ]...
    [E
     <keywords>~
     <description>~
    ]...
    [T <trigger_vnum>]...
    S
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import Exit, ExtraDescription, Room

from .constants import asciiflag_to_int, int_to_flag_list

logger = logging.getLogger(__name__)


def parse_wld_file(filepath: str | Path) -> list[Room]:
    """Parse a single .wld file and return a list of Room objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding="utf-8", errors="replace")
    return parse_wld_text(text, str(filepath))


def parse_wld_text(text: str, source: str = "<string>") -> list[Room]:
    """Parse .wld format text into Room objects."""
    rooms: list[Room] = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip empty lines and look for #vnum
        if not line.startswith("#"):
            i += 1
            continue

        vnum_str = line[1:].strip()
        if vnum_str == "$" or vnum_str.startswith("$"):
            break  # End of file marker

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

    # Room stats line: zone_num flags sector [unlinked previous map_x [map_y]]
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 3:
            room.zone_number = int(parts[0])
            flags_int = asciiflag_to_int(parts[1])
            room.room_flags = int_to_flag_list(flags_int)
            room.sector_type = int(parts[2])
        if len(parts) >= 4:
            room.extensions["tba_unlinked"] = int(parts[3])
        if len(parts) >= 5:
            room.extensions["tba_previous"] = int(parts[4])
        if len(parts) >= 6:
            room.extensions["tba_map_x"] = int(parts[5])
        if len(parts) >= 7:
            room.extensions["tba_map_y"] = int(parts[6])

    # Parse optional sections: D (exits), E (extra descs), T (triggers), S (end)
    while i < len(lines):
        line = lines[i].rstrip()

        if line == "S":
            i += 1
            # In CircleMUD, T (trigger) lines come AFTER the S marker
            while i < len(lines):
                tline = lines[i].rstrip()
                if tline.startswith("T "):
                    try:
                        trg_vnum = int(tline.split()[1])
                        room.trigger_vnums.append(trg_vnum)
                    except (IndexError, ValueError):
                        pass
                    i += 1
                else:
                    break
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

        elif line.startswith("T "):
            try:
                trg_vnum = int(line.split()[1])
                room.trigger_vnums.append(trg_vnum)
            except (IndexError, ValueError):
                pass
            i += 1

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


def _read_tilde_string(lines: list[str], i: int) -> tuple[str, int]:
    """Read lines until a line ending with ~ is found.

    Returns the concatenated text (without the trailing ~) and the new index.
    """
    parts: list[str] = []
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.rstrip().endswith("~"):
            # Remove the trailing ~
            content = line.rstrip()[:-1]
            parts.append(content)
            break
        parts.append(line.rstrip("\n"))

    return "\n".join(parts).strip(), i
