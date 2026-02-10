"""Parse LPC item files (LIB_WEAPON/ARMOR/ITEM/FOOD etc.) into UIR Item objects."""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import Item, ItemAffect

from .lpc_parser import (
    extract_array,
    extract_inherit,
    extract_int_call,
    extract_prop_calls,
    extract_string_call,
    extract_void_call,
    read_lpc_file,
    strip_color_codes,
)
from .vnum_generator import VnumGenerator

logger = logging.getLogger(__name__)

# inherit type -> UIR item_type
INHERIT_TO_ITEM_TYPE = {
    "LIB_WEAPON": 5,    # WEAPON
    "LIB_ARMOR": 9,     # ARMOR
    "LIB_FOOD": 19,     # FOOD
    "LIB_DRINK": 17,    # DRINKCON
    "LIB_ITEM": 12,     # OTHER
    "LIB_TORCH": 1,     # LIGHT
    "LIB_AMGI": 5,      # Hidden weapon (암기) -> WEAPON
}

ITEM_INHERITS = set(INHERIT_TO_ITEM_TYPE.keys())

# Wear slot type string -> wear_flag bit
WEAR_TYPE_MAP = {
    "머리": 1, "귀걸이": 2, "목걸이": 3, "신체": 4,
    "허리": 5, "팔보호": 6, "손": 7, "팔찌": 8,
    "반지": 9, "하체": 10, "신발": 11,
    "왼손": 12, "오른손": 13, "맨손": 14, "양손": 15,
}


def parse_all_items(
    lib_dir: Path,
    room_dirs: list[str],
    vnum_gen: VnumGenerator,
    encoding: str = "euc-kr",
) -> list[Item]:
    """Parse all item .c files from 물체/ dir and room obj/ dirs."""
    items: list[Item] = []
    seen_paths: set[str] = set()

    # 1. 물체/ directory
    obj_dir = lib_dir / "물체"
    if obj_dir.is_dir():
        for c_file in sorted(obj_dir.rglob("*.c")):
            rel = str(c_file.relative_to(lib_dir))
            if rel in seen_paths:
                continue
            seen_paths.add(rel)
            item = _parse_item_file(c_file, lib_dir, vnum_gen, encoding)
            if item:
                items.append(item)

    # 2. Room obj/ subdirectories
    for room_dir_name in room_dirs:
        room_base = lib_dir / room_dir_name
        if not room_base.is_dir():
            continue
        for obj_subdir in room_base.rglob("obj"):
            if not obj_subdir.is_dir():
                continue
            for c_file in sorted(obj_subdir.glob("*.c")):
                rel = str(c_file.relative_to(lib_dir))
                if rel in seen_paths:
                    continue
                seen_paths.add(rel)
                item = _parse_item_file(c_file, lib_dir, vnum_gen, encoding)
                if item:
                    items.append(item)

    return items


def _parse_item_file(
    filepath: Path,
    lib_dir: Path,
    vnum_gen: VnumGenerator,
    encoding: str,
) -> Item | None:
    """Parse a single item .c file."""
    try:
        text = read_lpc_file(filepath, encoding)
    except Exception:
        return None

    inherit = extract_inherit(text)
    if inherit not in ITEM_INHERITS:
        return None

    item_type = INHERIT_TO_ITEM_TYPE[inherit]

    rel_path = "/" + str(filepath.relative_to(lib_dir))
    if rel_path.endswith(".c"):
        rel_path = rel_path[:-2]
    vnum = vnum_gen.path_to_vnum(rel_path)

    # Basic fields
    name = extract_string_call(text, "setName") or ""
    keywords_arr = extract_array(text, "setID") or []
    keywords = " ".join(keywords_arr) if keywords_arr else name

    short_desc = extract_string_call(text, "setShort") or ""
    long_desc = extract_string_call(text, "setLong") or ""
    short_desc = strip_color_codes(short_desc)
    long_desc = strip_color_codes(long_desc)

    # Weight / cost
    weight = extract_int_call(text, "setMass") or 0
    cost = extract_int_call(text, "setValue") or 0

    # Min level
    min_level = extract_int_call(text, "setLimitLevel") or 0

    # Wear flags from setType
    wear_flags: list[int] = []
    wear_type = extract_string_call(text, "setType")
    if wear_type and wear_type in WEAR_TYPE_MAP:
        wear_flags.append(WEAR_TYPE_MAP[wear_type])

    # Values array (4 elements)
    values = [0, 0, 0, 0]

    if inherit == "LIB_WEAPON" or inherit == "LIB_AMGI":
        # Weapon values
        weapon_dmg = extract_int_call(text, "setWeapon") or 0
        sp_weapon = extract_int_call(text, "setSpWeapon") or 0
        values[0] = weapon_dmg
        values[1] = sp_weapon
        two_hand = extract_int_call(text, "setTwoHand")
        if two_hand:
            values[2] = 1
    elif inherit == "LIB_ARMOR":
        armor_val = extract_int_call(text, "setArmor") or 0
        sp_armor = extract_int_call(text, "setSpArmor") or 0
        values[0] = armor_val
        values[1] = sp_armor

    # Item affects from setStatUp
    affects: list[ItemAffect] = []
    stat_up_map = {
        "힘": 1, "민첩": 2, "지혜": 3, "기골": 4, "내공": 5, "투지": 6,
    }
    from .lpc_parser import extract_all_string_pair_calls
    stat_ups = extract_all_string_pair_calls(text, "setStatUp")
    for stat_name, modifier in stat_ups:
        loc = stat_up_map.get(stat_name, 0)
        if loc:
            affects.append(ItemAffect(location=loc, modifier=modifier))

    # Extra flags
    extra_flags: list[int] = []
    if extract_void_call(text, "setInvis"):
        extra_flags.append(1)  # INVISIBLE

    # Timer (durability)
    max_life = extract_int_call(text, "setMaxLifeCircle") or 0

    return Item(
        vnum=vnum,
        keywords=keywords,
        short_description=short_desc or name,
        long_description=long_desc,
        item_type=item_type,
        extra_flags=extra_flags,
        wear_flags=wear_flags,
        values=values,
        weight=weight,
        cost=cost,
        min_level=min_level,
        timer=max_life,
        affects=affects,
    )
