"""Parse LPC room files (inherit LIB_ROOM) into UIR Room objects."""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import Exit, ExtraDescription, Room

from .lpc_parser import (
    extract_inherit,
    extract_int_call,
    extract_mapping,
    extract_prop_calls,
    extract_string_call,
    extract_void_call,
    read_lpc_file,
    strip_color_codes,
)
from .vnum_generator import VnumGenerator

logger = logging.getLogger(__name__)

# Korean direction names -> standard direction numbers
DIR_MAP = {
    "북": 0, "동": 1, "남": 2, "서": 3, "위": 4, "아래": 5,
    "북동": 6, "북서": 7, "남동": 8, "남서": 9,
}


def parse_all_rooms(
    lib_dir: Path,
    room_dirs: list[str],
    vnum_gen: VnumGenerator,
    encoding: str = "euc-kr",
) -> tuple[list[Room], dict[int, dict[str, str]]]:
    """Parse all room .c files from room directories.

    Returns:
        (rooms, pending_exits) where pending_exits maps
        room_vnum -> {direction_str: destination_path} for 2-pass resolution.
    """
    rooms: list[Room] = []
    pending_exits: dict[int, dict[str, str]] = {}

    for room_dir_name in room_dirs:
        room_base = lib_dir / room_dir_name
        if not room_base.is_dir():
            continue

        for c_file in _find_room_files(room_base):
            try:
                room, exits = parse_room_file(c_file, lib_dir, vnum_gen, encoding)
                if room:
                    rooms.append(room)
                    if exits:
                        pending_exits[room.vnum] = exits
            except Exception as e:
                logger.debug("Error parsing room %s: %s", c_file, e)

    return rooms, pending_exits


def parse_room_file(
    filepath: Path,
    lib_dir: Path,
    vnum_gen: VnumGenerator,
    encoding: str = "euc-kr",
) -> tuple[Room | None, dict[str, str]]:
    """Parse a single room .c file.

    Returns (Room, pending_exit_paths) or (None, {}) if not a room.
    """
    try:
        text = read_lpc_file(filepath, encoding)
    except Exception:
        return None, {}

    inherit = extract_inherit(text)
    if inherit != "LIB_ROOM":
        return None, {}

    # Compute relative path for vnum
    rel_path = _relative_lpc_path(filepath, lib_dir)
    vnum = vnum_gen.path_to_vnum(rel_path)

    # Zone from parent directory
    zone_dir = filepath.parent.relative_to(lib_dir)
    zone_vnum = vnum_gen.zone_id(str(zone_dir))

    # Basic fields
    name = extract_string_call(text, "setShort") or ""
    description = extract_string_call(text, "setLong") or ""

    # Clean color codes
    name = strip_color_codes(name)
    description = strip_color_codes(description)

    # Room attributes
    room_attr = extract_int_call(text, "setRoomAttr") or 0
    room_flags: list[int] = []
    if room_attr:
        room_flags.append(room_attr)

    # Sector type
    sector_type = 1  # indoor by default
    if extract_void_call(text, "setOutSide"):
        sector_type = 0  # outdoor

    # Special flags
    if extract_void_call(text, "setLight"):
        room_flags.append(100)  # LIGHT flag
    if extract_void_call(text, "setHoly"):
        room_flags.append(101)  # HOLY flag

    # Extensions
    extensions: dict = {}
    mp = extract_int_call(text, "setMp")
    if mp is not None:
        extensions["movement_cost"] = mp

    long_type = extract_int_call(text, "setLongType")
    if long_type is not None:
        extensions["long_type"] = long_type

    fast_heal = extract_int_call(text, "setFastHeal")
    if fast_heal:
        extensions["fast_heal"] = fast_heal

    no_sky = extract_int_call(text, "setNoSky")
    if no_sky:
        extensions["no_sky"] = no_sky

    no_under = extract_int_call(text, "setNoUnder")
    if no_under:
        extensions["no_under"] = no_under

    no_hourse = extract_int_call(text, "setNoHourse")
    if no_hourse:
        extensions["no_hourse"] = no_hourse

    no_drop = extract_int_call(text, "setNoDrop")
    if no_drop:
        extensions["no_drop"] = no_drop

    # Props
    props = extract_prop_calls(text)
    if props:
        extensions["props"] = props

    # Room inventory (mob spawns)
    room_inv = extract_mapping(text, "setRoomInventory")
    if room_inv:
        extensions["room_inventory"] = room_inv

    # LimitMob
    limit_mob = extract_mapping(text, "setLimitMob")
    if limit_mob:
        extensions["limit_mob"] = limit_mob

    # Room items (examinable)
    room_items = extract_mapping(text, "setRoomItems")
    if room_items:
        extra_descs = [
            ExtraDescription(keywords=k, description=str(v))
            for k, v in room_items.items()
        ]
    else:
        extra_descs = []

    # Exits: collect paths for 2-pass resolution
    exit_mapping = extract_mapping(text, "setExits") or {}
    enter_mapping = extract_mapping(text, "setEnters") or {}
    # Merge enters into exits
    exit_mapping.update(enter_mapping)

    room = Room(
        vnum=vnum,
        name=name,
        description=description,
        zone_number=zone_vnum,
        room_flags=room_flags,
        sector_type=sector_type,
        exits=[],  # Filled in pass 2
        extra_descriptions=extra_descs,
        extensions=extensions,
    )

    # Return raw exit paths for 2-pass resolution
    pending: dict[str, str] = {}
    for direction, dest in exit_mapping.items():
        if isinstance(dest, str):
            pending[direction] = dest

    return room, pending


def resolve_exits(
    rooms: list[Room],
    pending_exits: dict[int, dict[str, str]],
    vnum_gen: VnumGenerator,
) -> None:
    """Pass 2: convert exit destination paths to VNUMs."""
    room_map = {r.vnum: r for r in rooms}

    for room_vnum, exits in pending_exits.items():
        room = room_map.get(room_vnum)
        if not room:
            continue

        for direction_str, dest_path in exits.items():
            dir_num = DIR_MAP.get(direction_str)
            if dir_num is None:
                # Named entrance (e.g. "회혼실") - use 10+ as custom direction
                dir_num = 10 + hash(direction_str) % 90

            dest_vnum = vnum_gen.path_to_vnum(dest_path)
            room.exits.append(Exit(
                direction=dir_num,
                destination=dest_vnum,
                keyword=direction_str if dir_num >= 10 else "",
            ))


def _find_room_files(room_base: Path) -> list[Path]:
    """Find all .c files that are rooms (not mob/ or obj/ subdirs)."""
    results: list[Path] = []
    for c_file in room_base.rglob("*.c"):
        # Skip mob and obj subdirectories
        parts = c_file.relative_to(room_base).parts
        if any(p in ("mob", "obj") for p in parts):
            continue
        results.append(c_file)
    return results


def _relative_lpc_path(filepath: Path, lib_dir: Path) -> str:
    """Convert absolute path to LPC-style relative path."""
    rel = filepath.relative_to(lib_dir)
    # Convert to / prefix style: 방/관도/hwab0324.c -> /방/관도/hwab0324
    path_str = "/" + str(rel)
    if path_str.endswith(".c"):
        path_str = path_str[:-2]
    return path_str
