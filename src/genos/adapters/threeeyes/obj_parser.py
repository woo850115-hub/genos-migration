"""Parse 3eyes binary object files (objmon/o{nn}).

Each file contains up to 100 fixed-size records of 352 bytes.
vnum = file_index * 100 + record_index.
Empty records (name all null) are skipped.

Object struct layout (352 bytes, 32-bit Linux):
  offset 0:   char name[70]
  offset 70:  char etc[10]
  offset 80:  char description[80]
  offset 160: char key[3][20]
  offset 220: char use_output[80]
  offset 300: long value         (4)
  offset 304: short weight       (2)
  offset 306: char type          (1)
  offset 307: char adjustment    (1)
  offset 308: short shotsmax     (2)
  offset 310: short shotscur     (2)
  offset 312: short ndice        (2)
  offset 314: short sdice        (2)
  offset 316: short pdice        (2)
  offset 318: char armor         (1)
  offset 319: char wearflag      (1)
  offset 320: char magicpower    (1)
  offset 321: char magicrealm    (1)
  offset 322: short special      (2)
  offset 324: char flags[8]      (8)
  offset 332: char questnum      (1)
  offset 333: 3 padding + 4 pointers (16) = 19 bytes (ignored)
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import DiceRoll, Item, ItemAffect

from .binary_utils import (
    flags_to_bit_positions,
    read_byte,
    read_cstring,
    read_cstring_array,
    read_int,
    read_short,
    read_ubyte,
)
from .constants import SIZEOF_OBJECT, RECORDS_PER_FILE

logger = logging.getLogger(__name__)


def parse_obj_file(filepath: Path, file_index: int) -> list[Item]:
    """Parse a single object file and return a list of Items."""
    data = filepath.read_bytes()
    expected = SIZEOF_OBJECT * RECORDS_PER_FILE
    if len(data) < expected:
        logger.warning(
            "Object file %s is %d bytes, expected %d",
            filepath, len(data), expected,
        )

    items: list[Item] = []
    record_count = min(len(data) // SIZEOF_OBJECT, RECORDS_PER_FILE)

    for i in range(record_count):
        offset = i * SIZEOF_OBJECT
        record = data[offset : offset + SIZEOF_OBJECT]

        # Skip empty records (name is all null)
        if record[:70].rstrip(b"\x00") == b"":
            continue

        vnum = file_index * 100 + i
        items.append(_parse_object_record(record, vnum))

    return items


def _parse_object_record(rec: bytes, vnum: int) -> Item:
    """Parse a single 352-byte object record into an Item."""
    name = read_cstring(rec, 0, 70)
    etc = read_cstring(rec, 70, 10)
    description = read_cstring(rec, 80, 80)
    keys = read_cstring_array(rec, 160, 3, 20)
    use_output = read_cstring(rec, 220, 80)

    value = read_int(rec, 300)
    weight = read_short(rec, 304)
    obj_type = read_byte(rec, 306)
    adjustment = read_byte(rec, 307)
    shotsmax = read_short(rec, 308)
    shotscur = read_short(rec, 310)
    ndice = read_short(rec, 312)
    sdice = read_short(rec, 314)
    pdice = read_short(rec, 316)
    armor = read_byte(rec, 318)
    wearflag = read_ubyte(rec, 319)
    magicpower = read_byte(rec, 320)
    magicrealm = read_byte(rec, 321)
    special = read_short(rec, 322)
    flags_raw = rec[324:332]
    questnum = read_byte(rec, 332)

    # Build keywords from name + keys
    keyword_parts = [name] + [k for k in keys if k]
    keywords = " ".join(keyword_parts)

    # Map wearflag to wear_flags list
    wear_flags: list[int] = []
    if wearflag > 0:
        wear_flags.append(wearflag)

    # Object flags → extra_flags
    extra_flags = flags_to_bit_positions(flags_raw)

    # Affects from adjustment/armor
    affects: list[ItemAffect] = []
    if adjustment != 0:
        affects.append(ItemAffect(location=1, modifier=adjustment))  # APPLY_HITROLL
    if armor != 0:
        affects.append(ItemAffect(location=17, modifier=armor))  # APPLY_AC

    item = Item(
        vnum=vnum,
        keywords=keywords,
        short_description=name,
        long_description=description,
        action_description=use_output,
        item_type=obj_type,
        extra_flags=extra_flags,
        wear_flags=wear_flags,
        values=[value, ndice, sdice, pdice],
        weight=weight,
        cost=value,
        rent=0,
        timer=0,
        min_level=0,
        affects=affects,
    )

    # Store 3eyes-specific data in extensions via extra_descriptions
    # (UIR Item doesn't have extensions, but we can use values/affects)
    return item


def parse_all_objects(objmon_dir: Path) -> list[Item]:
    """Parse all object files in the objmon directory."""
    items: list[Item] = []
    for fpath in sorted(objmon_dir.glob("o[0-9][0-9]")):
        fname = fpath.name
        try:
            file_index = int(fname[1:])
        except ValueError:
            continue
        try:
            items.extend(parse_obj_file(fpath, file_index))
        except Exception as e:
            logger.warning("Error parsing %s: %s", fpath, e)
    return items
