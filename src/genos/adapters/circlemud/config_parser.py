"""Parser for game system configuration from CircleMUD/tbaMUD C source files.

Extracts data from three source files:
1. config.c: Game configuration variables (int/bool/room_vnum)
2. class.c: Experience tables, THAC0, saving throws, level titles, practice params
3. constants.c: Attribute modifier tables (str_app, dex_app, etc.)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from genos.uir.schema import (
    AttributeModifier,
    ExperienceEntry,
    GameConfig,
    LevelTitle,
    PracticeParams,
    SavingThrowEntry,
    ThacOEntry,
)

logger = logging.getLogger(__name__)

# Constant resolution
_CONSTANTS: dict[str, int] = {
    "LVL_IMMORT": 31, "LVL_GOD": 32, "LVL_GRGOD": 33, "LVL_IMPL": 34,
    "YES": 1, "NO": 0, "TRUE": 1, "FALSE": 0,
    "CLASS_MAGIC_USER": 0, "CLASS_CLERIC": 1, "CLASS_THIEF": 2, "CLASS_WARRIOR": 3,
    "CLASS_UNDEFINED": -1,
    "SAVING_PARA": 0, "SAVING_ROD": 1, "SAVING_PETRI": 2,
    "SAVING_BREATH": 3, "SAVING_SPELL": 4,
    "NOWHERE": -1,
    "MAP_OFF": 0, "MAP_ON": 1, "MAP_IMM_ONLY": 2,
    "SPELL": 0, "SKILL": 1,
}

# Category mapping for config variables
_CONFIG_CATEGORIES: dict[str, str] = {
    "pk_setting": "pk", "pt_setting": "pk", "script_players": "game",
    "level_can_shout": "game", "holler_move_cost": "game",
    "tunnel_size": "game",
    "max_exp_gain": "economy", "max_exp_loss": "economy",
    "max_npc_corpse_time": "corpse", "max_pc_corpse_time": "corpse",
    "idle_void": "idle", "idle_rent_time": "idle", "idle_max_level": "idle",
    "dts_are_dumps": "game", "load_into_inventory": "game",
    "track_through_doors": "game", "no_mort_to_immort": "game",
    "diagonal_dirs": "game",
    "free_rent": "rent", "max_obj_save": "rent", "min_rent_cost": "rent",
    "auto_save": "rent", "autosave_time": "rent",
    "crash_file_timeout": "rent", "rent_file_timeout": "rent",
    "auto_pwipe": "game", "selfdelete_fastwipe": "game",
    "mortal_start_room": "room", "immort_start_room": "room",
    "frozen_start_room": "room",
    "donation_room_1": "room", "donation_room_2": "room",
    "donation_room_3": "room",
    "bitwarning": "game", "bitsavetodisk": "game",
    "DFLT_PORT": "port", "max_playing": "port",
    "max_filesize": "game", "max_bad_pws": "game",
    "siteok_everyone": "game", "nameserver_is_slow": "game",
    "auto_save_olc": "game", "use_new_socials": "game",
    "use_autowiz": "game", "min_wizlist_lev": "game",
    "display_closed_doors": "game",
    "map_option": "game", "default_map_size": "game",
    "default_minimap_size": "game",
    "medit_advanced_stats": "game", "ibt_autosave": "game",
}


def _resolve_const(value: str) -> int:
    """Resolve a C constant or integer literal to an int."""
    value = value.strip()
    if value in _CONSTANTS:
        return _CONSTANTS[value]
    # Handle expressions like "LVL_IMMORT - 1"
    m = re.match(r'(\w+)\s*-\s*(\d+)', value)
    if m:
        base = _CONSTANTS.get(m.group(1))
        if base is not None:
            return base - int(m.group(2))
    try:
        return int(value)
    except ValueError:
        return 0


# ── config.c parsing ──────────────────────────────────────────────────

def parse_game_config(
    src_dir: str | Path,
    encoding: str = "utf-8",
) -> list[GameConfig]:
    """Parse game configuration variables from config.c."""
    src_dir = Path(src_dir)
    config_path = src_dir / "config.c"
    if not config_path.exists():
        return []

    text = config_path.read_text(encoding=encoding, errors="replace")
    configs: list[GameConfig] = []

    # Match: type varname = value;
    # Types: int, room_vnum, ush_int
    pattern = re.compile(
        r'^(?:int|room_vnum|ush_int)\s+(\w+)\s*=\s*([^;]+);',
        re.MULTILINE,
    )
    for m in pattern.finditer(text):
        varname = m.group(1)
        raw_value = m.group(2).strip()

        # Determine type
        line_start = text.rfind('\n', 0, m.start()) + 1
        type_decl = text[line_start:m.start() + len(m.group(0))]

        if "room_vnum" in type_decl:
            value_type = "room_vnum"
        elif raw_value in ("YES", "NO", "TRUE", "FALSE"):
            value_type = "bool"
        else:
            value_type = "int"

        resolved = _resolve_const(raw_value)
        category = _CONFIG_CATEGORIES.get(varname, "game")

        configs.append(GameConfig(
            key=varname,
            value=str(resolved),
            value_type=value_type,
            category=category,
        ))

    return configs


# ── class.c parsing ───────────────────────────────────────────────────

def parse_exp_table(
    src_dir: str | Path,
    encoding: str = "utf-8",
) -> list[ExperienceEntry]:
    """Parse level_exp() function from class.c.

    tbaMUD has 4 classes × 31 levels in switch/case format.
    """
    src_dir = Path(src_dir)
    class_path = src_dir / "class.c"
    if not class_path.exists():
        return []

    text = class_path.read_text(encoding=encoding, errors="replace")

    # Find level_exp function
    match = re.search(r'int\s+level_exp\s*\([^)]*\)\s*\{', text)
    if not match:
        return []

    func_body = _extract_function_body(text, match.end())
    if not func_body:
        return []

    entries: list[ExperienceEntry] = []
    class_map = {
        "CLASS_MAGIC_USER": 0, "CLASS_CLERIC": 1,
        "CLASS_THIEF": 2, "CLASS_WARRIOR": 3,
    }

    current_class = -1
    for line in func_body.split("\n"):
        line = line.strip()

        # Match class case
        for cname, cid in class_map.items():
            if f"case {cname}:" in line or f"case {cname} :" in line:
                current_class = cid
                break

        if current_class < 0:
            continue

        # Match level case: "case  N: return VALUE;"
        m = re.match(r'case\s+(\w+)\s*:\s*return\s+([^;]+);', line)
        if m:
            level_str = m.group(1)
            exp_str = m.group(2).strip()
            level = _resolve_const(level_str)
            exp = _resolve_const(exp_str)
            entries.append(ExperienceEntry(
                class_id=current_class, level=level, exp_required=exp,
            ))

    return entries


def parse_thac0_table(
    src_dir: str | Path,
    encoding: str = "utf-8",
) -> list[ThacOEntry]:
    """Parse thaco() function from class.c."""
    src_dir = Path(src_dir)
    class_path = src_dir / "class.c"
    if not class_path.exists():
        return []

    text = class_path.read_text(encoding=encoding, errors="replace")

    match = re.search(r'int\s+thaco\s*\([^)]*\)\s*\{', text)
    if not match:
        return []

    func_body = _extract_function_body(text, match.end())
    if not func_body:
        return []

    entries: list[ThacOEntry] = []
    class_map = {
        "CLASS_MAGIC_USER": 0, "CLASS_CLERIC": 1,
        "CLASS_THIEF": 2, "CLASS_WARRIOR": 3,
    }

    current_class = -1
    for line in func_body.split("\n"):
        line = line.strip()

        for cname, cid in class_map.items():
            if f"case {cname}:" in line or f"case {cname} :" in line:
                current_class = cid
                break

        if current_class < 0:
            continue

        m = re.match(r'case\s+(\d+)\s*:\s*return\s+([^;]+);', line)
        if m:
            level = int(m.group(1))
            thac0 = _resolve_const(m.group(2))
            entries.append(ThacOEntry(
                class_id=current_class, level=level, thac0=thac0,
            ))

    return entries


def parse_saving_throws(
    src_dir: str | Path,
    encoding: str = "utf-8",
) -> list[SavingThrowEntry]:
    """Parse saving_throws() function from class.c.

    Triple-nested switch: class → save_type → level.
    """
    src_dir = Path(src_dir)
    class_path = src_dir / "class.c"
    if not class_path.exists():
        return []

    text = class_path.read_text(encoding=encoding, errors="replace")

    match = re.search(r'(?:byte|int)\s+saving_throws\s*\([^)]*\)\s*\{', text)
    if not match:
        return []

    func_body = _extract_function_body(text, match.end())
    if not func_body:
        return []

    entries: list[SavingThrowEntry] = []
    class_map = {
        "CLASS_MAGIC_USER": 0, "CLASS_CLERIC": 1,
        "CLASS_THIEF": 2, "CLASS_WARRIOR": 3,
    }
    save_map = {
        "SAVING_PARA": 0, "SAVING_ROD": 1, "SAVING_PETRI": 2,
        "SAVING_BREATH": 3, "SAVING_SPELL": 4,
    }

    current_class = -1
    current_save = -1

    for line in func_body.split("\n"):
        line = line.strip()

        for cname, cid in class_map.items():
            if f"case {cname}:" in line or f"case {cname} :" in line:
                current_class = cid
                break

        for sname, sid in save_map.items():
            if f"case {sname}:" in line or f"case {sname} :" in line:
                current_save = sid
                break

        if current_class < 0 or current_save < 0:
            continue

        m = re.match(r'case\s+(\d+)\s*:\s*return\s+([^;]+);', line)
        if m:
            level = int(m.group(1))
            save_val = _resolve_const(m.group(2))
            entries.append(SavingThrowEntry(
                class_id=current_class,
                save_type=current_save,
                level=level,
                save_value=save_val,
            ))

    return entries


def parse_level_titles(
    src_dir: str | Path,
    encoding: str = "utf-8",
) -> list[LevelTitle]:
    """Parse title_male() and title_female() from class.c."""
    src_dir = Path(src_dir)
    class_path = src_dir / "class.c"
    if not class_path.exists():
        return []

    text = class_path.read_text(encoding=encoding, errors="replace")
    entries: list[LevelTitle] = []

    for gender, func_name in [("male", "title_male"), ("female", "title_female")]:
        match = re.search(
            rf'const\s+char\s*\*\s*{func_name}\s*\([^)]*\)\s*\{{', text,
        )
        if not match:
            continue

        func_body = _extract_function_body(text, match.end())
        if not func_body:
            continue

        class_map = {
            "CLASS_MAGIC_USER": 0, "CLASS_CLERIC": 1,
            "CLASS_THIEF": 2, "CLASS_WARRIOR": 3,
        }
        current_class = -1

        for line in func_body.split("\n"):
            line = line.strip()

            for cname, cid in class_map.items():
                if f"case {cname}:" in line or f"case {cname} :" in line:
                    current_class = cid
                    break

            if current_class < 0:
                continue

            m = re.match(r'case\s+(\w+)\s*:\s*return\s+"([^"]+)";', line)
            if m:
                level = _resolve_const(m.group(1))
                title = m.group(2)
                entries.append(LevelTitle(
                    class_id=current_class,
                    level=level,
                    gender=gender,
                    title=title,
                ))

    return entries


def parse_practice_params(
    src_dir: str | Path,
    encoding: str = "utf-8",
    num_classes: int = 4,
) -> list[PracticeParams]:
    """Parse prac_params[4][NUM_CLASSES] from class.c."""
    src_dir = Path(src_dir)
    class_path = src_dir / "class.c"
    if not class_path.exists():
        return []

    text = class_path.read_text(encoding=encoding, errors="replace")

    match = re.search(r'int\s+prac_params\s*\[\s*\d*\s*\]\s*\[\s*\w+\s*\]\s*=\s*\{', text)
    if not match:
        return []

    body = _extract_balanced(text, match.end(), '{', '}')
    if not body:
        return []

    # Parse rows: each { val, val, ... }
    rows: list[list[int]] = []
    for row_match in re.finditer(r'\{([^}]+)\}', body):
        vals = []
        for v in row_match.group(1).split(","):
            v = v.strip()
            if v:
                vals.append(_resolve_const(v))
        if vals:
            rows.append(vals)

    if len(rows) < 4:
        return []

    entries: list[PracticeParams] = []
    for class_id in range(min(num_classes, len(rows[0]))):
        prac_type = "spell" if rows[3][class_id] == 0 else "skill"
        entries.append(PracticeParams(
            class_id=class_id,
            learned_level=rows[0][class_id],
            max_per_practice=rows[1][class_id],
            min_per_practice=rows[2][class_id],
            prac_type=prac_type,
        ))

    return entries


# ── constants.c parsing ──────────────────────────────────────────────

def parse_attribute_modifiers(
    src_dir: str | Path,
    encoding: str = "utf-8",
) -> list[AttributeModifier]:
    """Parse attribute modifier tables from constants.c.

    Tables: str_app, dex_app_skill, dex_app, con_app, int_app, wis_app
    """
    src_dir = Path(src_dir)
    const_path = src_dir / "constants.c"
    if not const_path.exists():
        return []

    text = const_path.read_text(encoding=encoding, errors="replace")
    entries: list[AttributeModifier] = []

    table_specs: list[tuple[str, str, list[str]]] = [
        (r'str_app\s*\[\s*\]', "strength",
         ["tohit", "todam", "carry_weight", "wield_weight"]),
        (r'dex_app_skill\s*\[\s*\]', "dex_skill",
         ["p_pocket", "p_locks", "traps", "sneak", "hide"]),
        (r'dex_app\s*\[\s*\]', "dexterity",
         ["reaction", "miss_att", "defensive"]),
        (r'con_app\s*\[\s*\]', "constitution", ["hitp"]),
        (r'int_app\s*\[\s*\]', "intelligence", ["learn"]),
        (r'wis_app\s*\[\s*\]', "wisdom", ["bonus"]),
    ]

    for pattern, stat_name, field_names in table_specs:
        match = re.search(pattern + r'\s*=\s*\{', text)
        if not match:
            continue

        body = _extract_balanced(text, match.end(), '{', '}')
        if not body:
            continue

        score = 0
        for row_match in re.finditer(r'\{([^}]+)\}', body):
            vals = []
            for v in row_match.group(1).split(","):
                v = v.strip()
                if v:
                    try:
                        vals.append(int(v))
                    except ValueError:
                        vals.append(0)

            mods = {}
            for i, fname in enumerate(field_names):
                if i < len(vals):
                    mods[fname] = vals[i]

            entries.append(AttributeModifier(
                stat_name=stat_name, score=score, modifiers=mods,
            ))
            score += 1

    return entries


# ── Helpers ──────────────────────────────────────────────────────────

def _extract_function_body(text: str, start: int) -> str | None:
    """Extract a C function body from the opening { to closing }."""
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


def _extract_balanced(text: str, start: int, open_ch: str, close_ch: str) -> str | None:
    """Extract content between balanced delimiters."""
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
