"""Tests for Phase 3: game system configuration parsers.

Unit tests use inline C source samples.
Integration tests use real data from tbaMUD, Simoon, and 3eyes.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from genos.uir.schema import (
    AttributeModifier,
    ExperienceEntry,
    GameConfig,
    LevelTitle,
    PracticeParams,
    SavingThrowEntry,
    ThacOEntry,
    UIR,
)

# ── CircleMUD config_parser unit tests ────────────────────────────────


class TestCircleMudConfigParser:
    """Unit tests with inline C source samples."""

    def _make_src_dir(self, tmp_path, files: dict[str, str]) -> Path:
        """Create a temporary src dir with given files."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        for name, content in files.items():
            (src_dir / name).write_text(content, encoding="utf-8")
        return src_dir

    def test_parse_game_config(self, tmp_path):
        from genos.adapters.circlemud.config_parser import parse_game_config

        src_dir = self._make_src_dir(tmp_path, {
            "config.c": textwrap.dedent("""\
                int pk_setting = 0;
                int max_exp_gain = 100000;
                int dts_are_dumps = YES;
                room_vnum mortal_start_room = 3001;
                ush_int DFLT_PORT = 4000;
                int idle_max_level = LVL_IMMORT;
            """),
        })

        configs = parse_game_config(src_dir)
        assert len(configs) >= 5

        by_key = {c.key: c for c in configs}
        assert by_key["pk_setting"].value == "0"
        assert by_key["pk_setting"].category == "pk"
        assert by_key["max_exp_gain"].value == "100000"
        assert by_key["dts_are_dumps"].value == "1"
        assert by_key["dts_are_dumps"].value_type == "bool"
        assert by_key["mortal_start_room"].value == "3001"
        assert by_key["mortal_start_room"].value_type == "room_vnum"
        assert by_key["DFLT_PORT"].value == "4000"
        assert by_key["idle_max_level"].value == "31"

    def test_parse_exp_table(self, tmp_path):
        from genos.adapters.circlemud.config_parser import parse_exp_table

        src_dir = self._make_src_dir(tmp_path, {
            "class.c": textwrap.dedent("""\
                int level_exp(int chclass, int level) {
                  switch (chclass) {
                    case CLASS_MAGIC_USER:
                    switch (level) {
                      case  0: return 0;
                      case  1: return 1;
                      case  2: return 2500;
                    }
                    break;
                    case CLASS_WARRIOR:
                    switch (level) {
                      case  0: return 0;
                      case  1: return 1;
                      case  2: return 2000;
                    }
                    break;
                  }
                  return 123456;
                }
            """),
        })

        entries = parse_exp_table(src_dir)
        assert len(entries) == 6

        mage_entries = [e for e in entries if e.class_id == 0]
        assert len(mage_entries) == 3
        assert mage_entries[2].exp_required == 2500

        warrior_entries = [e for e in entries if e.class_id == 3]
        assert len(warrior_entries) == 3
        assert warrior_entries[2].exp_required == 2000

    def test_parse_thac0_table(self, tmp_path):
        from genos.adapters.circlemud.config_parser import parse_thac0_table

        src_dir = self._make_src_dir(tmp_path, {
            "class.c": textwrap.dedent("""\
                int thaco(int class_num, int level) {
                  switch (class_num) {
                  case CLASS_MAGIC_USER:
                    switch (level) {
                    case  0: return 100;
                    case  1: return  20;
                    case  2: return  20;
                    case  3: return  20;
                    default:
                      log("SYSERR: Missing level for mage thac0.");
                    }
                  case CLASS_WARRIOR:
                    switch (level) {
                    case  0: return 100;
                    case  1: return  20;
                    case  2: return  19;
                    default:
                      log("SYSERR: Missing level for warrior thac0.");
                    }
                  }
                  return 100;
                }
            """),
        })

        entries = parse_thac0_table(src_dir)
        assert len(entries) >= 5

        mage = [e for e in entries if e.class_id == 0]
        assert mage[0].thac0 == 100  # level 0
        assert mage[1].thac0 == 20   # level 1

        warrior = [e for e in entries if e.class_id == 3]
        assert warrior[2].thac0 == 19  # level 2

    def test_parse_saving_throws(self, tmp_path):
        from genos.adapters.circlemud.config_parser import parse_saving_throws

        src_dir = self._make_src_dir(tmp_path, {
            "class.c": textwrap.dedent("""\
                byte saving_throws(int class_num, int type, int level) {
                  switch (class_num) {
                  case CLASS_MAGIC_USER:
                    switch (type) {
                    case SAVING_PARA:
                      switch (level) {
                      case  0: return 90;
                      case  1: return 70;
                      default:
                        break;
                      }
                    case SAVING_SPELL:
                      switch (level) {
                      case  0: return 90;
                      case  1: return 60;
                      default:
                        break;
                      }
                    }
                  }
                  return 100;
                }
            """),
        })

        entries = parse_saving_throws(src_dir)
        assert len(entries) >= 2

        para = [e for e in entries if e.save_type == 0]
        assert para[0].save_value == 90
        assert para[1].save_value == 70

        spell = [e for e in entries if e.save_type == 4]
        assert spell[0].save_value == 90
        assert spell[1].save_value == 60

    def test_parse_level_titles(self, tmp_path):
        from genos.adapters.circlemud.config_parser import parse_level_titles

        src_dir = self._make_src_dir(tmp_path, {
            "class.c": textwrap.dedent("""\
                const char *title_male(int chclass, int level) {
                  switch (chclass) {
                    case CLASS_WARRIOR:
                    switch(level) {
                      case  1: return "the Swordpupil";
                      case  2: return "the Recruit";
                      default: return "the Warrior";
                    }
                  }
                  return "the Classless";
                }
                const char *title_female(int chclass, int level) {
                  switch (chclass) {
                    case CLASS_WARRIOR:
                    switch(level) {
                      case  1: return "the Swordpupil";
                      case  2: return "the Recruit";
                      default: return "the Warrior";
                    }
                  }
                  return "the Classless";
                }
            """),
        })

        entries = parse_level_titles(src_dir)
        assert len(entries) >= 4

        male = [e for e in entries if e.gender == "male"]
        assert male[0].title == "the Swordpupil"
        assert male[0].class_id == 3  # warrior

    def test_parse_practice_params(self, tmp_path):
        from genos.adapters.circlemud.config_parser import parse_practice_params

        src_dir = self._make_src_dir(tmp_path, {
            "class.c": textwrap.dedent("""\
                #define SPELL 0
                #define SKILL 1
                int prac_params[4][NUM_CLASSES] = {
                  { 95,  95,  85,  80 },
                  { 100, 100, 12,  12 },
                  { 25,  25,  0,   0  },
                  { SPELL, SPELL, SKILL, SKILL },
                };
            """),
        })

        entries = parse_practice_params(src_dir)
        assert len(entries) == 4

        assert entries[0].class_id == 0
        assert entries[0].learned_level == 95
        assert entries[0].prac_type == "spell"

        assert entries[3].class_id == 3
        assert entries[3].learned_level == 80
        assert entries[3].prac_type == "skill"
        assert entries[3].max_per_practice == 12

    def test_parse_attribute_modifiers(self, tmp_path):
        from genos.adapters.circlemud.config_parser import parse_attribute_modifiers

        src_dir = self._make_src_dir(tmp_path, {
            "constants.c": textwrap.dedent("""\
                cpp_extern const struct str_app_type str_app[] = {
                  {-5, -4, 0, 0},
                  {-5, -4, 3, 1},
                  {-3, -2, 3, 2},
                };
                cpp_extern const struct con_app_type con_app[] = {
                  {-4},
                  {-3},
                  {-2},
                };
                cpp_extern const struct wis_app_type wis_app[] = {
                  {0},
                  {0},
                  {0},
                };
            """),
        })

        entries = parse_attribute_modifiers(src_dir)
        str_entries = [e for e in entries if e.stat_name == "strength"]
        assert len(str_entries) == 3
        assert str_entries[0].modifiers["tohit"] == -5
        assert str_entries[0].modifiers["todam"] == -4
        assert str_entries[1].modifiers["carry_weight"] == 3

        con_entries = [e for e in entries if e.stat_name == "constitution"]
        assert len(con_entries) == 3
        assert con_entries[0].modifiers["hitp"] == -4

    def test_parse_missing_files(self, tmp_path):
        """Parser should return empty lists for missing files."""
        from genos.adapters.circlemud.config_parser import (
            parse_attribute_modifiers,
            parse_exp_table,
            parse_game_config,
            parse_level_titles,
            parse_practice_params,
            parse_saving_throws,
            parse_thac0_table,
        )

        src_dir = tmp_path / "nonexistent"
        assert parse_game_config(src_dir) == []
        assert parse_exp_table(src_dir) == []
        assert parse_thac0_table(src_dir) == []
        assert parse_saving_throws(src_dir) == []
        assert parse_level_titles(src_dir) == []
        assert parse_practice_params(src_dir) == []
        assert parse_attribute_modifiers(src_dir) == []


