"""Parse game configuration from LP-MUD header files and config files.

Extracts:
- GameConfig from 세팅.h, woong.cfg/config.HanLP
- Combat constants from 전투.h
- Stat formulas from 구조/monster.c
"""

from __future__ import annotations

import re
from pathlib import Path

from genos.uir.schema import GameConfig


def parse_settings_header(
    header_path: Path,
    encoding: str = "euc-kr",
) -> list[GameConfig]:
    """Parse 세팅.h for game configuration defines."""
    raw = header_path.read_bytes()
    text = raw.decode(encoding, errors="replace")

    configs: list[GameConfig] = []

    # Extract #define KEY VALUE patterns
    for m in re.finditer(
        r'#define\s+(\w+)\s+(?:DIR_DOMAIN\s+)?(?:"/([^"]+)"|([\w/]+)\s+"([^"]+)"|(\d+))',
        text,
    ):
        key = m.group(1)
        # Try different value captures
        if m.group(2):
            value = m.group(2)
            vtype = "room_vnum"
        elif m.group(4):
            value = m.group(4)
            vtype = "str"
        elif m.group(5):
            value = m.group(5)
            vtype = "int"
        else:
            continue

        configs.append(GameConfig(
            key=key,
            value=value,
            value_type=vtype,
            category="room" if "ROOM" in key else "game",
        ))

    # Also try simple DIR_DOMAIN "/path" patterns
    for m in re.finditer(
        r'#define\s+(\w+)\s+DIR_DOMAIN\s+"/([^"]+)"',
        text,
    ):
        key = m.group(1)
        value = "/방/" + m.group(2)
        if not any(c.key == key for c in configs):
            configs.append(GameConfig(
                key=key,
                value=value,
                value_type="room_vnum",
                category="room",
            ))

    # YEAR_TIME numeric
    for m in re.finditer(r'#define\s+(\w+)\s+(\d+)', text):
        key = m.group(1)
        if not any(c.key == key for c in configs):
            configs.append(GameConfig(
                key=key,
                value=m.group(2),
                value_type="int",
                category="game",
            ))

    return configs


def parse_driver_config(
    config_path: Path,
    encoding: str = "euc-kr",
) -> list[GameConfig]:
    """Parse woong.cfg or config.HanLP driver configuration."""
    raw = config_path.read_bytes()
    text = raw.decode(encoding, errors="replace")

    configs: list[GameConfig] = []

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Format: key : value
        m = re.match(r"([^:]+?)\s*:\s*(.+)", line)
        if not m:
            continue

        key = m.group(1).strip()
        value = m.group(2).strip()

        # Determine type
        if re.match(r"^\d+$", value):
            vtype = "int"
        elif value.lower() in ("true", "false"):
            vtype = "bool"
        else:
            vtype = "str"

        # Categorize
        category = "game"
        if "port" in key.lower():
            category = "port"
        elif "time" in key.lower():
            category = "game"
        elif "maximum" in key.lower() or "size" in key.lower():
            category = "limits"
        elif "file" in key.lower() or "directory" in key.lower():
            category = "paths"

        configs.append(GameConfig(
            key=key,
            value=value,
            value_type=vtype,
            category=category,
        ))

    return configs


def parse_combat_header(
    header_path: Path,
    encoding: str = "euc-kr",
) -> list[GameConfig]:
    """Parse 전투.h for combat system constants."""
    raw = header_path.read_bytes()
    text = raw.decode(encoding, errors="replace")

    configs: list[GameConfig] = []

    for m in re.finditer(r'#define\s+(\w+)\s+(\d+)', text):
        key = m.group(1)
        value = m.group(2)

        # Categorize by constant name
        if key in ("TINY", "SMALL", "MEDIUM", "LARGE", "HUGE"):
            category = "weapon_size"
        elif key in ("NONE", "PIECING", "SLASH", "BLUDGE", "SHOOT"):
            category = "damage_type"
        elif key.startswith(("HELMET", "EARRING", "PENDANT", "BODY_ARMOR",
                            "BELT", "ARM_ARMOR", "GAUNTLET", "ARMLET",
                            "RING", "LEG_ARMOR", "SHOES", "MAX_ARMOR")):
            category = "armor_slot"
        elif key in ("HIT_SELF", "HIT_GROUP", "DROP_WEAPON", "BREAK_WEAPON",
                     "BREAK_ARMOR", "STUN", "DAMAGE_X", "KILL"):
            category = "critical_type"
        elif key.endswith("_UNBALANCED"):
            category = "unbalanced_type"
        else:
            category = "combat"

        configs.append(GameConfig(
            key=key,
            value=value,
            value_type="int",
            category=category,
        ))

    return configs


