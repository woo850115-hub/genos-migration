"""CircleMUD .mob file parser (Enhanced format).

Format per mobile (Enhanced 'E' format):
    #<vnum>
    <keywords>~
    <short_desc>~
    <long_desc (may be multi-line, ends with newline)>
    ~
    <detailed_desc (multi-line)>
    ~
    <action_flags> <affect_flags> <alignment> <unused...> E
    <level> <hitroll> <ac> <hp_dice> <damage_dice>
    <gold> <exp>
    <load_pos> <default_pos> <sex>
    [BareHandAttack: <type>]
    [E]
    [T <trigger_vnum>]...
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from genos.uir.schema import DiceRoll, Monster

from .constants import asciiflag_to_int, int_to_flag_list

logger = logging.getLogger(__name__)


def parse_mob_file(filepath: str | Path) -> list[Monster]:
    """Parse a single .mob file and return a list of Monster objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding="utf-8", errors="replace")
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
    # long_desc~ (the "in room" description)
    mob.long_description, i = _read_tilde_string(lines, i)
    # detailed_desc~
    mob.detailed_description, i = _read_tilde_string(lines, i)

    # Flags line: action_flags affect_flags alignment [extra...] E|S
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 3:
            action_int = asciiflag_to_int(parts[0])
            mob.action_flags = int_to_flag_list(action_int)
            affect_int = asciiflag_to_int(parts[1])
            mob.affect_flags = int_to_flag_list(affect_int)
            mob.alignment = int(parts[2])

        # Detect format: last field is 'E' (enhanced) or 'S' (simple)
        mob.mob_type = parts[-1] if parts else "E"

    if mob.mob_type == "E":
        # Enhanced format
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

    # Optional trailing lines: BareHandAttack, E (end marker), T (triggers)
    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("BareHandAttack:"):
            try:
                mob.bare_hand_attack = int(line.split(":")[1].strip())
            except (IndexError, ValueError):
                pass
            i += 1

        elif line == "E":
            # End-of-mob marker in enhanced format
            i += 1
            break

        elif line.startswith("T "):
            try:
                trg_vnum = int(line.split()[1])
                mob.trigger_vnums.append(trg_vnum)
            except (IndexError, ValueError):
                pass
            i += 1

        elif line.startswith("#") or line.startswith("$"):
            break

        else:
            i += 1

    # Collect any remaining T lines after the E marker
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("T "):
            try:
                trg_vnum = int(line.split()[1])
                mob.trigger_vnums.append(trg_vnum)
            except (IndexError, ValueError):
                pass
            i += 1
        elif line.startswith("#") or line.startswith("$") or line == "":
            break
        else:
            break

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
    # Fallback: try as "0d0+N"
    try:
        return DiceRoll(num=0, size=0, bonus=int(dice_str))
    except ValueError:
        return DiceRoll()


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