# ── 3eyes config_parser unit tests ────────────────────────────────────


class TestThreeEyesConfigParser:
    """Unit tests for 3eyes global.c parser."""

    def _make_src_dir(self, tmp_path, content: str) -> Path:
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "global.c").write_text(content, encoding="utf-8")
        return src_dir

    def test_parse_thac0_table(self, tmp_path):
        from genos.adapters.threeeyes.config_parser import parse_thac0_table

        src_dir = self._make_src_dir(tmp_path, textwrap.dedent("""\
            short thaco_list[][20] = {
                { 20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20 },
            /*a*/ { 18,18,18,17,17,16,16,15,15,14,14,13,13,12,12,11,10,10, 9, 9 },
            /*b*/ { 20,19,18,17,16,15,14,13,12,11,10, 9, 8, 7, 6, 5, 4, 3, 3, 2 },
            };
        """))

        entries = parse_thac0_table(src_dir)
        # Class 0 is skipped (not in _PLAYER_CLASSES), classes 1,2 are parsed
        assassin = [e for e in entries if e.class_id == 1]
        assert len(assassin) == 20
        assert assassin[0].thac0 == 18  # level 1
        assert assassin[0].level == 1

        barbarian = [e for e in entries if e.class_id == 2]
        assert len(barbarian) == 20
        assert barbarian[0].thac0 == 20  # level 1

    def test_parse_exp_table(self, tmp_path):
        from genos.adapters.threeeyes.config_parser import parse_exp_table

        src_dir = self._make_src_dir(tmp_path, textwrap.dedent("""\
            long level_exp[] = {
            /*  1*/  132,        256,        384,        512,        640,
            /*  6*/  768,        896,       1024,       1280,       1536,
                     0,
            };
        """))

        entries = parse_exp_table(src_dir)
        assert len(entries) == 10
        assert entries[0].level == 1
        assert entries[0].exp_required == 132
        assert entries[0].class_id == 0  # shared
        assert entries[9].exp_required == 1536

    def test_parse_bonus_table(self, tmp_path):
        from genos.adapters.threeeyes.config_parser import parse_bonus_table

        src_dir = self._make_src_dir(tmp_path, textwrap.dedent("""\
            int bonus[] = { -4, -4, -4, -3, -3, -2, -2, -1, -1, -1 };
        """))

        entries = parse_bonus_table(src_dir)
        assert len(entries) == 10
        assert entries[0].stat_name == "bonus"
        assert entries[0].score == 0
        assert entries[0].modifiers["bonus"] == -4
        assert entries[5].modifiers["bonus"] == -2

    def test_parse_class_stats(self, tmp_path):
        from genos.adapters.threeeyes.config_parser import parse_class_stats

        src_dir = self._make_src_dir(tmp_path, textwrap.dedent("""\
            struct {} class_stats[13] = {
                { 1,  1,  1,  1,  1,  1,  1},
                { 55,  50,  6,  2,  1,  6,  0},  /* assassin */
                { 57,  50,  7,  1,  2,  3,  1},  /* barbarian */
            };
        """))

        result = parse_class_stats(src_dir)
        assert 1 in result  # assassin
        assert result[1]["hpstart"] == 55
        assert result[1]["mpstart"] == 50
        assert result[1]["hp"] == 6

        assert 2 in result  # barbarian
        assert result[2]["hpstart"] == 57

    def test_parse_missing_file(self, tmp_path):
        from genos.adapters.threeeyes.config_parser import (
            parse_bonus_table,
            parse_class_stats,
            parse_exp_table,
            parse_level_cycle,
            parse_thac0_table,
        )

        src_dir = tmp_path / "nonexistent"
        assert parse_thac0_table(src_dir) == []
        assert parse_exp_table(src_dir) == []
        assert parse_bonus_table(src_dir) == []
        assert parse_class_stats(src_dir) == {}
        assert parse_level_cycle(src_dir) == {}


