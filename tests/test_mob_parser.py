"""Tests for the CircleMUD .mob parser."""

import os

import pytest

from genos.adapters.circlemud.mob_parser import parse_mob_file, parse_mob_text

TBAMUD_MOB = "/home/genos/workspace/tbamud/lib/world/mob/0.mob"


@pytest.fixture
def sample_mob_text():
    return """\
#1
Puff dragon fractal~
Puff~
Puff the Fractal Dragon is here, contemplating a higher reality.
~
   Is that some type of differential curve involving some strange, and unknown
calculus that she seems to be made out of?
~
516106 0 0 0 2128 0 0 0 1000 E
34 9 -10 6d6+340 5d5+5
340 115600
8 8 2
BareHandAttack: 12
E
T 95
#5
jack russell~
Jack Russell~
Jack Russell hunts with his dogs.
~
   The Jack Russell takes its name from the Reverend John Russell.
~
72 0 0 0 0 0 0 0 0 E
3 19 8 0d0+30 1d2+0
30 900
8 8 1
E
$~
"""


def test_parse_puff(sample_mob_text):
    mobs = parse_mob_text(sample_mob_text)
    assert len(mobs) == 2

    puff = mobs[0]
    assert puff.vnum == 1
    assert puff.keywords == "Puff dragon fractal"
    assert puff.short_description == "Puff"
    assert "Fractal Dragon" in puff.long_description
    assert puff.level == 34
    assert puff.hitroll == 9
    assert puff.armor_class == -10
    assert puff.hp_dice.num == 6
    assert puff.hp_dice.size == 6
    assert puff.hp_dice.bonus == 340
    assert puff.damage_dice.num == 5
    assert puff.damage_dice.size == 5
    assert puff.damage_dice.bonus == 5
    assert puff.gold == 340
    assert puff.experience == 115600
    assert puff.sex == 2  # female
    assert puff.bare_hand_attack == 12  # blast
    assert 95 in puff.trigger_vnums


def test_parse_jack(sample_mob_text):
    mobs = parse_mob_text(sample_mob_text)
    jack = mobs[1]
    assert jack.vnum == 5
    assert jack.level == 3
    assert jack.hp_dice.bonus == 30
    assert jack.sex == 1  # male


@pytest.mark.skipif(
    not os.path.exists(TBAMUD_MOB),
    reason="tbaMUD data not available",
)
def test_parse_real_mob_file():
    mobs = parse_mob_file(TBAMUD_MOB)
    assert len(mobs) > 0

    vnums = {m.vnum for m in mobs}
    assert 1 in vnums  # Puff
    assert 0 in vnums  # trigger mob

    puff = next(m for m in mobs if m.vnum == 1)
    assert puff.level == 34
