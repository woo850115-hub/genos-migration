"""Phase 2 tests: Socials, Help, Commands, Skills, Races parsers."""

from __future__ import annotations

import io
import textwrap
from pathlib import Path

import pytest

from genos.uir.schema import (
    Command,
    HelpEntry,
    Race,
    Skill,
    Social,
    UIR,
)

# ── Paths ──────────────────────────────────────────────────────────────

TBAMUD_ROOT = Path("/home/genos/workspace/tbamud")
SIMOON_ROOT = Path("/home/genos/workspace/simoon")

has_tbamud = TBAMUD_ROOT.exists()
has_simoon = SIMOON_ROOT.exists()


# ══════════════════════════════════════════════════════════════════════
# UNIT TESTS (inline samples, no external data needed)
# ══════════════════════════════════════════════════════════════════════


class TestSocialParser:
    """Test social_parser with inline samples."""

    def test_parse_basic_social(self):
        from genos.adapters.circlemud.social_parser import _parse_socials_text

        text = textwrap.dedent("""\
        accuse 0 5
        Accuse who??
        #
        You look accusingly at $M.
        $n looks accusingly at $N.
        $n looks accusingly at you.
        Accuse somebody who's not even there??
        You accuse yourself.
        $n seems to have a bad conscience.

        $
        """)
        socials = _parse_socials_text(text)
        assert len(socials) == 1

        s = socials[0]
        assert s.command == "accuse"
        assert s.min_victim_position == 0
        assert s.flags == 5
        assert s.no_arg_to_char == "Accuse who??"

    def test_parse_multiple_socials(self):
        from genos.adapters.circlemud.social_parser import _parse_socials_text

        text = textwrap.dedent("""\
        applaud 0 0
        Clap, clap, clap.
        $n gives a round of applause.
        #

        blush 0 0
        Your cheeks are burning.
        $n blushes.
        #

        $
        """)
        socials = _parse_socials_text(text)
        assert len(socials) == 2
        assert socials[0].command == "applaud"
        assert socials[1].command == "blush"
        assert socials[0].no_arg_to_char == "Clap, clap, clap."
        assert socials[0].no_arg_to_room == "$n gives a round of applause."

    def test_parse_social_with_all_messages(self):
        from genos.adapters.circlemud.social_parser import _parse_socials_text

        text = textwrap.dedent("""\
        bow 0 5
        You bow deeply.
        $n bows deeply.
        You bow before $M.
        $n bows before $N.
        $n bows before you.
        Who's that?
        You kiss your toes.
        $n folds up like a jacknife and kisses $s own toes.

        $
        """)
        socials = _parse_socials_text(text)
        assert len(socials) == 1
        s = socials[0]
        assert s.no_arg_to_char == "You bow deeply."
        assert s.no_arg_to_room == "$n bows deeply."
        assert s.found_to_char == "You bow before $M."
        assert s.found_to_room == "$n bows before $N."
        assert s.found_to_victim == "$n bows before you."
        assert s.not_found == "Who's that?"
        assert s.self_to_char == "You kiss your toes."
        assert s.self_to_room == "$n folds up like a jacknife and kisses $s own toes."

    def test_empty_file(self):
        from genos.adapters.circlemud.social_parser import _parse_socials_text

        socials = _parse_socials_text("$\n")
        assert socials == []


