"""Tests for the CircleMUD .trg (DG Script) parser."""

import os

import pytest

from genos.adapters.circlemud.trg_parser import parse_trg_file, parse_trg_text

TBAMUD_TRG = "/home/genos/workspace/tbamud/lib/world/trg/0.trg"


@pytest.fixture
def sample_trg_text():
    return """\
#1
Mob Tutorial Example Quest Offer - M14~
0 g 100
~
* By Rumble of The Builder Academy
if %actor.is_pc% && %direction% == south
  wait 1 sec
  say Can you help me, %actor.name%?
  wait 1 sec
  say An ogre has something of mine.
end
~
#2
Mob Tutorial Example Kill Ogre - 16~
0 f 100
~
say You got the best of me, %actor.name%. But I'll be back.
%load% obj 1
%load% mob %self.vnum%
~
$~
"""


def test_parse_triggers(sample_trg_text):
    triggers = parse_trg_text(sample_trg_text)
    assert len(triggers) == 2

    t1 = triggers[0]
    assert t1.vnum == 1
    assert t1.name == "Mob Tutorial Example Quest Offer - M14"
    assert t1.attach_type == 0  # MOB
    assert t1.numeric_arg == 100
    assert "actor.is_pc" in t1.script
    assert "say Can you help me" in t1.script


def test_trigger_script_content(sample_trg_text):
    triggers = parse_trg_text(sample_trg_text)
    t2 = triggers[1]
    assert t2.vnum == 2
    assert "%load% obj 1" in t2.script


@pytest.mark.skipif(
    not os.path.exists(TBAMUD_TRG),
    reason="tbaMUD data not available",
)
def test_parse_real_trg_file():
    triggers = parse_trg_file(TBAMUD_TRG)
    assert len(triggers) > 0

    # Trigger 0 should exist (non-attachable)
    vnums = {t.vnum for t in triggers}
    assert 0 in vnums
    assert 1 in vnums
