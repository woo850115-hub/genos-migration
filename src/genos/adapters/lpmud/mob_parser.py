"""Parse LPC monster files (inherit LIB_MONSTER) into UIR Monster objects."""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import DiceRoll, Monster

from .lpc_parser import (
    extract_all_string_pair_calls,
    extract_array,
    extract_clone_items,
    extract_float_call,
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

GENDER_MAP = {"남자": 1, "여자": 2, "동물": 0, "장": 0}


def parse_all_monsters(
    lib_dir: Path,
    room_dirs: list[str],
    vnum_gen: VnumGenerator,
    encoding: str = "euc-kr",
) -> list[Monster]:
    """Parse all monster .c files from room mob/ dirs and 물체/ dir."""
    monsters: list[Monster] = []
    seen_paths: set[str] = set()

    # 1. Room mob/ subdirectories
    for room_dir_name in room_dirs:
        room_base = lib_dir / room_dir_name
        if not room_base.is_dir():
            continue
        for mob_dir in room_base.rglob("mob"):
            if not mob_dir.is_dir():
                continue
            for c_file in sorted(mob_dir.glob("*.c")):
                rel = str(c_file.relative_to(lib_dir))
                if rel in seen_paths:
                    continue
                seen_paths.add(rel)
                mob = _parse_mob_file(c_file, lib_dir, vnum_gen, encoding)
                if mob:
                    monsters.append(mob)

    # 2. 물체/ directory (top-level monster files)
    obj_dir = lib_dir / "물체"
    if obj_dir.is_dir():
        for c_file in sorted(obj_dir.rglob("*.c")):
            rel = str(c_file.relative_to(lib_dir))
            if rel in seen_paths:
                continue
            seen_paths.add(rel)
            mob = _parse_mob_file(c_file, lib_dir, vnum_gen, encoding)
            if mob:
                monsters.append(mob)

    return monsters


def _parse_mob_file(
    filepath: Path,
    lib_dir: Path,
    vnum_gen: VnumGenerator,
    encoding: str,
) -> Monster | None:
    """Parse a single monster .c file."""
    try:
        text = read_lpc_file(filepath, encoding)
    except Exception:
        return None

    inherit = extract_inherit(text)
    if inherit != "LIB_MONSTER":
        return None

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

    # Gender
    gender_str = extract_string_call(text, "setGender") or ""
    sex = GENDER_MAP.get(gender_str, 0)

    # Level from randomStat(N)
    level = extract_int_call(text, "randomStat") or 1

    # Stats
    stats = extract_all_string_pair_calls(text, "setStat")
    stat_dict = {s: v for s, v in stats}

    # Experience
    exp = extract_int_call(text, "setExp") or 0
    adj_exp = extract_float_call(text, "setAdjExp")

    # Gold
    gold = extract_int_call(text, "setGold") or 0

    # HP/SP/MP overrides
    max_hp = extract_int_call(text, "setMaxHp")
    max_sp = extract_int_call(text, "setMaxSp")

    # Armor/Weapon class
    armor_class = extract_int_call(text, "setArmorClass") or 0

    # Action flags
    action_flags: list[int] = []
    if extract_void_call(text, "setAggresive"):
        action_flags.append(1)  # AGGRESSIVE
    if extract_void_call(text, "setAggresiveMunpa"):
        action_flags.append(2)  # AGGRESSIVE_MUNPA
    if extract_void_call(text, "setUnconditionalAttack"):
        action_flags.append(3)  # UNCONDITIONAL_ATTACK
    if extract_void_call(text, "setNoAttack"):
        action_flags.append(4)  # NO_ATTACK

    # HP dice approximation from level
    hp_dice = _level_to_hp_dice(level, max_hp)

    # Extensions
    extensions: dict = {}
    if stat_dict:
        extensions["stats"] = stat_dict

    race = extract_string_call(text, "setRace")
    if race:
        extensions["race"] = race

    munpa = extract_string_call(text, "setMunpa")
    if munpa:
        extensions["faction"] = munpa

    wander = extract_int_call(text, "setWander")
    if wander:
        extensions["wander_prob"] = wander

    # Chat
    chat_arr = extract_array(text, "setChat")
    if chat_arr:
        extensions["chat"] = chat_arr
    chat_chance = extract_int_call(text, "setChatChance")
    if chat_chance:
        extensions["chat_chance"] = chat_chance

    # Cloned items (inventory)
    cloned = extract_clone_items(text)
    if cloned:
        extensions["inventory"] = cloned

    # Props
    props = extract_prop_calls(text)
    if props:
        extensions["props"] = props

    if adj_exp:
        extensions["adj_exp"] = adj_exp
    if max_sp:
        extensions["max_sp"] = max_sp

    # Attack messages
    attack_msgs = extract_array(text, "setBasicAttackMessage")
    if attack_msgs:
        extensions["attack_messages"] = attack_msgs

    extensions["source_path"] = rel_path

    return Monster(
        vnum=vnum,
        keywords=keywords,
        short_description=short_desc or name,
        long_description=long_desc,
        level=level,
        sex=sex,
        gold=gold,
        experience=exp,
        armor_class=armor_class,
        hp_dice=hp_dice,
        action_flags=action_flags,
        extensions=extensions,
    )


def _level_to_hp_dice(level: int, max_hp: int | None = None) -> DiceRoll:
    """Approximate HP dice from level or explicit max_hp."""
    if max_hp and max_hp > 0:
        # Approximate: num d size + bonus
        num = max(1, max_hp // 100)
        size = min(100, max(8, max_hp // max(num, 1)))
        bonus = max_hp - (num * size // 2)
        return DiceRoll(num=num, size=size, bonus=max(0, bonus))

    # Level-based approximation
    num = max(1, level // 5)
    size = 8
    bonus = level * 2
    return DiceRoll(num=num, size=size, bonus=bonus)
