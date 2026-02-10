"""Tests for the CircleMUD .obj parser."""

import os

import pytest

from genos.adapters.circlemud.obj_parser import parse_obj_file, parse_obj_text

TBAMUD_OBJ = "/home/genos/workspace/tbamud/lib/world/obj/0.obj"


@pytest.fixture
def sample_obj_text():
    return """\
#1
wings~
a pair of wings~
A pair of wings is sitting here.~
~
9 0 0 0 0 ae 0 0 0 0 0 0 0
6 0 0 0
1 1 0 0 0
#4
emails listing~
an email listing of the gods~
The email listing of the gods is pinned against the wall.~
~
12 0 0 0 0 a 0 0 0 0 0 0 0
0 0 0 0
1 1 0 30 0
E
emails listing~
   HELP CONTACT
~
$~
"""


def test_parse_basic(sample_obj_text):
    items = parse_obj_text(sample_obj_text)
    assert len(items) == 2

    wings = items[0]
    assert wings.vnum == 1
    assert wings.keywords == "wings"
    assert wings.short_description == "a pair of wings"
    assert wings.item_type == 9  # ITEM_ARMOR
    assert wings.values == [6, 0, 0, 0]
    assert wings.weight == 1
    assert wings.cost == 1


def test_parse_extra_desc(sample_obj_text):
    items = parse_obj_text(sample_obj_text)
    emails = items[1]
    assert emails.vnum == 4
    assert emails.item_type == 12  # ITEM_OTHER
    assert len(emails.extra_descriptions) == 1
    assert "emails" in emails.extra_descriptions[0].keywords
    assert emails.min_level == 0  # 5th field in weight/cost/rent line


def test_parse_wear_flags_128bit():
    """Test tbaMUD 128-bit format (13 fields): type ef0 ef1 ef2 ef3 wf0 wf1 wf2 wf3 af0 af1 af2 af3"""
    text = """\
#10
sword~
a sword~
A sword lies here.~
~
5 0 0 0 0 an 0 0 0 0 0 0 0
0 3 12 4
10 500 100 0 0
A
18 2
$~
"""
    items = parse_obj_text(text)
    assert len(items) == 1
    sword = items[0]
    assert sword.item_type == 5  # ITEM_WEAPON
    # wear_flags field at index 5 = 'an' → a=bit0(TAKE), n=bit13(WIELD)
    assert 0 in sword.wear_flags   # TAKE
    assert 13 in sword.wear_flags  # WIELD
    assert len(sword.affects) == 1
    assert sword.affects[0].location == 18  # APPLY_HITROLL
    assert sword.affects[0].modifier == 2


def test_parse_wear_flags_old():
    """Test old 3-field format: type extra_flags wear_flags."""
    text = """\
#20
shield~
a shield~
A shield lies here.~
~
9 0 aj
0 5 0 0
15 200 50
$~
"""
    items = parse_obj_text(text)
    assert len(items) == 1
    shield = items[0]
    assert shield.item_type == 9  # ITEM_ARMOR
    # 'aj' = a(bit0=TAKE) + j(bit9=SHIELD)
    assert 0 in shield.wear_flags
    assert 9 in shield.wear_flags


@pytest.mark.skipif(
    not os.path.exists(TBAMUD_OBJ),
    reason="tbaMUD data not available",
)
def test_parse_real_obj_file():
    items = parse_obj_file(TBAMUD_OBJ)
    assert len(items) > 0

    vnums = {i.vnum for i in items}
    assert 1 in vnums  # wings
    assert 4 in vnums  # emails listing