# ── Schema tests ──────────────────────────────────────────────────────


class TestPhase3Schema:
    """Test Phase 3 dataclasses and UIR integration."""

    def test_game_config_defaults(self):
        gc = GameConfig()
        assert gc.key == ""
        assert gc.value_type == "int"

    def test_experience_entry(self):
        e = ExperienceEntry(class_id=0, level=10, exp_required=250000)
        assert e.exp_required == 250000

    def test_thac0_entry(self):
        t = ThacOEntry(class_id=3, level=1, thac0=20)
        assert t.thac0 == 20

    def test_saving_throw_entry(self):
        s = SavingThrowEntry(class_id=0, save_type=4, level=1, save_value=60)
        assert s.save_type == 4

    def test_level_title(self):
        lt = LevelTitle(class_id=3, level=1, gender="male", title="the Swordpupil")
        assert lt.title == "the Swordpupil"

    def test_attribute_modifier(self):
        am = AttributeModifier(stat_name="strength", score=18, modifiers={"tohit": 1, "todam": 2})
        assert am.modifiers["tohit"] == 1

    def test_practice_params(self):
        pp = PracticeParams(class_id=0, learned_level=95, prac_type="spell")
        assert pp.prac_type == "spell"

    def test_uir_has_phase3_fields(self):
        uir = UIR()
        assert uir.game_configs == []
        assert uir.experience_table == []
        assert uir.thac0_table == []
        assert uir.saving_throws == []
        assert uir.level_titles == []
        assert uir.attribute_modifiers == []
        assert uir.practice_params == []

    def test_migration_stats_has_phase3_counters(self):
        from genos.uir.schema import MigrationStats
        stats = MigrationStats()
        assert stats.total_game_configs == 0
        assert stats.total_exp_entries == 0
        assert stats.total_thac0_entries == 0
        assert stats.total_saving_throw_entries == 0
        assert stats.total_level_titles == 0
        assert stats.total_attribute_modifiers == 0