def parse_stat_formulas(
    monster_c_path: Path,
    encoding: str = "euc-kr",
) -> list[GameConfig]:
    """Extract stat calculation formulas from monster.c as config entries.

    Formulas are stored as string values for documentation/reproduction.
    """
    raw = monster_c_path.read_bytes()
    text = raw.decode(encoding, errors="replace")

    configs: list[GameConfig] = []

    # Extract sigma function
    if "int sigma(" in text:
        configs.append(GameConfig(
            key="sigma_formula",
            value="sum(1..n-1), cap at 150 then linear: sigma(150)+((n-150)*150)",
            value_type="str",
            category="formula",
            description="Sigma summation function used in stat calculations",
        ))

    # HP formula from setupBody
    hp_m = re.search(
        r'res\s*=\s*\((\d+)\s*\+\s*(\d+)\s*\*\s*\(sig_a\s*/\s*(\d+)\s*\)',
        text,
    )
    if hp_m:
        base, mult, div = hp_m.group(1), hp_m.group(2), hp_m.group(3)
        configs.append(GameConfig(
            key="hp_formula",
            value=f"hp = {base} + {mult} * (sigma(기골) / {div}); defense_type: x2, attack_type: x4",
            value_type="str",
            category="formula",
            description="HP calculation from setupBody()",
        ))

    # SP formula
    sp_m = re.search(
        r'sp\s*=\s*max_sp\s*=\s*\((\d+)\s*\+',
        text,
    )
    if sp_m:
        configs.append(GameConfig(
            key="sp_formula",
            value="sp = 80 + ((sigma(내공)*2 + sigma(지혜)) / 30)",
            value_type="str",
            category="formula",
            description="SP calculation from setupBody()",
        ))

    # MP formula
    mp_m = re.search(
        r'mp\s*=\s*max_mp\s*=\s*\((\d+)\s*\+\s*\(sig_a\s*/\s*(\d+)\)',
        text,
    )
    if mp_m:
        configs.append(GameConfig(
            key="mp_formula",
            value=f"mp = {mp_m.group(1)} + (sigma(민첩) / {mp_m.group(2)})",
            value_type="str",
            category="formula",
            description="MP calculation from setupBody()",
        ))

    # randomStat formula
    if "void randomStat(" in text:
        configs.append(GameConfig(
            key="random_stat_formula",
            value="stat = (level - level/10) + random(level/5); ArmorClass = level/4; WeaponClass = level/4",
            value_type="str",
            category="formula",
            description="Monster stat generation from randomStat(level)",
        ))

    # Exp formula from setAdjExp
    if "void setAdjExp(" in text:
        configs.append(GameConfig(
            key="adj_exp_formula",
            value="exp = ((avg_stat^2) / 12) * adjust",
            value_type="str",
            category="formula",
            description="Experience calculation from setAdjExp(adjust)",
        ))

    # Healing rates
    heal_m = re.findall(r'add(?:Hp|Sp|Mp)\s*\(\s*\(\(\s*get\w+\(\)\s*\*\s*(\d+)\s*\)\s*/\s*100\s*\)', text)
    if heal_m:
        configs.append(GameConfig(
            key="heal_rates_normal",
            value="hp: 8%, sp: 9%, mp: 13% per tick",
            value_type="str",
            category="formula",
            description="Normal healing rates in healBody()",
        ))
        configs.append(GameConfig(
            key="heal_rates_fast",
            value="hp: 16%, sp: 18%, mp: 26% per tick",
            value_type="str",
            category="formula",
            description="Fast healing rates (setFastHeal rooms)",
        ))

    return configs
