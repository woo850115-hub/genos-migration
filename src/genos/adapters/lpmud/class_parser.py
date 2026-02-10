"""Parse 직업.h (JobData) header for character class definitions."""

from __future__ import annotations

import re
from pathlib import Path

from genos.uir.schema import CharacterClass


# Stat name order in 선행능력/주요능력 arrays
STAT_NAMES = ("힘", "민첩", "지혜", "기골", "내공", "투지")


def parse_classes(header_path: Path, encoding: str = "euc-kr") -> list[CharacterClass]:
    """Parse 직업.h file into CharacterClass list."""
    raw = header_path.read_bytes()
    text = raw.decode(encoding, errors="replace")

    # Extract each ([ ... ]) mapping block
    classes: list[CharacterClass] = []
    # Pattern matches mapping entries inside JobData array
    pattern = re.compile(r"\(\[\s*(.*?)\s*\]\)", re.DOTALL)

    for idx, m in enumerate(pattern.finditer(text)):
        block = m.group(1)
        cls = _parse_job_block(block, idx + 1)
        if cls:
            classes.append(cls)

    return classes


def _parse_job_block(block: str, index: int) -> CharacterClass | None:
    """Parse a single JobData mapping entry."""
    fields = _extract_mapping_fields(block)
    if not fields:
        return None

    name = fields.get("직업명", "")
    if not name:
        return None

    base_unit = _int_field(fields, "기본유닛", 6)
    inc_unit = _int_field(fields, "증가유닛", 2)

    # 선행능력 (prerequisite stats) - 6 element array
    prereq_stats = _array_field(fields, "선행능력")
    # 주요능력 (primary stats) - 6 element binary flags
    primary_stats = _array_field(fields, "주요능력")

    # Class advancement paths
    direct_classes = _string_array_field(fields, "직결직업")
    related_classes = _string_array_field(fields, "관계직업")
    prereq_classes = _string_array_field(fields, "선행직업")

    extensions: dict = {}
    if prereq_stats:
        extensions["stat_requirements"] = dict(zip(STAT_NAMES, prereq_stats))
    if primary_stats:
        extensions["primary_stats"] = dict(zip(STAT_NAMES, primary_stats))
    extensions["next_classes"] = direct_classes
    extensions["related_classes"] = related_classes
    extensions["prerequisite_classes"] = prereq_classes

    inc_stop = _int_field(fields, "증가멈춤", 10)
    if inc_stop:
        extensions["inc_stop"] = inc_stop

    return CharacterClass(
        id=index,
        name=name,
        abbreviation=name[:2],
        hp_gain_min=base_unit,
        hp_gain_max=base_unit + inc_unit * inc_stop,
        extensions=extensions,
    )


def _extract_mapping_fields(block: str) -> dict[str, str]:
    """Extract key-value pairs from an LPC mapping block.

    Splits on "key" : value boundaries, respecting nested arrays/parens.
    """
    result: dict[str, str] = {}

    # Find all "key" : value pairs by scanning for quoted keys followed by ':'
    key_pattern = re.compile(r'"([^"]+)"\s*:')
    key_positions: list[tuple[str, int]] = []
    for m in key_pattern.finditer(block):
        key_positions.append((m.group(1), m.end()))

    for i, (key, val_start) in enumerate(key_positions):
        # Value extends until the next key's quote starts (minus comma)
        if i + 1 < len(key_positions):
            # Find the start of next key's quote
            next_key_m = re.search(
                rf'"{re.escape(key_positions[i + 1][0])}"',
                block[val_start:],
            )
            if next_key_m:
                val_end = val_start + next_key_m.start()
                val = block[val_start:val_end].strip().rstrip(",").strip()
            else:
                val = block[val_start:].strip()
        else:
            val = block[val_start:].strip()

        # Strip surrounding quotes from simple string values
        if val.startswith('"') and val.endswith('"') and val.count('"') == 2:
            val = val[1:-1]
        result[key] = val

    return result


def _int_field(fields: dict, key: str, default: int = 0) -> int:
    val = fields.get(key, "")
    m = re.match(r"(-?\d+)", val.strip())
    return int(m.group(1)) if m else default


def _array_field(fields: dict, key: str) -> list[int]:
    """Parse ({ N, N, N }) -> list of ints."""
    val = fields.get(key, "")
    m = re.search(r"\(\{(.*?)\}\)", val, re.DOTALL)
    if not m:
        return []
    items = m.group(1).split(",")
    result: list[int] = []
    for item in items:
        item = item.strip()
        if re.match(r"-?\d+$", item):
            result.append(int(item))
    return result


def _string_array_field(fields: dict, key: str) -> list[str]:
    """Parse ({ "a", "b" }) -> list of strings."""
    val = fields.get(key, "")
    return re.findall(r'"([^"]+)"', val)