# ── Integration tests with real data ──────────────────────────────────

TBAMUD_PATH = Path("/home/genos/workspace/tbamud")
SIMOON_PATH = Path("/home/genos/workspace/simoon")
THREEEYES_PATH = Path("/home/genos/workspace/3eyes")


@pytest.mark.skipif(not TBAMUD_PATH.exists(), reason="tbaMUD not available")
class TestTbaMudIntegration:
    """Integration tests using real tbaMUD source."""

    def test_game_config_count(self):
        from genos.adapters.circlemud.config_parser import parse_game_config
        configs = parse_game_config(TBAMUD_PATH / "src")
        assert len(configs) >= 30
        by_key = {c.key: c for c in configs}
        assert "pk_setting" in by_key
        assert "mortal_start_room" in by_key

    def test_exp_table_count(self):
        from genos.adapters.circlemud.config_parser import parse_exp_table
        entries = parse_exp_table(TBAMUD_PATH / "src")
        # 4 classes × ~32 levels each
        assert len(entries) >= 120
        # Check structure
        mage = [e for e in entries if e.class_id == 0]
        assert len(mage) >= 30
        assert mage[0].level == 0
        assert mage[0].exp_required == 0
        assert mage[1].exp_required == 1

    def test_thac0_table_count(self):
        from genos.adapters.circlemud.config_parser import parse_thac0_table
        entries = parse_thac0_table(TBAMUD_PATH / "src")
        # 4 classes × 35 levels each
        assert len(entries) >= 136

    def test_saving_throws_count(self):
        from genos.adapters.circlemud.config_parser import parse_saving_throws
        entries = parse_saving_throws(TBAMUD_PATH / "src")
        # 4 classes × 5 types × 41 levels = 820
        assert len(entries) >= 800

    def test_level_titles_count(self):
        from genos.adapters.circlemud.config_parser import parse_level_titles
        entries = parse_level_titles(TBAMUD_PATH / "src")
        # Male + female, ~34 levels × 4 classes × 2 genders
        assert len(entries) >= 100

    def test_attribute_modifiers_count(self):
        from genos.adapters.circlemud.config_parser import parse_attribute_modifiers
        entries = parse_attribute_modifiers(TBAMUD_PATH / "src")
        # 6 tables with 26+ entries each
        assert len(entries) >= 150

    def test_practice_params_count(self):
        from genos.adapters.circlemud.config_parser import parse_practice_params
        entries = parse_practice_params(TBAMUD_PATH / "src")
        assert len(entries) == 4

    def test_full_adapter_parse(self):
        from genos.adapters.circlemud.adapter import CircleMudAdapter
        adapter = CircleMudAdapter(TBAMUD_PATH)
        uir = adapter.parse()
        assert len(uir.game_configs) >= 30
        assert len(uir.experience_table) >= 120
        assert len(uir.thac0_table) >= 136
        assert len(uir.saving_throws) >= 800
        assert len(uir.level_titles) >= 100
        assert len(uir.attribute_modifiers) >= 150
        assert len(uir.practice_params) == 4
        assert uir.migration_stats.total_game_configs >= 30
        assert uir.migration_stats.total_exp_entries >= 120


