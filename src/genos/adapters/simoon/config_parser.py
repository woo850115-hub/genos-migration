"""Parser for game system configuration from Simoon (CircleMUD 3.0 Korean) source.

Reuses CircleMUD config_parser for config.c and constants.c (with euc-kr encoding),
and adds Simoon-specific parsers for titles[] and train_params[].
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from genos.adapters.circlemud.config_parser import (
    parse_attribute_modifiers as _cm_parse_attr_mods,
    parse_game_config as _cm_parse_game_config,
    parse_practice_params as _cm_parse_practice_params,
    _extract_balanced,
    _resolve_const,
)
from genos.uir.schema import (
    AttributeModifier,
    ExperienceEntry,
    GameConfig,
    LevelTitle,
    PracticeParams,
)

logger = logging.getLogger(__name__)

_ENCODING = "euc-kr"


def parse_game_config(src_dir: str | Path) -> list[GameConfig]:
    """Parse game config from Simoon's config.c (EUC-KR)."""
    return _cm_parse_game_config(src_dir, encoding=_ENCODING)


def parse_attribute_modifiers(src_dir: str | Path) -> list[AttributeModifier]:
    """Parse attribute modifier tables from Simoon's constants.c (EUC-KR)."""
    return _cm_parse_attr_mods(src_dir, encoding=_ENCODING)


def parse_practice_params(src_dir: str | Path) -> list[PracticeParams]:
    """Parse prac_params from Simoon's class.c (7 classes)."""
    return _cm_parse_practice_params(src_dir, encoding=_ENCODING, num_classes=7)


def parse_simoon_titles(
    src_dir: str | Path,
) -> tuple[list[LevelTitle], list[ExperienceEntry]]:
    """Parse titles[1][LVL_BULSA+1] from Simoon's class.c.

    The titles array stores {male_title, female_title, exp_required} for each level.
    Returns both LevelTitle entries and ExperienceEntry entries.
    """
    src_dir = Path(src_dir)
    class_path = src_dir / "class.c"
    if not class_path.exists():
        return [], []

    text = class_path.read_text(encoding=_ENCODING, errors="replace")

    match = re.search(r'titles\s*\[\s*\d*\s*\]\s*\[\s*\w+\s*(?:\+\s*\d+)?\s*\]\s*=\s*\{', text)
    if not match:
        return [], []

    body = _extract_balanced(text, match.end(), '{', '}')
    if not body:
        return [], []

    titles: list[LevelTitle] = []
    exp_entries: list[ExperienceEntry] = []

    # Pattern: {"male_title", "female_title", exp_value}
    level = 0
    for m in re.finditer(r'\{\s*"([^"]*?)"\s*,\s*"([^"]*?)"\s*,\s*(\d+)\s*\}', body):
        male_title = m.group(1)
        female_title = m.group(2)
        exp = int(m.group(3))

        titles.append(LevelTitle(
            class_id=0, level=level, gender="male", title=male_title,
        ))
        titles.append(LevelTitle(
            class_id=0, level=level, gender="female", title=female_title,
        ))
        exp_entries.append(ExperienceEntry(
            class_id=0, level=level, exp_required=exp,
        ))
        level += 1

    return titles, exp_entries


def parse_train_params(
    src_dir: str | Path,
) -> list[PracticeParams]:
    """Parse train_params[6][NUM_CLASSES] from Simoon's class.c.

    Stores stat caps per class. Extends PracticeParams with stat_caps in extensions.
    """
    src_dir = Path(src_dir)
    class_path = src_dir / "class.c"
    if not class_path.exists():
        return []

    text = class_path.read_text(encoding=_ENCODING, errors="replace")

    match = re.search(r'int\s+train_params\s*\[\s*\d*\s*\]\s*\[\s*\w+\s*\]\s*=\s*\{', text)
    if not match:
        return []

    body = _extract_balanced(text, match.end(), '{', '}')
    if not body:
        return []

    rows: list[list[int]] = []
    for row_match in re.finditer(r'\{([^}]+)\}', body):
        vals = []
        for v in row_match.group(1).split(","):
            v = v.strip()
            if v:
                try:
                    vals.append(int(v))
                except ValueError:
                    vals.append(0)
        if vals:
            rows.append(vals)

    if len(rows) < 6:
        return []

    stat_names = ["strength", "constitution", "wisdom", "intelligence", "dexterity", "charisma"]
    num_classes = len(rows[0])

    entries: list[PracticeParams] = []
    for class_id in range(num_classes):
        stat_caps = {}
        for i, sname in enumerate(stat_names):
            if i < len(rows) and class_id < len(rows[i]):
                stat_caps[sname] = rows[i][class_id]
        entries.append(PracticeParams(
            class_id=class_id,
            extensions={"train_stat_caps": stat_caps},
        ))

    return entries
