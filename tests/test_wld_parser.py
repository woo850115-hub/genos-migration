"""Tests for the CircleMUD .wld parser using actual tbaMUD data."""

import os

import pytest

from genos.adapters.circlemud.wld_parser import parse_wld_file, parse_wld_text

TBAMUD_WLD = "/home/genos/workspace/tbamud/lib/world/wld/0.wld"


@pytest.fixture
def sample_wld_text():
    return """\
#0
The Void~
   You don't think that you are not floating in nothing.
~
0 8 0 0 0 1
D4
~
~
0 0 100
S
T 1200
#1
Limbo~
   You are floating in a formless void.
~
0 8 0 0 0 1
D5
A strange portal in the floor is the only exit.
~
~
0 0 100
S
$~
"""


def test_parse_basic(sample_wld_text):
    rooms = parse_wld_text(sample_wld_text)
    assert len(rooms) == 2

    void = rooms[0]
    assert void.vnum == 0
    assert void.name == "The Void"
    assert "floating" in void.description
    assert void.sector_type == 0
    assert 3 in void.room_flags  # bit 3 from flag value 8

    # Exit
    assert len(void.exits) == 1
    assert void.exits[0].direction == 4  # up
    assert void.exits[0].destination == 100

    # Trigger
    assert void.trigger_vnums == [1200]


def test_parse_limbo(sample_wld_text):
    rooms = parse_wld_text(sample_wld_text)
    limbo = rooms[1]
    assert limbo.vnum == 1
    assert limbo.name == "Limbo"
    assert len(limbo.exits) == 1
    assert limbo.exits[0].direction == 5  # down
    assert limbo.exits[0].description == "A strange portal in the floor is the only exit."


@pytest.mark.skipif(
    not os.path.exists(TBAMUD_WLD),
    reason="tbaMUD data not available",
)
def test_parse_real_wld_file():
    rooms = parse_wld_file(TBAMUD_WLD)
    assert len(rooms) > 0

    # Check specific known rooms
    vnums = {r.vnum for r in rooms}
    assert 0 in vnums  # The Void
    assert 1 in vnums  # Limbo
    assert 2 in vnums  # Welcome
    assert 99 in vnums  # TBA Cafe 99

    # Room 20 has a door with keyword "gateway"
    room20 = next(r for r in rooms if r.vnum == 20)
    door_exits = [e for e in room20.exits if e.keyword]
    assert len(door_exits) >= 1
    assert "gateway" in door_exits[0].keyword

    # Room 99 has extra descriptions
    room99 = next(r for r in rooms if r.vnum == 99)
    assert len(room99.extra_descriptions) >= 1


def test_parse_extra_descriptions():
    text = """\
#90
Test Room~
   A test room.
~
0 8 0 0 0 0
E
drain floor~
   The metal drain is covered.
~
S
$~
"""
    rooms = parse_wld_text(text)
    assert len(rooms) == 1
    assert len(rooms[0].extra_descriptions) == 1
    assert "drain" in rooms[0].extra_descriptions[0].keywords


def test_parse_multiple_triggers():
    text = """\
#91
Cell~
   A cell.
~
0 8 0 0 0 0
S
T 171
T 172
$~
"""
    rooms = parse_wld_text(text)
    assert len(rooms) == 1
    assert rooms[0].trigger_vnums == [171, 172]