class TestHelpParser:
    """Test help_parser with inline samples."""

    def test_parse_basic_help(self):
        from genos.adapters.circlemud.help_parser import _parse_help_text

        text = textwrap.dedent("""\
        LOOK

        Usage: look [at] [object | character | direction]

        The basic command to see the world around you.
        #0
        """)
        entries = _parse_help_text(text)
        assert len(entries) == 1
        e = entries[0]
        assert e.keywords == ["LOOK"]
        assert e.min_level == 0
        assert "look" in e.text.lower()

    def test_parse_multiple_entries(self):
        from genos.adapters.circlemud.help_parser import _parse_help_text

        text = textwrap.dedent("""\
        NORTH SOUTH EAST WEST

        Move in the specified direction.
        #0
        HELP

        Get help on a topic.
        #0
        """)
        entries = _parse_help_text(text)
        assert len(entries) == 2
        assert entries[0].keywords == ["NORTH", "SOUTH", "EAST", "WEST"]
        assert entries[1].keywords == ["HELP"]

    def test_parse_immortal_help(self):
        from genos.adapters.circlemud.help_parser import _parse_help_text

        text = textwrap.dedent("""\
        WIZCOMMAND

        An immortal-only command.
        #31
        """)
        entries = _parse_help_text(text)
        assert len(entries) == 1
        assert entries[0].min_level == 31

    def test_parse_hash_only_terminator(self):
        from genos.adapters.circlemud.help_parser import _parse_help_text

        text = textwrap.dedent("""\
        TEST

        Some help text.
        #
        """)
        entries = _parse_help_text(text)
        assert len(entries) == 1
        assert entries[0].min_level == 0


class TestCmdParser:
    """Test cmd_parser with inline samples."""

    def test_parse_tbamud_commands(self):
        from genos.adapters.circlemud.cmd_parser import _parse_cmd_text

        text = textwrap.dedent("""\
        const struct command_info cmd_info[] = {
          { "RESERVED", "", 0, 0, 0, 0 },
          { "north"    , "n"       , POS_STANDING, do_move     , 0, 1 },
          { "cast"     , "c"       , POS_SITTING , do_cast     , 1, 0 },
          { "\\n", "\\n", 0, 0, 0, 0 }
        };
        """)
        cmds = _parse_cmd_text(text, has_min_match=True)
        # RESERVED and \n are filtered
        assert len(cmds) >= 2
        north = next(c for c in cmds if c.name == "north")
        assert north.min_match == "n"
        assert north.min_position == 8  # POS_STANDING
        assert north.handler == "do_move"

        cast = next(c for c in cmds if c.name == "cast")
        assert cast.min_match == "c"
        assert cast.min_position == 6  # POS_SITTING
        assert cast.min_level == 1

    def test_parse_simoon_commands(self):
        from genos.adapters.circlemud.cmd_parser import _parse_cmd_text

        text = textwrap.dedent("""\
        const struct command_info cmd_info[] = {
          { "RESERVED", 0, 0, 0, 0 },
          { "at"       , POS_DEAD    , do_at       , 113, 0 },
          { "\\n", 0, 0, 0, 0 }
        };
        """)
        cmds = _parse_cmd_text(text, has_min_match=False)
        assert len(cmds) >= 1
        at = next(c for c in cmds if c.name == "at")
        assert at.min_match == ""
        assert at.min_level == 113
        assert at.handler == "do_at"


