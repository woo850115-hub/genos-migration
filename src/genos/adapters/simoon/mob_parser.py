"""Simoon .mob file parser.

Format per mobile (Enhanced 'E' format):
    #<vnum>
    <keywords>~
    <short_desc>~
    <long_desc (multi-line)>
    ~
    <detailed_desc (multi-line)>
    ~
    <action_flags> <affect_flags> <alignment> E
    <level> <hitroll> <ac> <hp_dice> <damage_dice>
    <gold> <exp>
    <load_pos> <default_pos> <sex>
    [BareHandAttack: <type>]
    [Str: <val>]
    [StrAdd: <val>]
    [Dex: <val>]
    [Int: <val>]
    [Wis: <val>]
    [Con: <val>]
    [Cha: <val>]
    [Att1: <val>]
    [Att2: <val>]
    [Att3: <val>]
    E

Differences from tbaMUD:
  - Flags are plain integers (not asciiflag)
  - Custom named attributes (Str:, Dex:, Att1:, etc.) stored in extensions
  - No T (trigger) lines
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from genos.uir.schema import DiceRoll, Monster

logger = logging.getLogger(__name__)

_ENCODING = "euc-kr"

# Named attributes that go into extensions
_NAMED_ATTRS = frozenset({
    "BareHandAttack", "Str", "StrAdd", "Dex", "Int", "Wis", "Con", "Cha",
    "Att1", "Att2", "Att3",
})


def parse_mob_file(filepath: str | Path) -> list[Monster]:
    """Parse a single .mob file and return a list of Monster objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding=_ENCODING, errors="replace")
    return parse_mob_text(text, str(filepath))


def parse_mob_text(text: str, source: str = "<string>") -> list[Monster]:
    """Parse .mob format text into Monster objects."""
    monsters: list[Monster] = []
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
        mob, i = _parse_single_mob(vnum, lines, i, source)
        if mob:
            monsters.append(mob)

    return monsters


def _parse_single_mob(
    vnum: int, lines: list[str], i: int, source: str
) -> tuple[Monster | None, int]:
    """Parse a single mob block starting after #vnum."""
    mob = Monster(vnum=vnum)

    # keywords~
    mob.keywords, i = _read_tilde_string(lines, i)
    # short_desc~
    mob.short_description, i = _read_tilde_string(lines, i)
    # long_desc~
    mob.long_description, i = _read_tilde_string(lines, i)
    # detailed_desc~
    mob.detailed_description, i = _read_tilde_string(lines, i)

    # Flags line: action_flags affect_flags alignment E|S
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 3:
            mob.action_flags = _parse_flags(parts[0])
            mob.affect_flags = _parse_flags(parts[1])
            mob.alignment = int(parts[2])
        mob.mob_type = parts[-1] if parts else "E"

    if mob.mob_type == "E":
        # Line: level hitroll ac hp_dice damage_dice
        if i < len(lines):
            parts = lines[i].rstrip().split()
            i += 1
            if len(parts) >= 5:
                mob.level = int(parts[0])
                mob.hitroll = int(parts[1])
                mob.armor_class = int(parts[2])
                mob.hp_dice = _parse_dice(parts[3])
                mob.damage_dice = _parse_dice(parts[4])

        # Line: gold exp
        if i < len(lines):
            parts = lines[i].rstrip().split()
            i += 1
            if len(parts) >= 2:
                mob.gold = int(parts[0])
                mob.experience = int(parts[1])

        # Line: load_pos default_pos sex
        if i < len(lines):
            parts = lines[i].rstrip().split()
            i += 1
            if len(parts) >= 3:
                mob.load_position = int(parts[0])
                mob.default_position = int(parts[1])
                mob.sex = int(parts[2])

    # Optional trailing lines: BareHandAttack, named attrs, E (end marker)
    while i < len(lines):
        line = lines[i].rstrip()

        if line == "E":
            i += 1
            break

        if line.startswith("#") or line.startswith("$"):
            break

        # Check for named attribute lines like "Str: 18", "BareHandAttack: 1"
        if ":" in line:
            attr_name, _, attr_val = line.partition(":")
            attr_name = attr_name.strip()
            attr_val = attr_val.strip()
            if attr_name in _NAMED_ATTRS:
                try:
                    val = int(attr_val)
                except ValueError:
                    val = attr_val
                if attr_name == "BareHandAttack":
                    mob.bare_hand_attack = int(val)
                else:
                    mob.extensions[attr_name] = val
                i += 1
                continue

        i += 1

    return mob, i


def _parse_dice(dice_str: str) -> DiceRoll:
    """Parse a dice string like '6d6+340' into a DiceRoll."""
    m = re.match(r"(\d+)d(\d+)([+-]\d+)?", dice_str)
    if m:
        return DiceRoll(
            num=int(m.group(1)),
            size=int(m.group(2)),
            bonus=int(m.group(3)) if m.group(3) else 0,
        )
    try:
        return DiceRoll(num=0, size=0, bonus=int(dice_str))
    except ValueError:
        return DiceRoll()


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
