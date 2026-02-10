"""Parse 3eyes binary monster files (objmon/m{nn}).

Each file contains up to 100 fixed-size records of 1184 bytes.
vnum = file_index * 100 + record_index.
Only type==MONSTER (1) records are parsed; type==PLAYER (0) skipped.

Creature struct layout (1184 bytes, 32-bit Linux):
  offset 0:   short fd           (2)
  offset 2:   unsigned char level (1)
  offset 3:   char type          (1)
  offset 4:   char class         (1)
  offset 5:   char race          (1)
  offset 6:   char numwander     (1)
  offset 7:   1 pad
  offset 8:   short alignment    (2)
  offset 10:  char strength      (1)
  offset 11:  char dexterity     (1)
  offset 12:  char constitution  (1)
  offset 13:  char intelligence  (1)
  offset 14:  char piety         (1)
  offset 15:  1 pad
  offset 16:  short hpmax        (2)
  offset 18:  short hpcur        (2)
  offset 20:  short mpmax        (2)
  offset 22:  short mpcur        (2)
  offset 24:  char armor         (1)
  offset 25:  char thaco         (1)
  offset 26:  2 pad
  offset 28:  long experience    (4)
  offset 32:  long gold          (4)
  offset 36:  short ndice        (2)
  offset 38:  short sdice        (2)
  offset 40:  short pdice        (2)
  offset 42:  short special      (2)
  offset 44:  char name[80]      (80)
  offset 124: char description[80] (80)
  offset 204: char talk[80]      (80)
  offset 284: char etc[15]       (15)
  offset 299: char key[3][20]    (60)
  offset 359: 1 pad
  offset 360: long proficiency[5] (20)
  offset 380: long realm[4]      (16)
  offset 396: char spells[16]    (16)
  offset 412: char flags[8]      (8)
  offset 420: char quests[16]    (16)
  offset 436: char questnum      (1)
  offset 437: 1 pad
  offset 438: short carry[10]    (20)
  offset 458: short rom_num      (2)
  offset 460: ptr ready[20]      (80)  -- ignored
  offset 540: daily[10]          (80)  -- ignored
  offset 620: lasttime[45]       (540) -- ignored
  offset 1160: 6 pointers        (24)  -- ignored
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import DiceRoll, Monster

from .binary_utils import (
    flags_to_bit_positions,
    read_byte,
    read_cstring,
    read_cstring_array,
    read_int,
    read_short,
    read_ubyte,
)
from .constants import (
    CREATURE_MONSTER,
    PROFICIENCIES,
    MAGIC_REALMS,
    SIZEOF_CREATURE,
    RECORDS_PER_FILE,
)

logger = logging.getLogger(__name__)


def parse_mob_file(filepath: Path, file_index: int) -> list[Monster]:
    """Parse a single monster file and return a list of Monsters."""
    data = filepath.read_bytes()
    expected = SIZEOF_CREATURE * RECORDS_PER_FILE
    if len(data) < expected:
        logger.warning(
            "Monster file %s is %d bytes, expected %d",
            filepath, len(data), expected,
        )

    monsters: list[Monster] = []
    record_count = min(len(data) // SIZEOF_CREATURE, RECORDS_PER_FILE)

    for i in range(record_count):
        offset = i * SIZEOF_CREATURE
        record = data[offset : offset + SIZEOF_CREATURE]

        # Skip PLAYER type (0) and empty records
        crt_type = read_byte(record, 3)
        if crt_type != CREATURE_MONSTER:
            continue

        # Skip empty records (name all null)
        if record[44:124].rstrip(b"\x00") == b"":
            continue

        vnum = file_index * 100 + i
        monsters.append(_parse_creature_record(record, vnum))

    return monsters


def _parse_creature_record(rec: bytes, vnum: int) -> Monster:
    """Parse a single 1184-byte creature record into a Monster."""
    level = read_ubyte(rec, 2)
    crt_class = read_byte(rec, 4)
    crt_race = read_byte(rec, 5)
    numwander = read_byte(rec, 6)
    alignment = read_short(rec, 8)

    strength = read_byte(rec, 10)
    dexterity = read_byte(rec, 11)
    constitution = read_byte(rec, 12)
    intelligence = read_byte(rec, 13)
    piety = read_byte(rec, 14)

    hpmax = read_short(rec, 16)
    hpcur = read_short(rec, 18)
    mpmax = read_short(rec, 20)
    mpcur = read_short(rec, 22)
    armor = read_byte(rec, 24)
    thaco = read_byte(rec, 25)

    experience = read_int(rec, 28)
    gold = read_int(rec, 32)
    ndice = read_short(rec, 36)
    sdice = read_short(rec, 38)
    pdice = read_short(rec, 40)
    special = read_short(rec, 42)

    name = read_cstring(rec, 44, 80)
    description = read_cstring(rec, 124, 80)
    talk = read_cstring(rec, 204, 80)
    etc = read_cstring(rec, 284, 15)
    keys = read_cstring_array(rec, 299, 3, 20)

    # Proficiencies
    profs: dict[str, int] = {}
    for idx in range(5):
        val = read_int(rec, 360 + idx * 4)
        if val > 0:
            prof_name = PROFICIENCIES.get(idx, f"prof_{idx}")
            profs[prof_name] = val

    # Magic realms
    realms: dict[str, int] = {}
    for idx in range(4):
        val = read_int(rec, 380 + idx * 4)
        if val > 0:
            realm_name = MAGIC_REALMS.get(idx + 1, f"realm_{idx}")
            realms[realm_name] = val

    # Spells
    spells_raw = rec[396:412]
    known_spells = flags_to_bit_positions(spells_raw)

    # Flags
    flags_raw = rec[412:420]
    action_flags = flags_to_bit_positions(flags_raw)

    # Quests
    quests_raw = rec[420:436]
    quest_flags = flags_to_bit_positions(quests_raw)

    questnum = read_byte(rec, 436)

    # Carry items
    carry: list[int] = []
    for idx in range(10):
        c = read_short(rec, 438 + idx * 2)
        if c > 0:
            carry.append(c)

    rom_num = read_short(rec, 458)

    # Build keywords
    keyword_parts = [name] + [k for k in keys if k]
    keywords = " ".join(keyword_parts)

    return Monster(
        vnum=vnum,
        keywords=keywords,
        short_description=name,
        long_description=description,
        detailed_description="",
        action_flags=action_flags,
        affect_flags=[],
        alignment=alignment,
        level=level,
        hitroll=0,
        armor_class=armor,
        hp_dice=DiceRoll(num=hpmax, size=1, bonus=0),
        damage_dice=DiceRoll(num=ndice, size=sdice, bonus=pdice),
        gold=gold,
        experience=experience,
        load_position=8,
        default_position=8,
        sex=1 if 12 in action_flags else 0,
        bare_hand_attack=0,
        mob_type="E",
        extensions={
            "class": crt_class,
            "race": crt_race,
            "thaco": thaco,
            "strength": strength,
            "dexterity": dexterity,
            "constitution": constitution,
            "intelligence": intelligence,
            "piety": piety,
            "hpmax": hpmax,
            "mpmax": mpmax,
            "numwander": numwander,
            "special": special,
            "proficiencies": profs,
            "realms": realms,
            "known_spells": known_spells,
            "quest_flags": quest_flags,
            "questnum": questnum,
            "carry_items": carry,
            "rom_num": rom_num,
            "talk": talk,
            "etc": etc,
        },
    )


def parse_all_monsters(objmon_dir: Path) -> list[Monster]:
    """Parse all monster files in the objmon directory."""
    monsters: list[Monster] = []
    for fpath in sorted(objmon_dir.glob("m[0-9][0-9]")):
        fname = fpath.name
        try:
            file_index = int(fname[1:])
        except ValueError:
            continue
        try:
            monsters.extend(parse_mob_file(fpath, file_index))
        except Exception as e:
            logger.warning("Error parsing %s: %s", fpath, e)
    return monsters
