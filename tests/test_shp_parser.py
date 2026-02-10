"""Tests for the CircleMUD .shp parser."""

import os

import pytest

from genos.adapters.circlemud.shp_parser import parse_shp_file, parse_shp_text

TBAMUD_SHP = "/home/genos/workspace/tbamud/lib/world/shp/0.shp"


@pytest.fixture
def sample_shp_text():
    return """\
CircleMUD v3.0 Shop File~
#99~
91
92
97
90
-1
1.00
1.00
-1
%s Sorry, I don't stock that item.~
%s You don't seem to have that.~
%s I don't trade in such items.~
%s I can't afford that!~
%s You are too poor!~
%s That'll be %d coins, thanks.~
%s I'll give you %d coins for that.~
0
0
97
0
99
-1
0
28
0
0
$~
"""


def test_parse_shop(sample_shp_text):
    shops = parse_shp_text(sample_shp_text)
    assert len(shops) == 1

    s = shops[0]
    assert s.vnum == 99
    assert s.selling_items == [91, 92, 97, 90]
    assert s.profit_buy == 1.00
    assert s.profit_sell == 1.00
    assert s.keeper_vnum == 97
    assert s.shop_room == 99
    assert "Sorry" in s.no_such_item1
    assert "coins, thanks" in s.message_buy


@pytest.mark.skipif(
    not os.path.exists(TBAMUD_SHP),
    reason="tbaMUD data not available",
)
def test_parse_real_shp_file():
    shops = parse_shp_file(TBAMUD_SHP)
    assert len(shops) > 0

    # Shop vnum 99 is the cafe
    vnums = {s.vnum for s in shops}
    assert 99 in vnums
