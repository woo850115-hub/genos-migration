"""Tests for the CircleMUD .zon parser."""

import os

import pytest

from genos.adapters.circlemud.zon_parser import parse_zon_file, parse_zon_text

TBAMUD_ZON = "/home/genos/workspace/tbamud/lib/world/zon/0.zon"


@pytest.fixture
def sample_zon_text():
    return """\
#0
Rumble~
The Builder Academy Zone~
0 99 30 2 d 0 0 0 -1 -1
M 0 34 1 8 	(Chuck Norris)
M 0 29 2 7 	(Epictetus)
D 0 20 0 2 	(Advanced Trigedit Example)
O 0 1228 99 88 	(a advertising bulletin board)
M 0 1 1 1 	(Puff)
S
$~
"""


def test_parse_zone(sample_zon_text):
    zones = parse_zon_text(sample_zon_text)
    assert len(zones) == 1

    z = zones[0]
    assert z.vnum == 0
    assert z.name == "Rumble"
    assert z.bot == 0
    assert z.top == 99
    assert z.lifespan == 30
    assert z.reset_mode == 2

    # Reset commands
    assert len(z.reset_commands) == 5
    assert z.reset_commands[0].command == "M"
    assert z.reset_commands[0].arg1 == 34  # mob vnum
    assert z.reset_commands[0].arg3 == 8   # room vnum

    assert z.reset_commands[2].command == "D"
    assert z.reset_commands[3].command == "O"
    assert z.reset_commands[4].command == "M"


def test_comments_handled():
    text = """\
#1
Test~
Test Zone~
100 199 30 2 0 0 0 0 -1 -1
* This is a comment
M 0 100 1 100 	(test mob)
S
$~
"""
    zones = parse_zon_text(text)
    assert len(zones) == 1
    assert len(zones[0].reset_commands) == 1


@pytest.mark.skipif(
    not os.path.exists(TBAMUD_ZON),
    reason="tbaMUD data not available",
)
def test_parse_real_zon_file():
    zones = parse_zon_file(TBAMUD_ZON)
    assert len(zones) >= 1
    z0 = zones[0]
    assert z0.vnum == 0
    assert z0.top == 99
    assert len(z0.reset_commands) > 0
