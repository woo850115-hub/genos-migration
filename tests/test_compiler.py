"""Tests for the GenOS compiler (DB + Lua generators)."""

import io
import os

import pytest

from genos.adapters.circlemud.adapter import CircleMudAdapter
from genos.compiler.compiler import GenosCompiler
from genos.compiler.db_generator import generate_ddl, generate_seed_data
from genos.compiler.lua_generator import (
    generate_combat_lua,
    generate_class_lua,
    generate_level_titles_lua,
    generate_races_lua,
    generate_skills_lua,
    generate_socials_lua,
)
from genos.uir.schema import (
    CharacterClass,
    CombatSystem,
    Exit,
    Item,
    LevelTitle,
    Monster,
    DiceRoll,
    Race,
    Room,
    Skill,
    Social,
    UIR,
    Zone,
    ZoneResetCommand,
)

TBAMUD_ROOT = "/home/genos/workspace/tbamud"


def _make_test_uir() -> UIR:
    uir = UIR()
    uir.rooms = [
        Room(vnum=0, name="The Void", description="Dark void.",
             exits=[Exit(direction=4, destination=1)]),
        Room(vnum=1, name="Limbo", description="Floating."),
    ]
    uir.items = [
        Item(vnum=1, keywords="sword", short_description="a sword",
             item_type=5, weight=10, cost=500),
    ]
    uir.monsters = [
        Monster(vnum=1, keywords="puff dragon", short_description="Puff",
                level=34, hp_dice=DiceRoll(6, 6, 340)),
    ]
    uir.zones = [
        Zone(vnum=0, name="Test", bot=0, top=99,
             reset_commands=[ZoneResetCommand(command="M", arg1=1, arg2=1, arg3=0)]),
    ]
    uir.character_classes = [
        CharacterClass(id=0, name="Magic User", abbreviation="Mu",
                        extensions={"base_thac0": 20, "thac0_gain": 0.66}),
        CharacterClass(id=3, name="Warrior", abbreviation="Wa",
                        hp_gain_min=10, hp_gain_max=15,
                        extensions={"base_thac0": 20, "thac0_gain": 1.0}),
    ]
    uir.combat_system = CombatSystem(
        type="thac0",
        parameters={"base_thac0": 20, "ac_range": [-10, 10]},
        damage_types=[
            "hit", "sting", "whip", "slash", "bite", "bludgeon",
            "crush", "pound", "claw", "maul", "thrash", "pierce",
            "blast", "punch", "stab",
        ],
    )
    uir.skills = [
        Skill(id=1, name="magic missile", spell_type="spell",
              max_mana=25, min_mana=10, mana_change=-3, min_position=8,
              targets=2, violent=True, routines=1,
              wearoff_msg="", class_levels={0: 1, 3: 10},
              extensions={"korean_name": "마법화살"}),
        Skill(id=2, name="cure light", spell_type="spell",
              max_mana=30, min_mana=15, mana_change=-2, min_position=8,
              targets=1, violent=False, routines=2,
              wearoff_msg="You feel less protected.",
              class_levels={1: 1}),
    ]
    uir.races = [
        Race(id=0, name="Human", abbreviation="Hum",
             stat_modifiers={"str": 0, "int": 0, "wis": 0},
             allowed_classes=[0, 1, 2, 3]),
        Race(id=1, name="Elf", abbreviation="Elf",
             stat_modifiers={"str": -1, "int": 1, "dex": 1},
             allowed_classes=[0, 2],
             extensions={"infravision": True}),
    ]
    uir.socials = [
        Social(command="smile", min_victim_position=0,
               no_arg_to_char="You smile happily.",
               no_arg_to_room="$n smiles happily.",
               found_to_char="You smile at $N.",
               found_to_room="$n smiles at $N.",
               found_to_victim="$n smiles at you.",
               not_found="Smile at whom?",
               self_to_char="You smile to yourself.",
               self_to_room="$n smiles at $mself."),
        Social(command="wave", min_victim_position=0,
               no_arg_to_char="You wave.",
               no_arg_to_room="$n waves."),
    ]
    uir.level_titles = [
        LevelTitle(class_id=0, level=1, gender="male", title="Apprentice"),
        LevelTitle(class_id=0, level=1, gender="female", title="Apprentice"),
        LevelTitle(class_id=0, level=10, gender="male", title="Conjurer"),
        LevelTitle(class_id=0, level=10, gender="female", title="Witchess"),
        LevelTitle(class_id=3, level=1, gender="male", title="Swordpupil"),
    ]
    return uir


def test_generate_ddl():
    uir = _make_test_uir()
    out = io.StringIO()
    generate_ddl(uir, out)
    sql = out.getvalue()
    assert "CREATE TABLE" in sql
    assert "rooms" in sql
    assert "items" in sql
    assert "monsters" in sql
    assert "zones" in sql
    assert "triggers" in sql


