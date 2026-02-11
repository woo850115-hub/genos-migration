"""Parse 3eyes binary room files (rooms/r{nn}/r{nnnnn}).

Each room is stored as a separate binary file with variable length:
  1. room struct (480 bytes)
  2. int exit_count  → exit_ structs (44 bytes each)
  3. int monster_count → creature structs (each followed by inventory)
  4. int object_count → object structs (each followed by contained objects)
  5. int short_desc_len → short_desc string
  6. int long_desc_len → long_desc string
  7. int obj_desc_len → obj_desc string

Room struct layout (480 bytes):
  offset 0:   char name[80]
  offset 80:  short rom_num       (2)
  offset 82:  2 pad
  offset 84:  char* long_desc     (4) -- pointer, ignored on disk
  offset 88:  char* short_desc    (4) -- pointer, ignored
  offset 92:  char* obj_desc      (4) -- pointer, ignored
  offset 96:  short special       (2)
  offset 98:  char trap           (1)
  offset 99:  1 pad
  offset 100: short trapexit      (2)
  offset 102: char track[80]      (80)
  offset 182: char flags[8]       (8)
  offset 190: short random[10]    (20)
  offset 210: char traffic        (1)
  offset 211: 1 pad
  offset 212: lasttime perm_mon[10] (120)
  offset 332: lasttime perm_obj[10] (120)
  offset 452: long lVisitedTime   (4)
  offset 456: long established    (4)
  offset 460: char lolevel        (1)
  offset 461: char hilevel        (1)
  offset 462: 2 pad
  offset 464: 4 pointers (16)     -- ignored on disk
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import Exit, Room

from .binary_utils import (
    flags_to_bit_positions,
    read_byte,
    read_cstring,
    read_int,
    read_short,
    read_ubyte,
)
from .constants import SIZEOF_ROOM, SIZEOF_EXIT, SIZEOF_OBJECT, SIZEOF_CREATURE

logger = logging.getLogger(__name__)


def parse_room_file(filepath: Path) -> Room | None:
    """Parse a single room binary file."""
    data = filepath.read_bytes()
    if len(data) < SIZEOF_ROOM:
        return None

    # ── Fixed room struct ──
    name = read_cstring(data, 0, 80)
    rom_num = read_short(data, 80)
    special = read_short(data, 96)
    trap = read_byte(data, 98)
    trapexit = read_short(data, 100)
    track = read_cstring(data, 102, 80)
    flags_raw = data[182:190]
    room_flags = flags_to_bit_positions(flags_raw)

    random_mobs: list[int] = []
    for i in range(10):
        rm = read_short(data, 190 + i * 2)
        if rm > 0:
            random_mobs.append(rm)

    traffic = read_ubyte(data, 210)
    lolevel = read_ubyte(data, 460)
    hilevel = read_ubyte(data, 461)

    pos = SIZEOF_ROOM

    # ── Exits ──
    exits: list[Exit] = []
    if pos + 4 > len(data):
        return None
    exit_count = read_int(data, pos)
    pos += 4
    for i in range(exit_count):
        if pos + SIZEOF_EXIT > len(data):
            break
        exits.append(_parse_exit(data, pos, direction=i))
        pos += SIZEOF_EXIT

    # ── Monsters (skip) ──
    if pos + 4 <= len(data):
        mon_count = read_int(data, pos)
        pos += 4
        for _ in range(mon_count):
            pos = _skip_creature_with_inventory(data, pos)
            if pos < 0:
                break
    if pos < 0:
        pos = len(data)

    # ── Objects (skip) ──
    if pos + 4 <= len(data):
        obj_count = read_int(data, pos)
        pos += 4
        for _ in range(obj_count):
            pos = _skip_object_with_contents(data, pos)
            if pos < 0:
                break
    if pos < 0:
        pos = len(data)

    # ── Descriptions (order: short, long, obj — matching write_rom) ──
    short_desc, pos = _read_length_prefixed_string(data, pos)
    long_desc, pos = _read_length_prefixed_string(data, pos)
    obj_desc, pos = _read_length_prefixed_string(data, pos)

    return Room(
        vnum=rom_num,
        name=name,
        description=long_desc if long_desc else short_desc,
        zone_number=rom_num // 100,
        room_flags=room_flags,
        sector_type=0,
        exits=exits,
        extensions={
            "special": special,
            "trap": trap,
            "trapexit": trapexit,
            "track": track,
            "random_mobs": random_mobs,
            "traffic": traffic,
            "lolevel": lolevel,
            "hilevel": hilevel,
            "short_desc": short_desc,
            "obj_desc": obj_desc,
        },
    )


def _parse_exit(data: bytes, offset: int, direction: int) -> Exit:
    """Parse a 44-byte exit_ struct.

    exit_ layout:
      offset 0:  char name[20]
      offset 20: short room       (2)
      offset 22: char flags[4]    (4)
      offset 26: 2 pad
      offset 28: lasttime ltime   (12)
      offset 40: char key         (1)
      offset 41: 3 pad
    """
    name = read_cstring(data, offset, 20)
    dest_room = read_short(data, offset + 20)
    exit_flags_raw = data[offset + 22 : offset + 26]
    door_flags = 0
    flag_positions = flags_to_bit_positions(exit_flags_raw)
    for fp in flag_positions:
        door_flags |= 1 << fp
    key_num = read_byte(data, offset + 40)

    return Exit(
        direction=direction,
        destination=dest_room,
        description="",
        keyword=name,
        door_flags=door_flags,
        key_vnum=key_num if key_num > 0 else -1,
    )


def _skip_object_with_contents(data: bytes, pos: int) -> int:
    """Skip an object struct + its contained objects (recursive).

    Format: object(352) + int(contained_count) + contained objects...
    """
    if pos + SIZEOF_OBJECT + 4 > len(data):
        return -1
    pos += SIZEOF_OBJECT
    cnt = read_int(data, pos)
    pos += 4
    for _ in range(cnt):
        pos = _skip_object_with_contents(data, pos)
        if pos < 0:
            return -1
    return pos


def _skip_creature_with_inventory(data: bytes, pos: int) -> int:
    """Skip a creature struct + its inventory objects.

    Format: creature(1184) + int(inv_count) + objects...
    """
    if pos + SIZEOF_CREATURE + 4 > len(data):
        return -1
    pos += SIZEOF_CREATURE
    cnt = read_int(data, pos)
    pos += 4
    for _ in range(cnt):
        pos = _skip_object_with_contents(data, pos)
        if pos < 0:
            return -1
    return pos


def _read_length_prefixed_string(data: bytes, pos: int) -> tuple[str, int]:
    """Read an int-length-prefixed C string (EUC-KR)."""
    if pos + 4 > len(data):
        return "", pos
    length = read_int(data, pos)
    pos += 4
    if length <= 0:
        return "", pos
    if pos + length > len(data):
        return "", pos + length
    raw = data[pos : pos + length]
    null_idx = raw.find(b"\x00")
    if null_idx >= 0:
        raw = raw[:null_idx]
    text = raw.decode("euc-kr", errors="replace").strip()
    return text, pos + length


def parse_all_rooms(rooms_dir: Path) -> list[Room]:
    """Parse all room files in the rooms directory.

    Room files are organized as rooms/r{nn}/r{nnnnn}.
    Rooms with vnum=0 are filtered out (invalid/placeholder entries).
    Duplicates by vnum are deduplicated, keeping the first occurrence.
    """
    rooms: list[Room] = []
    seen_vnums: set[int] = set()
    for zone_dir in sorted(rooms_dir.glob("r[0-9][0-9]")):
        if not zone_dir.is_dir():
            continue
        for room_file in sorted(zone_dir.glob("r[0-9][0-9][0-9][0-9][0-9]")):
            try:
                room = parse_room_file(room_file)
                if room is not None and room.vnum != 0 and room.vnum not in seen_vnums:
                    seen_vnums.add(room.vnum)
                    rooms.append(room)
            except Exception as e:
                logger.warning("Error parsing %s: %s", room_file, e)
    return rooms
