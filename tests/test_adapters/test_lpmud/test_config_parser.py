"""Tests for LP-MUD config_parser."""

from pathlib import Path

import pytest

from genos.adapters.lpmud.config_parser import (
    parse_combat_header,
    parse_driver_config,
    parse_settings_header,
    parse_stat_formulas,
)


def _write(tmp_path: Path, name: str, content: str, encoding: str = "euc-kr") -> Path:
    p = tmp_path / name
    p.write_bytes(content.encode(encoding))
    return p


# ── parse_settings_header ─────────────────────────────────────────

class TestParseSettingsHeader:
    def test_extracts_room_defines(self, tmp_path):
        text = (
            '#ifndef __CONFIGH__\n'
            '#define __CONFIGH__\n'
            '#define START_ROOM DIR_DOMAIN "/장백성/마을광장"\n'
            '#define NOVICE_ROOM DIR_DOMAIN "/초보지역/선택의방"\n'
            '#define FREEZER_ROOM DIR_DOMAIN "/냉동실"\n'
            '#define YEAR_TIME 86400\n'
            '#endif\n'
        )
        p = _write(tmp_path, "세팅.h", text)
        configs = parse_settings_header(p)

        keys = {c.key for c in configs}
        assert "YEAR_TIME" in keys
        # YEAR_TIME should be int type
        yt = next(c for c in configs if c.key == "YEAR_TIME")
        assert yt.value == "86400"
        assert yt.value_type == "int"

    def test_dir_domain_paths(self, tmp_path):
        text = '#define START_ROOM DIR_DOMAIN "/장백성/마을광장"\n'
        p = _write(tmp_path, "세팅.h", text)
        configs = parse_settings_header(p)

        sr = [c for c in configs if c.key == "START_ROOM"]
        assert len(sr) >= 1
        assert sr[0].category == "room"

    def test_empty_file(self, tmp_path):
        p = _write(tmp_path, "empty.h", "")
        assert parse_settings_header(p) == []


# ── parse_driver_config ───────────────────────────────────────────

class TestParseDriverConfig:
    def test_parses_key_value_pairs(self, tmp_path):
        text = (
            "# comment line\n"
            "name : 십웅기\n"
            "maximum users : 50\n"
            "port number : 9999\n"
            "address server ip : localhost\n"
        )
        p = _write(tmp_path, "woong.cfg", text)
        configs = parse_driver_config(p)

        keys = {c.key: c for c in configs}
        assert "name" in keys
        assert keys["name"].value == "십웅기"
        assert keys["name"].value_type == "str"

        assert "maximum users" in keys
        assert keys["maximum users"].value == "50"
        assert keys["maximum users"].value_type == "int"
        assert keys["maximum users"].category == "limits"

    def test_skips_comments_and_empty(self, tmp_path):
        text = "# this is a comment\n\n# another\n"
        p = _write(tmp_path, "empty.cfg", text)
        assert parse_driver_config(p) == []

    def test_port_category(self, tmp_path):
        text = "port number : 9999\n"
        p = _write(tmp_path, "port.cfg", text)
        configs = parse_driver_config(p)
        assert configs[0].category == "port"


# ── parse_combat_header ───────────────────────────────────────────

class TestParseCombatHeader:
    def test_weapon_sizes(self, tmp_path):
        text = (
            "#define TINY 1\n"
            "#define SMALL 2\n"
            "#define MEDIUM 3\n"
            "#define LARGE 4\n"
            "#define HUGE 5\n"
        )
        p = _write(tmp_path, "전투.h", text)
        configs = parse_combat_header(p)

        sizes = [c for c in configs if c.category == "weapon_size"]
        assert len(sizes) == 5
        assert all(c.value_type == "int" for c in sizes)

    def test_damage_types(self, tmp_path):
        text = (
            "#define NONE 0\n"
            "#define PIECING 1\n"
            "#define SLASH 2\n"
            "#define BLUDGE 3\n"
            "#define SHOOT 4\n"
        )
        p = _write(tmp_path, "전투.h", text)
        configs = parse_combat_header(p)

        dtypes = [c for c in configs if c.category == "damage_type"]
        assert len(dtypes) == 5

    def test_armor_slots(self, tmp_path):
        text = (
            "#define HELMET 1\n"
            "#define BODY_ARMOR 4\n"
            "#define MAX_ARMOR_NUM 22\n"
        )
        p = _write(tmp_path, "전투.h", text)
        configs = parse_combat_header(p)

        armor = [c for c in configs if c.category == "armor_slot"]
        assert len(armor) == 3

    def test_critical_types(self, tmp_path):
        text = "#define HIT_SELF 1\n#define KILL 8\n"
        p = _write(tmp_path, "전투.h", text)
        configs = parse_combat_header(p)

        crits = [c for c in configs if c.category == "critical_type"]
        assert len(crits) == 2

    def test_unbalanced_types(self, tmp_path):
        text = "#define SHIELD_UNBALANCED 1\n#define PARRY_UNBALANCED 2\n"
        p = _write(tmp_path, "전투.h", text)
        configs = parse_combat_header(p)

        unbal = [c for c in configs if c.category == "unbalanced_type"]
        assert len(unbal) == 2


