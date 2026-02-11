"""Parser for spell/skill definitions from CircleMUD/tbaMUD C source files.

Extracts data from three source files:
1. spells.h: SPELL_* and SKILL_* defines → ID mapping
2. spell_parser.c: spello() calls → spell metadata
3. class.c: spell_level() calls → per-class level requirements

tbaMUD spello() signature (10 args):
    spello(SPELL_ID, "name", max_mana, min_mana, mana_change,
           POS_*, targets, violent, routines, "wearoff_msg" | NULL);

Simoon spello() signature (8 args, no name/wearoff):
    spello(SPELL_ID, max_mana, min_mana, mana_change,
           POS_*, targets, violent, routines);
    (Korean names come from han_spells[] array)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from genos.uir.schema import Skill

logger = logging.getLogger(__name__)

# Position constants
_POS_MAP = {
    "POS_DEAD": 0, "POS_MORTALLYW": 1, "POS_INCAP": 2,
    "POS_STUNNED": 3, "POS_SLEEPING": 4, "POS_RESTING": 5,
    "POS_SITTING": 6, "POS_FIGHTING": 7, "POS_STANDING": 8,
}

# Class constants
_CLASS_MAP = {
    "CLASS_MAGIC_USER": 0, "CLASS_CLERIC": 1,
    "CLASS_THIEF": 2, "CLASS_WARRIOR": 3,
    # Simoon extended classes
    "CLASS_DARKMAGE": 4, "CLASS_BERSERKER": 5, "CLASS_SUMMONER": 6,
}


def parse_skills(
    src_dir: str | Path,
    encoding: str = "utf-8",
    has_spell_name: bool = True,
) -> list[Skill]:
    """Parse all spell/skill data from C source files.

    Args:
        src_dir: Path to the src/ directory containing .c and .h files.
        encoding: File encoding (utf-8 for tbaMUD, euc-kr for Simoon).
        has_spell_name: True for tbaMUD (name in spello), False for Simoon.

    Returns:
        List of Skill objects with metadata and class levels.
    """
    src_dir = Path(src_dir)

    # Step 1: Parse spell/skill ID defines from spells.h
    id_map = _parse_spell_defines(src_dir / "spells.h", encoding)

    # Step 2: Parse han_spells[] if present (Simoon)
    korean_names: dict[int, str] = {}
    if not has_spell_name:
        spell_parser_path = src_dir / "spell_parser.c"
        if spell_parser_path.exists():
            text = spell_parser_path.read_text(encoding=encoding, errors="replace")
            korean_names = _parse_han_spells(text)

    # Step 3: Parse spello() calls from spell_parser.c
    skills = _parse_spello_calls(
        src_dir / "spell_parser.c", encoding, id_map,
        has_spell_name=has_spell_name,
    )

    # Step 4: Apply Korean names if available
    for skill in skills:
        if skill.id in korean_names:
            skill.extensions["korean_name"] = korean_names[skill.id]

    # Step 5: Parse spell_level() calls from class.c
    class_levels = _parse_spell_levels(src_dir / "class.c", encoding, id_map)
    for skill in skills:
        if skill.id in class_levels:
            skill.class_levels = class_levels[skill.id]

    return skills


def _parse_spell_defines(filepath: Path, encoding: str) -> dict[str, int]:
    """Parse #define SPELL_* and SKILL_* from spells.h."""
    if not filepath.exists():
        return {}

    text = filepath.read_text(encoding=encoding, errors="replace")
    id_map: dict[str, int] = {}

    for m in re.finditer(
        r'#define\s+((?:SPELL|SKILL)_\w+)\s+(\d+)', text
    ):
        name = m.group(1)
        value = int(m.group(2))
        id_map[name] = value

    return id_map