@pytest.mark.skipif(not SIMOON_PATH.exists(), reason="Simoon not available")
class TestSimoonIntegration:
    """Integration tests using real Simoon source."""

    def test_game_config_count(self):
        from genos.adapters.simoon.config_parser import parse_game_config
        configs = parse_game_config(SIMOON_PATH / "src")
        assert len(configs) >= 20

    def test_titles_and_exp(self):
        from genos.adapters.simoon.config_parser import parse_simoon_titles
        titles, exp = parse_simoon_titles(SIMOON_PATH / "src")
        assert len(titles) >= 300  # male + female
        assert len(exp) >= 150

    def test_attribute_modifiers(self):
        from genos.adapters.simoon.config_parser import parse_attribute_modifiers
        entries = parse_attribute_modifiers(SIMOON_PATH / "src")
        assert len(entries) >= 100

    def test_practice_params(self):
        from genos.adapters.simoon.config_parser import parse_practice_params
        entries = parse_practice_params(SIMOON_PATH / "src")
        assert len(entries) == 7  # Simoon has 7 classes

    def test_train_params(self):
        from genos.adapters.simoon.config_parser import parse_train_params
        entries = parse_train_params(SIMOON_PATH / "src")
        assert len(entries) >= 6
        # Check that stat caps are in extensions
        assert "train_stat_caps" in entries[0].extensions

    def test_full_adapter_parse(self):
        from genos.adapters.simoon.adapter import SimoonAdapter
        adapter = SimoonAdapter(SIMOON_PATH)
        uir = adapter.parse()
        assert len(uir.game_configs) >= 20
        assert len(uir.experience_table) >= 150
        assert len(uir.level_titles) >= 300
        assert len(uir.attribute_modifiers) >= 100
        assert len(uir.practice_params) == 7


@pytest.mark.skipif(not THREEEYES_PATH.exists(), reason="3eyes not available")
class TestThreeEyesIntegration:
    """Integration tests using real 3eyes source."""

    def test_thac0_table(self):
        from genos.adapters.threeeyes.config_parser import parse_thac0_table
        entries = parse_thac0_table(THREEEYES_PATH / "src")
        # 8 classes × 20 levels = 160
        assert len(entries) == 160

    def test_exp_table(self):
        from genos.adapters.threeeyes.config_parser import parse_exp_table
        entries = parse_exp_table(THREEEYES_PATH / "src")
        assert len(entries) >= 200
        assert entries[0].level == 1
        assert entries[0].exp_required == 132

    def test_bonus_table(self):
        from genos.adapters.threeeyes.config_parser import parse_bonus_table
        entries = parse_bonus_table(THREEEYES_PATH / "src")
        assert len(entries) == 160
        assert entries[0].modifiers["bonus"] == -4

    def test_class_stats(self):
        from genos.adapters.threeeyes.config_parser import parse_class_stats
        stats = parse_class_stats(THREEEYES_PATH / "src")
        assert len(stats) == 8
        assert stats[1]["hpstart"] == 55  # assassin

    def test_level_cycle(self):
        from genos.adapters.threeeyes.config_parser import parse_level_cycle
        result = parse_level_cycle(THREEEYES_PATH / "src")
        assert len(result) == 8
        for class_id, cycle in result.items():
            assert len(cycle) == 10

    def test_full_adapter_parse(self):
        from genos.adapters.threeeyes.adapter import ThreeEyesAdapter
        adapter = ThreeEyesAdapter(THREEEYES_PATH)
        uir = adapter.parse()
        assert len(uir.thac0_table) == 160
        assert len(uir.experience_table) >= 200
        assert len(uir.attribute_modifiers) == 160
        assert uir.migration_stats.total_thac0_entries == 160
        assert uir.migration_stats.total_exp_entries >= 200
        # class_stats should be merged into character_classes
        for cls in uir.character_classes:
            assert "hpstart" in cls.extensions
        # level_cycle should be in extensions
        assert "level_cycle" in uir.extensions