# ── parse_stat_formulas ───────────────────────────────────────────

class TestParseStatFormulas:
    def test_sigma_detected(self, tmp_path):
        text = 'int sigma(int n) { int res; ... }'
        p = _write(tmp_path, "monster.c", text, encoding="utf-8")
        configs = parse_stat_formulas(p, encoding="utf-8")

        keys = {c.key for c in configs}
        assert "sigma_formula" in keys

    def test_random_stat_detected(self, tmp_path):
        text = 'void randomStat(int level) { ... }'
        p = _write(tmp_path, "monster.c", text, encoding="utf-8")
        configs = parse_stat_formulas(p, encoding="utf-8")

        keys = {c.key for c in configs}
        assert "random_stat_formula" in keys

    def test_adj_exp_detected(self, tmp_path):
        text = 'void setAdjExp(int adjust) { ... }'
        p = _write(tmp_path, "monster.c", text, encoding="utf-8")
        configs = parse_stat_formulas(p, encoding="utf-8")

        keys = {c.key for c in configs}
        assert "adj_exp_formula" in keys

    def test_empty_file_no_formulas(self, tmp_path):
        text = '// nothing here'
        p = _write(tmp_path, "monster.c", text, encoding="utf-8")
        configs = parse_stat_formulas(p, encoding="utf-8")
        assert configs == []

    def test_all_formulas_are_str_type(self, tmp_path):
        text = (
            'int sigma(int n) { }\n'
            'void randomStat(int level) { }\n'
            'void setAdjExp(int adjust) { }\n'
        )
        p = _write(tmp_path, "monster.c", text, encoding="utf-8")
        configs = parse_stat_formulas(p, encoding="utf-8")
        assert all(c.value_type == "str" for c in configs)
        assert all(c.category == "formula" for c in configs)


# ── Real data tests ───────────────────────────────────────────────

REAL_10WOONGI = Path("/home/genos/workspace/10woongi")


@pytest.mark.skipif(
    not REAL_10WOONGI.exists(),
    reason="10woongi data not available",
)
class TestRealData:
    def test_real_settings_header(self):
        p = REAL_10WOONGI / "lib" / "삽입파일" / "세팅.h"
        configs = parse_settings_header(p)
        keys = {c.key for c in configs}
        assert "YEAR_TIME" in keys
        assert "START_ROOM" in keys or any("ROOM" in k for k in keys)
        assert len(configs) >= 3

    def test_real_driver_config(self):
        p = REAL_10WOONGI / "bin" / "woong.cfg"
        configs = parse_driver_config(p)
        keys = {c.key: c for c in configs}
        assert "name" in keys
        assert keys["name"].value == "십웅기"
        assert len(configs) >= 10

    def test_real_combat_header(self):
        p = REAL_10WOONGI / "lib" / "삽입파일" / "전투.h"
        configs = parse_combat_header(p)
        categories = {c.category for c in configs}
        assert "weapon_size" in categories
        assert "damage_type" in categories
        assert "armor_slot" in categories
        assert len(configs) >= 30

    def test_real_stat_formulas(self):
        p = REAL_10WOONGI / "lib" / "구조" / "monster.c"
        configs = parse_stat_formulas(p)
        keys = {c.key for c in configs}
        assert "sigma_formula" in keys
        assert "random_stat_formula" in keys
        assert "adj_exp_formula" in keys
        assert len(configs) >= 5