def _parse_spello_calls(
    filepath: Path,
    encoding: str,
    id_map: dict[str, int],
    has_spell_name: bool = True,
) -> list[Skill]:
    """Parse spello() calls from spell_parser.c."""
    if not filepath.exists():
        return []

    text = filepath.read_text(encoding=encoding, errors="replace")
    skills: list[Skill] = []

    # Match spello(...) calls spanning multiple lines
    # We find each spello( and then extract balanced parentheses
    seen_ids: dict[int, int] = {}  # id -> index in skills list
    for m in re.finditer(r'spello\s*\(', text):
        start = m.end()
        args_text = _extract_balanced_parens(text, start)
        if args_text is None:
            continue

        # Remove comments
        args_text = re.sub(r'/\*.*?\*/', '', args_text, flags=re.DOTALL)

        skill = _parse_spello_args(args_text, id_map, has_spell_name)
        if skill:
            if skill.id in seen_ids:
                # Duplicate spello() call — keep first (with real values)
                logger.debug("Duplicate spello id=%d, keeping first", skill.id)
                continue
            seen_ids[skill.id] = len(skills)
            skills.append(skill)

    return skills


def _parse_spello_args(
    args_text: str,
    id_map: dict[str, int],
    has_spell_name: bool,
) -> Skill | None:
    """Parse the arguments of a single spello() call."""
    # Split by comma, being careful with nested expressions like TAR_A | TAR_B
    args = _split_args(args_text)

    try:
        if has_spell_name:
            # tbaMUD: SPELL_ID, "name", max, min, change, pos, targets, violent, routines, "wearoff"|NULL
            if len(args) < 10:
                return None
            spell_id = _resolve_id(args[0].strip(), id_map)
            name = args[1].strip().strip('"')
            max_mana = _resolve_int(args[2])
            min_mana = _resolve_int(args[3])
            mana_change = _resolve_int(args[4])
            min_pos = _resolve_pos(args[5])
            targets = _resolve_bitor(args[6])
            violent = args[7].strip() in ("TRUE", "1")
            routines = _resolve_bitor(args[8])
            wearoff_raw = args[9].strip()
            wearoff = "" if wearoff_raw == "NULL" else wearoff_raw.strip('"')
        else:
            # Simoon: SPELL_ID, max, min, change, pos, targets, violent, routines
            if len(args) < 8:
                return None
            spell_id = _resolve_id(args[0].strip(), id_map)
            name = args[0].strip()  # Use constant name as fallback
            max_mana = _resolve_int(args[1])
            min_mana = _resolve_int(args[2])
            mana_change = _resolve_int(args[3])
            min_pos = _resolve_pos(args[4])
            targets = _resolve_bitor(args[5])
            violent = args[6].strip() in ("TRUE", "1")
            routines = _resolve_bitor(args[7])
            wearoff = ""

        if spell_id is None:
            return None

        # Determine spell_type from ID
        spell_type = "skill" if spell_id >= 131 else "spell"

        # Clean up name for Simoon (SPELL_ARMOR -> armor)
        if not has_spell_name:
            name = _constant_to_name(args[0].strip())

        return Skill(
            id=spell_id,
            name=name,
            spell_type=spell_type,
            max_mana=max_mana,
            min_mana=min_mana,
            mana_change=mana_change,
            min_position=min_pos,
            targets=targets,
            violent=violent,
            routines=routines,
            wearoff_msg=wearoff,
        )
    except (ValueError, IndexError) as e:
        logger.debug("Skipping unparseable spello call: %s", e)
        return None


def _parse_spell_levels(
    filepath: Path,
    encoding: str,
    id_map: dict[str, int],
) -> dict[int, dict[int, int]]:
    """Parse spell_level() calls from class.c.

    Returns: {spell_id: {class_id: level}}
    """
    if not filepath.exists():
        return {}

    text = filepath.read_text(encoding=encoding, errors="replace")
    result: dict[int, dict[int, int]] = {}

    pattern = re.compile(
        r'spell_level\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\d+)\s*\)'
    )
    for m in pattern.finditer(text):
        spell_name = m.group(1)
        class_name = m.group(2)
        level = int(m.group(3))

        spell_id = id_map.get(spell_name)
        class_id = _CLASS_MAP.get(class_name)

        if spell_id is not None and class_id is not None:
            if spell_id not in result:
                result[spell_id] = {}
            result[spell_id][class_id] = level

    return result


