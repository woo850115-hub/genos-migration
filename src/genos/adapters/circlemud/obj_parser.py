"""CircleMUD .obj file parser.

Format per object:
    #<vnum>
    <keywords>~
    <short_desc>~
    <long_desc>~
    <action_desc>~
    <type> <extra_flags> <wear_flags> [13 fields in tbaMUD]
    <value0> <value1> <value2> <value3>
    <weight> <cost> <rent> [timer] [min_level]
    [E
     <keywords>~
     <description>~
    ]...
    [A
     <location> <modifier>
    ]...
    [T <trigger_vnum>]...
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import ExtraDescription, Item, ItemAffect

from .constants import asciiflag_to_int, int_to_flag_list

logger = logging.getLogger(__name__)


def parse_obj_file(filepath: str | Path) -> list[Item]:
    """Parse a single .obj file and return a list of Item objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding="utf-8", errors="replace")
    return parse_obj_text(text, str(filepath))


def parse_obj_text(text: str, source: str = "<string>") -> list[Item]:
    """Parse .obj format text into Item objects."""
    items: list[Item] = []
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
        item, i = _parse_single_obj(vnum, lines, i, source)
        if item:
            items.append(item)

    return items


def _parse_single_obj(
    vnum: int, lines: list[str], i: int, source: str
) -> tuple[Item | None, int]:
    """Parse a single object block starting after #vnum."""
    item = Item(vnum=vnum)

    # keywords~
    item.keywords, i = _read_tilde_string(lines, i)
    # short_desc~
    item.short_description, i = _read_tilde_string(lines, i)
    # long_desc~
    item.long_description, i = _read_tilde_string(lines, i)
    # action_desc~
    item.action_description, i = _read_tilde_string(lines, i)

    # Type/flags line - two formats:
    #   Old (4 fields): type extra_flags wear_flags [aff_flags]
    #   tbaMUD 128-bit (13 fields): type ef0 ef1 ef2 ef3 wf0 wf1 wf2 wf3 af0 af1 af2 af3
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 13:
            # tbaMUD 128-bit format
            item.item_type = int(parts[0])
            extra_int = asciiflag_to_int(parts[1])
            item.extra_flags = int_to_flag_list(extra_int)
            wear_int = asciiflag_to_int(parts[5])  # wf0 is at index 5
            item.wear_flags = int_to_flag_list(wear_int)
        elif len(parts) >= 3:
            # Old 3-4 field format
            item.item_type = int(parts[0])
            extra_int = asciiflag_to_int(parts[1])
            item.extra_flags = int_to_flag_list(extra_int)
            wear_int = asciiflag_to_int(parts[2])
            item.wear_flags = int_to_flag_list(wear_int)

    # Values line: value0 value1 value2 value3
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        item.values = [int(p) for p in parts[:4]] if len(parts) >= 4 else [0, 0, 0, 0]

    # Weight/cost/rent line: weight cost rent [timer] [min_level]
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 3:
            item.weight = int(parts[0])
            item.cost = int(parts[1])
            item.rent = int(parts[2])
        if len(parts) >= 4:
            item.timer = int(parts[3])
        if len(parts) >= 5:
            item.min_level = int(parts[4])

    # Optional sections: E (extra desc), A (affect), T (trigger)
    while i < len(lines):
        line = lines[i].rstrip()

        if line == "E":
            i += 1
            ed = ExtraDescription()
            ed.keywords, i = _read_tilde_string(lines, i)
            ed.description, i = _read_tilde_string(lines, i)
            item.extra_descriptions.append(ed)

        elif line == "A":
            i += 1
            if i < len(lines):
                parts = lines[i].rstrip().split()
                i += 1
                if len(parts) >= 2:
                    item.affects.append(
                        ItemAffect(location=int(parts[0]), modifier=int(parts[1]))
                    )

        elif line.startswith("T "):
            try:
                trg_vnum = int(line.split()[1])
                item.trigger_vnums.append(trg_vnum)
            except (IndexError, ValueError):
                pass
            i += 1

        elif line.startswith("#") or line.startswith("$"):
            break

        else:
            i += 1

    return item, i


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