def test_generate_seed_data():
    uir = _make_test_uir()
    out = io.StringIO()
    generate_seed_data(uir, out)
    sql = out.getvalue()
    assert "INSERT INTO rooms" in sql
    assert "The Void" in sql
    assert "INSERT INTO items" in sql
    assert "INSERT INTO monsters" in sql
    assert "INSERT INTO classes" in sql
    # Verify zone reset_commands use "command" key (not "cmd") for engine compatibility
    assert '"command": "M"' in sql
    assert '"cmd"' not in sql


def test_generate_combat_lua():
    uir = _make_test_uir()
    out = io.StringIO()
    generate_combat_lua(uir, out)
    lua = out.getvalue()
    assert "Combat.calculate_hit" in lua
    assert "Combat.roll_damage" in lua
    assert "Combat.get_thac0" in lua
    assert "Magic User" in lua


def test_generate_class_lua():
    uir = _make_test_uir()
    out = io.StringIO()
    generate_class_lua(uir, out)
    lua = out.getvalue()
    assert "Classes.level_up" in lua
    assert "Warrior" in lua
    assert "hp_gain" in lua


def test_generate_skills_lua():
    uir = _make_test_uir()
    out = io.StringIO()
    generate_skills_lua(uir, out)
    lua = out.getvalue()
    assert "Skills[1]" in lua
    assert "Skills[2]" in lua
    assert '"magic missile"' in lua
    assert '"cure light"' in lua
    assert "class_levels" in lua
    assert "[0]=1" in lua  # magic user at level 1
    assert "[3]=10" in lua  # warrior at level 10
    assert "violent = true" in lua
    assert "violent = false" in lua
    assert '"마법화살"' in lua  # korean_name
    assert "Skills.get_by_name" in lua
    assert "Skills.get_class_level" in lua
    assert 'wearoff = "You feel less protected."' in lua


def test_generate_races_lua():
    uir = _make_test_uir()
    out = io.StringIO()
    generate_races_lua(uir, out)
    lua = out.getvalue()
    assert "Races[0]" in lua
    assert "Races[1]" in lua
    assert '"Human"' in lua
    assert '"Elf"' in lua
    assert "stat_mods" in lua
    assert "str=0" in lua
    assert "str=-1" in lua
    assert "allowed_classes" in lua
    assert "infravision = true" in lua


def test_generate_socials_lua():
    uir = _make_test_uir()
    out = io.StringIO()
    generate_socials_lua(uir, out)
    lua = out.getvalue()
    assert 'Socials["smile"]' in lua
    assert 'Socials["wave"]' in lua
    assert "no_arg_char" in lua
    assert "no_arg_room" in lua
    assert "found_char" in lua
    assert "found_victim" in lua
    assert "not_found" in lua
    assert "self_char" in lua
    assert "self_room" in lua
    assert "return Socials" in lua


def test_generate_level_titles_lua():
    uir = _make_test_uir()
    out = io.StringIO()
    generate_level_titles_lua(uir, out)
    lua = out.getvalue()
    assert "LevelTitles[0]" in lua
    assert "LevelTitles[3]" in lua
    assert "male" in lua
    assert "female" in lua
    assert '"Apprentice"' in lua
    assert '"Conjurer"' in lua
    assert '"Witchess"' in lua
    assert '"Swordpupil"' in lua
    assert "LevelTitles.get_title" in lua


def test_compiler_writes_files(tmp_path):
    uir = _make_test_uir()
    compiler = GenosCompiler(uir, tmp_path)
    generated = compiler.compile()

    # schema.sql, seed.sql, combat.lua, classes.lua, korean_nlp.lua, korean_commands.lua
    # + skills.lua, races.lua, socials.lua, level_titles.lua = 10
    assert len(generated) >= 10
    for fpath in generated:
        assert os.path.exists(fpath)

    # Verify new Lua files exist
    lua_dir = tmp_path / "lua"
    assert (lua_dir / "skills.lua").exists()
    assert (lua_dir / "races.lua").exists()
    assert (lua_dir / "socials.lua").exists()
    assert (lua_dir / "level_titles.lua").exists()


@pytest.mark.skipif(
    not os.path.exists(TBAMUD_ROOT),
    reason="tbaMUD source not available",
)
def test_full_pipeline(tmp_path):
    """Full integration: parse tbaMUD → compile to SQL + Lua."""
    adapter = CircleMudAdapter(TBAMUD_ROOT)
    uir = adapter.parse()

    compiler = GenosCompiler(uir, tmp_path)
    generated = compiler.compile()

    # Should generate all expected files
    assert len(generated) >= 5  # schema, seed, combat, classes, triggers

    # Check SQL has data
    seed_path = tmp_path / "sql" / "seed_data.sql"
    seed_sql = seed_path.read_text()
    assert "INSERT INTO rooms" in seed_sql
    assert "INSERT INTO monsters" in seed_sql

    # Check Lua is valid
    combat_path = tmp_path / "lua" / "combat.lua"
    combat_lua = combat_path.read_text()
    assert "function" in combat_lua
