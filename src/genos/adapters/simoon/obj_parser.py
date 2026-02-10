"""Simoon .obj file parser.

Format per object:
    #<vnum>
    <keywords>~
    <short_desc>~
    <long_desc>~
    <action_desc>~
    <type> <extra_flags> <wear_flags>
    <value0> <value1> <value2> <value3>
    <weight> <cost> <rent>
    [E
     <keywords>~
     <description>~
    ]...
    [A
     <location> <modifier>
    ]...

Differences from tbaMUD:
  - Type line is always 3 fields (not 13)
  - All flags are plain integers (not asciiflag)
  - No T (trigger) lines
  - File ends with $~ marker
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import ExtraDescription, Item, ItemAffect

logger = logging.getLogger(__name__)

_ENCODING = "euc-kr"


def parse_obj_file(filepath: str | Path) -> list[Item]:
    """Parse a single .obj file and return a list of Item objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding=_ENCODING, errors="replace")
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

    # Type/flags line: type extra_flags wear_flags (3 fields, plain integers)
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 3:
            item.item_type = int(parts[0])
            item.extra_flags = _parse_flags(parts[1])
            item.wear_flags = _parse_flags(parts[2])

    # Values line: value0 value1 value2 value3
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        item.values = [int(p) for p in parts[:4]] if len(parts) >= 4 else [0, 0, 0, 0]

    # Weight/cost/rent line
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

    # Optional sections: E (extra desc), A (affect)
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

        elif line.startswith("#") or line.startswith("$"):
            break

        else:
            i += 1

    return item, i


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
