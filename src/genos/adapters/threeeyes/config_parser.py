"""Parser for game system configuration from 3eyes MUD C source (global.c).

Extracts:
- thaco_list[][20]: THAC0 table (8 playable classes × 20 levels)
- level_exp[]: Experience table (204 levels)
- bonus[]: Attribute bonus table (160 entries)
- class_stats[13]: Class statistics (hp/mp/dice)
- level_cycle[][10]: Stat allocation per level cycle
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from genos.uir.schema import (
    AttributeModifier,
    ExperienceEntry,
    ThacOEntry,
)

logger = logging.getLogger(__name__)

_ENCODING = "euc-kr"

# 3eyes class order: 0=none, 1=assassin..8=thief, 9+=admin
_PLAYER_CLASSES = {
    1: "Assassin", 2: "Barbarian", 3: "Cleric", 4: "Fighter",
    5: "Mage", 6: "Paladin", 7: "Ranger", 8: "Thief",
}


def parse_thac0_table(src_dir: str | Path) -> list[ThacOEntry]:
    """Parse thaco_list[][20] from global.c.

    Returns entries for playable classes (1-8) only.
    """
    src_dir = Path(src_dir)
    global_path = src_dir / "global.c"
    if not global_path.exists():
        return []

    text = global_path.read_text(encoding=_ENCODING, errors="replace")

    match = re.search(r'thaco_list\s*\[\s*\]\s*\[\s*\d+\s*\]\s*=\s*\{', text)
    if not match:
        return []

    body = _extract_balanced(text, match.end(), '{', '}')
    if not body:
        return []

    entries: list[ThacOEntry] = []
    class_idx = 0
    for row_match in re.finditer(r'\{([^}]+)\}', body):
        if class_idx in _PLAYER_CLASSES:
            vals = _parse_int_list(row_match.group(1))
            for level, thac0 in enumerate(vals, start=1):
                entries.append(ThacOEntry(
                    class_id=class_idx, level=level, thac0=thac0,
                ))
        class_idx += 1

    return entries


def parse_exp_table(src_dir: str | Path) -> list[ExperienceEntry]:
    """Parse level_exp[] from global.c. Single shared table (class_id=0)."""
    src_dir = Path(src_dir)
    global_path = src_dir / "global.c"
    if not global_path.exists():
        return []

    text = global_path.read_text(encoding=_ENCODING, errors="replace")

    match = re.search(r'level_exp\s*\[\s*\]\s*=\s*\{', text)
    if not match:
        return []

    body = _extract_balanced(text, match.end(), '{', '}')
    if not body:
        return []

    vals = _parse_long_list(body)
    entries: list[ExperienceEntry] = []
    for level, exp in enumerate(vals, start=1):
        if exp == 0 and level > 1:
            break
        entries.append(ExperienceEntry(
            class_id=0, level=level, exp_required=exp,
        ))

    return entries


def parse_bonus_table(src_dir: str | Path) -> list[AttributeModifier]:
    """Parse bonus[] from global.c → AttributeModifier(stat_name='bonus')."""
    src_dir = Path(src_dir)
    global_path = src_dir / "global.c"
    if not global_path.exists():
        return []

    text = global_path.read_text(encoding=_ENCODING, errors="replace")

    match = re.search(r'bonus\s*\[\s*\]\s*=\s*\{', text)
    if not match:
        return []

    body = _extract_balanced(text, match.end(), '{', '}')
    if not body:
        return []

    vals = _parse_int_list(body)
    entries: list[AttributeModifier] = []
    for score, bonus_val in enumerate(vals):
        entries.append(AttributeModifier(
            stat_name="bonus", score=score,
            modifiers={"bonus": bonus_val},
        ))

    return entries


def parse_class_stats(src_dir: str | Path) -> dict[int, dict[str, int]]:
    """Parse class_stats[13] from global.c.

    Returns {class_id: {hpstart, mpstart, hp, mp, ndice, sdice, pdice}}.
    Only player classes (1-8).
    """
    src_dir = Path(src_dir)
    global_path = src_dir / "global.c"
    if not global_path.exists():
        return {}

    text = global_path.read_text(encoding=_ENCODING, errors="replace")

    match = re.search(r'class_stats\s*\[\s*\d+\s*\]\s*=\s*\{', text)
    if not match:
        return {}

    body = _extract_balanced(text, match.end(), '{', '}')
    if not body:
        return {}

    field_names = ["hpstart", "mpstart", "hp", "mp", "ndice", "sdice", "pdice"]
    result: dict[int, dict[str, int]] = {}
    class_idx = 0

    for row_match in re.finditer(r'\{([^}]+)\}', body):
        if class_idx in _PLAYER_CLASSES:
            vals = _parse_int_list(row_match.group(1))
            stats = {}
            for i, fname in enumerate(field_names):
                if i < len(vals):
                    stats[fname] = vals[i]
            result[class_idx] = stats
        class_idx += 1

    return result


def parse_level_cycle(src_dir: str | Path) -> dict[int, list[int]]:
    """Parse level_cycle[][10] from global.c.

    Returns {class_id: [stat_indices per cycle]} for player classes.
    """
    src_dir = Path(src_dir)
    global_path = src_dir / "global.c"
    if not global_path.exists():
        return {}

    text = global_path.read_text(encoding=_ENCODING, errors="replace")

    # Resolve stat constants
    stat_defs = {}
    for m in re.finditer(r'#define\s+(STR|INT|DEX|CON|PTY)\s+(\d+)', text):
        stat_defs[m.group(1)] = int(m.group(2))

    match = re.search(r'level_cycle\s*\[\s*\]\s*\[\s*\d+\s*\]\s*=\s*\{', text)
    if not match:
        return {}

    body = _extract_balanced(text, match.end(), '{', '}')
    if not body:
        return {}

    result: dict[int, list[int]] = {}
    class_idx = 0

    for row_match in re.finditer(r'\{([^}]+)\}', body):
        if class_idx in _PLAYER_CLASSES:
            vals = []
            for v in row_match.group(1).split(","):
                v = v.strip()
                if v in stat_defs:
                    vals.append(stat_defs[v])
                else:
                    try:
                        vals.append(int(v))
                    except ValueError:
                        vals.append(0)
            result[class_idx] = vals
        class_idx += 1

    return result


# ── Helpers ──────────────────────────────────────────────────────────

def _extract_balanced(text: str, start: int, open_ch: str, close_ch: str) -> str | None:
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
        i += 1
    if depth != 0:
        return None
    return text[start:i - 1]


def _parse_int_list(text: str) -> list[int]:
    """Parse comma-separated integers, ignoring comments."""
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    vals = []
    for v in text.split(","):
        v = v.strip()
        if v:
            try:
                vals.append(int(v))
            except ValueError:
                pass
    return vals


def _parse_long_list(text: str) -> list[int]:
    """Parse comma-separated longs, ignoring comments and whitespace."""
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    vals = []
    for v in text.split(","):
        v = v.strip()
        if v:
            try:
                vals.append(int(v))
            except ValueError:
                pass
    return vals