# ── Compiler tests ────────────────────────────────────────────────────


class TestCompilerPhase3:
    """Test that Phase 3 data flows through compiler."""

    def test_ddl_has_phase3_tables(self):
        from io import StringIO
        from genos.compiler.db_generator import generate_ddl
        uir = UIR()
        out = StringIO()
        generate_ddl(uir, out)
        ddl = out.getvalue()
        assert "game_configs" in ddl
        # 6 legacy tables merged into game_tables
        assert "game_tables" in ddl

    def test_seed_data_phase3(self):
        from io import StringIO
        from genos.compiler.db_generator import generate_seed_data
        uir = UIR()
        uir.game_configs = [GameConfig(key="test", value="42", category="game")]
        uir.experience_table = [ExperienceEntry(class_id=0, level=1, exp_required=100)]
        uir.thac0_table = [ThacOEntry(class_id=0, level=1, thac0=20)]
        uir.saving_throws = [SavingThrowEntry(class_id=0, save_type=0, level=1, save_value=70)]
        uir.level_titles = [LevelTitle(class_id=0, level=1, gender="male", title="Test")]
        uir.attribute_modifiers = [AttributeModifier(stat_name="str", score=0, modifiers={"tohit": -5})]
        uir.practice_params = [PracticeParams(class_id=0, learned_level=95)]

        out = StringIO()
        generate_seed_data(uir, out)
        sql = out.getvalue()
        assert "INSERT INTO game_configs" in sql
        # All 6 legacy tables now go into game_tables
        assert "INSERT INTO game_tables" in sql
        assert "exp_table" in sql
        assert "thac0" in sql
        assert "saving_throw" in sql
        assert "level_title" in sql
        assert "stat_bonus" in sql
        assert "practice" in sql

    def test_lua_config_generation(self):
        from io import StringIO
        from genos.compiler.lua_generator import generate_config_lua
        uir = UIR()
        uir.game_configs = [
            GameConfig(key="pk_setting", value="0", value_type="int", category="pk"),
            GameConfig(key="free_rent", value="1", value_type="bool", category="rent"),
        ]
        out = StringIO()
        generate_config_lua(uir, out)
        lua = out.getvalue()
        assert "Config.pk" in lua
        assert "pk_setting = 0" in lua
        assert "free_rent = true" in lua

    def test_lua_exp_table_generation(self):
        from io import StringIO
        from genos.compiler.lua_generator import generate_exp_table_lua
        uir = UIR()
        uir.experience_table = [
            ExperienceEntry(class_id=0, level=1, exp_required=1),
            ExperienceEntry(class_id=0, level=2, exp_required=2500),
        ]
        out = StringIO()
        generate_exp_table_lua(uir, out)
        lua = out.getvalue()
        assert "ExpTables[0]" in lua
        assert "[1] = 1" in lua
        assert "[2] = 2500" in lua

    def test_lua_stat_tables_generation(self):
        from io import StringIO
        from genos.compiler.lua_generator import generate_stat_tables_lua
        uir = UIR()
        uir.thac0_table = [ThacOEntry(class_id=0, level=1, thac0=20)]
        uir.attribute_modifiers = [AttributeModifier(stat_name="strength", score=0, modifiers={"tohit": -5})]
        out = StringIO()
        generate_stat_tables_lua(uir, out)
        lua = out.getvalue()
        assert "StatTables.thac0" in lua
        assert "StatTables.strength" in lua