class TestSkillParser:
    """Test skill_parser with inline samples."""

    def test_parse_spell_defines(self):
        from genos.adapters.circlemud.skill_parser import _parse_spell_defines

        import tempfile

        content = textwrap.dedent("""\
        #define SPELL_ARMOR 1
        #define SPELL_BLESS 3
        #define SKILL_BACKSTAB 131
        #define SPELL_RESERVED_DBC 0
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".h", delete=False) as f:
            f.write(content)
            f.flush()
            result = _parse_spell_defines(Path(f.name), "utf-8")

        assert result["SPELL_ARMOR"] == 1
        assert result["SPELL_BLESS"] == 3
        assert result["SKILL_BACKSTAB"] == 131
        assert result["SPELL_RESERVED_DBC"] == 0

    def test_parse_spello_args_tbamud(self):
        from genos.adapters.circlemud.skill_parser import _parse_spello_args

        args = 'SPELL_ARMOR, "armor", 30, 15, 3, POS_FIGHTING, TAR_CHAR_ROOM, FALSE, MAG_AFFECTS, "You feel less protected."'
        id_map = {"SPELL_ARMOR": 1}
        skill = _parse_spello_args(args, id_map, has_spell_name=True)
        assert skill is not None
        assert skill.id == 1
        assert skill.name == "armor"
        assert skill.max_mana == 30
        assert skill.min_mana == 15
        assert skill.mana_change == 3
        assert skill.spell_type == "spell"
        assert skill.wearoff_msg == "You feel less protected."

    def test_parse_spello_args_simoon(self):
        from genos.adapters.circlemud.skill_parser import _parse_spello_args

        args = 'SPELL_ARMOR, 30, 15, 3, POS_FIGHTING, TAR_CHAR_ROOM, FALSE, MAG_AFFECTS'
        id_map = {"SPELL_ARMOR": 1}
        skill = _parse_spello_args(args, id_map, has_spell_name=False)
        assert skill is not None
        assert skill.id == 1
        assert skill.name == "armor"
        assert skill.max_mana == 30
        assert skill.spell_type == "spell"

    def test_parse_spell_levels(self):
        from genos.adapters.circlemud.skill_parser import _parse_spell_levels

        import tempfile

        content = textwrap.dedent("""\
        void init_spell_levels(void) {
          spell_level(SPELL_MAGIC_MISSILE, CLASS_MAGIC_USER, 1);
          spell_level(SPELL_ARMOR, CLASS_CLERIC, 1);
          spell_level(SPELL_BACKSTAB, CLASS_THIEF, 5);
        }
        """)
        id_map = {"SPELL_MAGIC_MISSILE": 32, "SPELL_ARMOR": 1, "SPELL_BACKSTAB": 131}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write(content)
            f.flush()
            result = _parse_spell_levels(Path(f.name), "utf-8", id_map)

        assert result[32] == {0: 1}  # magic missile: MU at level 1
        assert result[1] == {1: 1}   # armor: Cleric at level 1
        assert result[131] == {2: 5} # backstab: Thief at level 5

    def test_constant_to_name(self):
        from genos.adapters.circlemud.skill_parser import _constant_to_name

        assert _constant_to_name("SPELL_MAGIC_MISSILE") == "magic missile"
        assert _constant_to_name("SKILL_BACKSTAB") == "backstab"

    def test_parse_han_spells(self):
        from genos.adapters.circlemud.skill_parser import _parse_han_spells

        text = textwrap.dedent("""\
        char *han_spells[] = {
          "unused",
          "armor_kor",
          "teleport_kor",
        };
        """)
        result = _parse_han_spells(text)
        assert result[0] == "unused"
        assert result[1] == "armor_kor"
        assert result[2] == "teleport_kor"


class TestSchemaExtensions:
    """Test new UIR schema dataclasses."""

    def test_social_defaults(self):
        s = Social()
        assert s.command == ""
        assert s.min_victim_position == 0
        assert s.flags == 0

    def test_help_entry_defaults(self):
        h = HelpEntry()
        assert h.keywords == []
        assert h.min_level == 0
        assert h.text == ""

    def test_skill_defaults(self):
        sk = Skill()
        assert sk.id == 0
        assert sk.class_levels == {}
        assert sk.extensions == {}

    def test_race_defaults(self):
        r = Race()
        assert r.id == 0
        assert r.stat_modifiers == {}
        assert r.allowed_classes == []

    def test_command_new_fields(self):
        c = Command()
        assert c.min_match == ""
        assert c.handler == ""
        assert c.subcmd == 0
        assert c.category == ""

    def test_uir_new_fields(self):
        uir = UIR()
        assert uir.socials == []
        assert uir.help_entries == []
        assert uir.skills == []
        assert uir.races == []


class TestDbGenerator:
    """Test that db_generator handles new tables."""

    def test_ddl_has_new_tables(self):
        from genos.compiler.db_generator import generate_ddl

        uir = UIR()
        buf = io.StringIO()
        generate_ddl(uir, buf)
        ddl = buf.getvalue()

        assert "CREATE TABLE IF NOT EXISTS socials" in ddl
        assert "CREATE TABLE IF NOT EXISTS help_entries" in ddl
        assert "CREATE TABLE IF NOT EXISTS skills" in ddl
        assert "CREATE TABLE IF NOT EXISTS races" in ddl

    def test_seed_socials(self):
        from genos.compiler.db_generator import generate_seed_data

        uir = UIR()
        uir.socials = [Social(command="wave", min_victim_position=0, flags=0,
                              no_arg_to_char="You wave.")]
        buf = io.StringIO()
        generate_seed_data(uir, buf)
        sql = buf.getvalue()

        assert "INSERT INTO socials" in sql
        assert "'wave'" in sql
        assert "You wave." in sql

    def test_seed_help(self):
        from genos.compiler.db_generator import generate_seed_data

        uir = UIR()
        uir.help_entries = [HelpEntry(keywords=["LOOK"], min_level=0,
                                      text="Look around.")]
        buf = io.StringIO()
        generate_seed_data(uir, buf)
        sql = buf.getvalue()

        assert "INSERT INTO help_entries" in sql
        assert "LOOK" in sql

    def test_seed_commands_removed(self):
        """Commands table was removed in v1.0 — commands are Lua-driven now."""
        from genos.compiler.db_generator import generate_seed_data

        uir = UIR()
        uir.commands = [Command(name="north", handler="do_move",
                                min_position=8)]
        buf = io.StringIO()
        generate_seed_data(uir, buf)
        sql = buf.getvalue()

        # Commands are no longer seeded as a separate table
        assert "INSERT INTO commands" not in sql

    def test_seed_skills(self):
        from genos.compiler.db_generator import generate_seed_data

        uir = UIR()
        uir.skills = [Skill(id=1, name="armor", spell_type="spell",
                            max_mana=30, min_mana=15)]
        buf = io.StringIO()
        generate_seed_data(uir, buf)
        sql = buf.getvalue()

        assert "INSERT INTO skills" in sql
        assert "'armor'" in sql

    def test_seed_races(self):
        from genos.compiler.db_generator import generate_seed_data

        uir = UIR()
        uir.races = [Race(id=0, name="Human", abbreviation="Hu")]
        buf = io.StringIO()
        generate_seed_data(uir, buf)
        sql = buf.getvalue()

        assert "INSERT INTO races" in sql
        assert "'Human'" in sql


# ══════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS (require actual data)
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not has_tbamud, reason="tbaMUD data not available")
class TestTbaMudIntegration:
    """Integration tests against actual tbaMUD data."""

    def test_parse_socials(self):
        from genos.adapters.circlemud.social_parser import parse_social_file

        socials = parse_social_file(TBAMUD_ROOT / "lib" / "misc" / "socials")
        assert len(socials) > 50
        # Check first social
        accuse = next((s for s in socials if s.command == "accuse"), None)
        assert accuse is not None
        assert accuse.flags == 5

    def test_parse_help(self):
        from genos.adapters.circlemud.help_parser import parse_help_dir

        entries = parse_help_dir(TBAMUD_ROOT / "lib" / "text" / "help")
        assert len(entries) > 10

    def test_parse_commands(self):
        from genos.adapters.circlemud.cmd_parser import parse_cmd_file

        cmds = parse_cmd_file(
            TBAMUD_ROOT / "src" / "interpreter.c",
            has_min_match=True,
        )
        assert len(cmds) > 100
        # Check that known commands exist
        north = next((c for c in cmds if c.name == "north"), None)
        assert north is not None
        assert north.handler == "do_move"
        assert north.min_match == "n"

    def test_parse_skills(self):
        from genos.adapters.circlemud.skill_parser import parse_skills

        skills = parse_skills(TBAMUD_ROOT / "src", has_spell_name=True)
        assert len(skills) > 30

        # Check known spell
        armor = next((s for s in skills if s.name == "armor"), None)
        assert armor is not None
        assert armor.id == 1
        assert armor.spell_type == "spell"
        assert armor.max_mana == 30

    def test_adapter_parse_full(self):
        from genos.adapters.circlemud.adapter import CircleMudAdapter

        adapter = CircleMudAdapter(TBAMUD_ROOT)
        uir = adapter.parse()

        assert len(uir.socials) > 50
        assert len(uir.commands) > 100
        assert len(uir.skills) > 30
        assert uir.migration_stats.total_socials == len(uir.socials)
        assert uir.migration_stats.total_commands == len(uir.commands)
        assert uir.migration_stats.total_skills == len(uir.skills)

    def test_adapter_analyze(self):
        from genos.adapters.circlemud.adapter import CircleMudAdapter

        adapter = CircleMudAdapter(TBAMUD_ROOT)
        report = adapter.analyze()

        assert report.social_count > 50
        assert report.command_count > 100
        assert report.skill_count > 30


@pytest.mark.skipif(not has_simoon, reason="Simoon data not available")
class TestSimoonIntegration:
    """Integration tests against actual Simoon data."""

    def test_parse_socials(self):
        from genos.adapters.circlemud.social_parser import parse_social_file

        socials = parse_social_file(
            SIMOON_ROOT / "lib" / "misc" / "socials",
            encoding="euc-kr",
        )
        assert len(socials) > 50

    def test_parse_help(self):
        from genos.adapters.simoon.help_parser import parse_help_dir

        entries = parse_help_dir(SIMOON_ROOT / "lib" / "text" / "help")
        assert len(entries) > 100

    def test_parse_commands(self):
        from genos.adapters.simoon.cmd_parser import parse_cmd_file

        cmds = parse_cmd_file(SIMOON_ROOT / "src" / "interpreter.c")
        assert len(cmds) > 50
        # Check an English command
        at = next((c for c in cmds if c.name == "at"), None)
        assert at is not None
        assert at.handler == "do_at"

    def test_parse_skills(self):
        from genos.adapters.circlemud.skill_parser import parse_skills

        skills = parse_skills(
            SIMOON_ROOT / "src", encoding="euc-kr", has_spell_name=False,
        )
        assert len(skills) > 30

    def test_adapter_parse_full(self):
        from genos.adapters.simoon.adapter import SimoonAdapter

        adapter = SimoonAdapter(SIMOON_ROOT)
        uir = adapter.parse()

        assert len(uir.socials) > 50
        assert len(uir.help_entries) > 100
        assert len(uir.commands) > 50
        assert len(uir.skills) > 30
        assert len(uir.races) == 5
        assert len(uir.character_classes) == 7

        # Check races
        human = next((r for r in uir.races if r.name == "Human"), None)
        assert human is not None
        assert human.stat_modifiers.get("charisma") == 3

        # Check stats
        assert uir.migration_stats.total_socials > 0
        assert uir.migration_stats.total_help_entries > 0
        assert uir.migration_stats.total_commands > 0
        assert uir.migration_stats.total_skills > 0
        assert uir.migration_stats.total_races == 5

    def test_adapter_analyze(self):
        from genos.adapters.simoon.adapter import SimoonAdapter

        adapter = SimoonAdapter(SIMOON_ROOT)
        report = adapter.analyze()

        assert report.social_count > 50
        assert report.help_count > 100
        assert report.command_count > 50
        assert report.race_count == 5

    def test_skills_have_korean_names(self):
        from genos.adapters.circlemud.skill_parser import parse_skills

        skills = parse_skills(
            SIMOON_ROOT / "src", encoding="euc-kr", has_spell_name=False,
        )
        korean_skills = [s for s in skills if s.extensions.get("korean_name")]
        assert len(korean_skills) > 10