def _parse_han_spells(text: str) -> dict[int, str]:
    """Parse han_spells[] Korean name array from Simoon spell_parser.c."""
    # Find han_spells[] array
    match = re.search(r'han_spells\s*\[\s*\]\s*=\s*\{', text)
    if not match:
        return {}

    start = match.end()
    body = _extract_balanced_braces(text, start)
    if not body:
        return {}

    names: dict[int, str] = {}
    # Each entry is a quoted string: "name"
    idx = 0
    for m in re.finditer(r'"([^"]*)"', body):
        names[idx] = m.group(1)
        idx += 1

    return names


# ── Helpers ──────────────────────────────────────────────────────────────

def _extract_balanced_parens(text: str, start: int) -> str | None:
    """Extract content between balanced parentheses starting after '('."""
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
        i += 1
    if depth != 0:
        return None
    return text[start:i - 1]


def _extract_balanced_braces(text: str, start: int) -> str | None:
    """Extract content between balanced braces starting after '{'."""
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
        i += 1
    if depth != 0:
        return None
    return text[start:i - 1]


def _split_args(text: str) -> list[str]:
    """Split comma-separated args, respecting nested parens and strings."""
    args: list[str] = []
    depth = 0
    current: list[str] = []
    in_string = False

    for ch in text:
        if ch == '"' and (not current or current[-1] != '\\'):
            in_string = not in_string
            current.append(ch)
        elif in_string:
            current.append(ch)
        elif ch == '(':
            depth += 1
            current.append(ch)
        elif ch == ')':
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            args.append(''.join(current))
            current = []
        else:
            current.append(ch)

    if current:
        args.append(''.join(current))
    return args


def _resolve_id(value: str, id_map: dict[str, int]) -> int | None:
    """Resolve a SPELL_* or SKILL_* constant to its numeric ID."""
    value = value.strip()
    if value in id_map:
        return id_map[value]
    try:
        return int(value)
    except ValueError:
        return None


def _resolve_int(value: str) -> int:
    """Resolve a string to integer."""
    value = value.strip()
    try:
        return int(value)
    except ValueError:
        return 0


def _resolve_pos(value: str) -> int:
    """Resolve a POS_* constant."""
    value = value.strip()
    return _POS_MAP.get(value, 0)


def _resolve_bitor(value: str) -> int:
    """Resolve a bitwise OR expression like 'TAR_CHAR_ROOM | TAR_OBJ_INV'."""
    # Known target constants
    known = {
        "TAR_IGNORE": 1, "TAR_CHAR_ROOM": 2, "TAR_CHAR_WORLD": 4,
        "TAR_FIGHT_SELF": 8, "TAR_FIGHT_VICT": 16, "TAR_SELF_ONLY": 32,
        "TAR_NOT_SELF": 64, "TAR_OBJ_INV": 128, "TAR_OBJ_ROOM": 256,
        "TAR_OBJ_WORLD": 512, "TAR_OBJ_EQUIP": 1024,
        "MAG_DAMAGE": 1, "MAG_AFFECTS": 2, "MAG_UNAFFECTS": 4,
        "MAG_POINTS": 8, "MAG_ALTER_OBJS": 16, "MAG_GROUPS": 32,
        "MAG_MASSES": 64, "MAG_AREAS": 128, "MAG_SUMMONS": 256,
        "MAG_CREATIONS": 512, "MAG_MANUAL": 1024, "MAG_ROOMS": 2048,
        "FALSE": 0, "TRUE": 1,
    }
    parts = [p.strip() for p in value.split("|")]
    result = 0
    for p in parts:
        if p in known:
            result |= known[p]
        else:
            try:
                result |= int(p)
            except ValueError:
                pass
    return result


def _constant_to_name(const: str) -> str:
    """Convert SPELL_MAGIC_MISSILE to 'magic missile'."""
    # Remove SPELL_ or SKILL_ prefix
    for prefix in ("SPELL_", "SKILL_"):
        if const.startswith(prefix):
            const = const[len(prefix):]
            break
    return const.lower().replace("_", " ")
