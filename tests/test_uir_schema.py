"""Tests for UIR schema dataclasses."""

from genos.uir.schema import (
    CharacterClass,
    CombatSystem,
    DiceRoll,
    Exit,
    ExtraDescription,
    GameMetadata,
    Item,
    ItemAffect,
    MigrationStats,
    Monster,
    Quest,
    Room,
    Shop,
    SourceMudInfo,
    Trigger,
    UIR,
    Zone,
    ZoneResetCommand,
)


def test_uir_default():
    uir = UIR()
    assert uir.uir_version == "1.0"
    assert uir.rooms == []
    assert uir.items == []
    assert uir.monsters == []


def test_room_creation():
    room = Room(vnum=0, name="The Void", sector_type=1)
    assert room.vnum == 0
    assert room.name == "The Void"
    assert room.exits == []
    assert room.trigger_vnums == []


def test_exit_creation():
    exit_ = Exit(direction=0, destination=100, door_flags=3, key_vnum=50)
    assert exit_.direction == 0
    assert exit_.destination == 100
    assert exit_.door_flags == 3


def test_item_defaults():
    item = Item(vnum=1)
    assert item.values == [0, 0, 0, 0]
    assert item.affects == []
    assert item.extra_descriptions == []


def test_monster_dice_roll():
    d = DiceRoll(num=6, size=6, bonus=340)
    assert str(d) == "6d6+340"


def test_zone_with_commands():
    z = Zone(vnum=0, name="Test Zone")
    z.reset_commands.append(
        ZoneResetCommand(command="M", if_flag=0, arg1=1, arg2=1, arg3=5)
    )
    assert len(z.reset_commands) == 1
    assert z.reset_commands[0].command == "M"


def test_character_class():
    cls = CharacterClass(
        id=3, name="Warrior", abbreviation="Wa",
        extensions={"base_thac0": 20, "thac0_gain": 1.0},
    )
    assert cls.extensions["base_thac0"] == 20
    assert cls.extensions["thac0_gain"] == 1.0


def test_combat_system_defaults():
    cs = CombatSystem()
    assert cs.type == ""
    assert cs.damage_types == []
    assert cs.parameters == {}


def test_trigger():
    t = Trigger(vnum=1, name="Test", attach_type=0, script="say hello")
    assert t.attach_type == 0


def test_quest():
    q = Quest(vnum=100, name="Kill Mice")
    assert q.target_vnum == -1


def test_shop():
    s = Shop(vnum=0, keeper_vnum=97, profit_buy=1.2, profit_sell=0.9)
    assert s.selling_items == []
