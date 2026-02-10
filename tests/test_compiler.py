"""Tests for the GenOS compiler (DB + Lua generators)."""

import io
import os

import pytest

from genos.adapters.circlemud.adapter import CircleMudAdapter
from genos.compiler.compiler import GenosCompiler
from genos.compiler.db_generator import generate_ddl, generate_seed_data
from genos.compiler.lua_generator import generate_combat_lua, generate_class_lua
from genos.uir.schema import (
    CharacterClass,
    CombatSystem,
    Exit,
    Item,
    Monster,
    DiceRoll,
    Room,
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


def test_compiler_writes_files(tmp_path):
    uir = _make_test_uir()
    compiler = GenosCompiler(uir, tmp_path)
    generated = compiler.compile()

    assert len(generated) >= 4  # schema.sql, seed.sql, combat.lua, classes.lua
    for fpath in generated:
        assert os.path.exists(fpath)


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
