"""Tests for SimoonAdapter and Simoon parsers."""

import os

import pytest

from genos.adapters.detector import detect_mud_type
from genos.adapters.simoon.adapter import SimoonAdapter
from genos.adapters.simoon.mob_parser import parse_mob_text
from genos.adapters.simoon.obj_parser import parse_obj_text
from genos.adapters.simoon.qst_parser import parse_qst_text
from genos.adapters.simoon.wld_parser import parse_wld_text
from genos.adapters.simoon.zon_parser import parse_zon_text
from genos.uir.validator import validate_uir

SIMOON_ROOT = "/home/genos/workspace/simoon"
TBAMUD_ROOT = "/home/genos/workspace/tbamud"


# ── Unit Tests (no real data required) ──────────────────────────────


class TestWldParser:
    @pytest.fixture
    def sample_wld(self):
        return """\
#100
테스트 방~
아름다운 방입니다.
여기가 바로 시작점이에요.
~
1 537100436 0
D0
~
~
0 -1 18600
D1
북쪽 설명~
문~
1 104 101
S
#101
두번째 방~
간단한 방입니다.
~
1 156 2
E
낙서~
벽에 낙서가 있습니다.
~
S
$~
"""

    def test_parse_basic(self, sample_wld):
        rooms = parse_wld_text(sample_wld)
        assert len(rooms) == 2

        r = rooms[0]
        assert r.vnum == 100
        assert "테스트 방" in r.name
        assert "아름다운" in r.description
        assert r.zone_number == 1
        assert r.sector_type == 0
        assert len(r.exits) == 2
        assert r.exits[0].direction == 0
        assert r.exits[0].destination == 18600
        assert r.exits[1].direction == 1
        assert r.exits[1].door_flags == 1
        assert r.exits[1].key_vnum == 104
        assert r.exits[1].destination == 101

    def test_parse_flags(self, sample_wld):
        rooms = parse_wld_text(sample_wld)
        r = rooms[0]
        # 537100436 = flags, should have some bits set
        assert len(r.room_flags) > 0

    def test_parse_extra_desc(self, sample_wld):
        rooms = parse_wld_text(sample_wld)
        r = rooms[1]
        assert r.vnum == 101
        assert len(r.extra_descriptions) == 1
        assert "낙서" in r.extra_descriptions[0].keywords
        assert "벽에" in r.extra_descriptions[0].description


class TestMobParser:
    @pytest.fixture
    def sample_mob(self):
        return """\
#200
도우미~
도우미~
아주 키가 작은 도우미가 당신을 보며 활짝 웃고 있습니다.
~
특별한점을 찾아볼수 없습니다.
~
10 0 1000 E
3 0 10 4d0+87 3d15+1
2163 0
8 8 2
Str: 18
StrAdd: 100
Dex: 18
Int: 18
Wis: 18
Con: 18
Cha: 18
E
#201
나레이터~
나레이터~
나레이터가 춤을 추고 있습니다.
~
특별한점을 찾아볼수 없습니다.
~
16393 0 1000 E
5 -10 10 4d0+300 3d10+1
2240 120
8 8 2
E
$
"""

    def test_parse_basic(self, sample_mob):
        mobs = parse_mob_text(sample_mob)
        assert len(mobs) == 2

        m = mobs[0]
        assert m.vnum == 200
        assert "도우미" in m.keywords
        assert m.alignment == 1000
        assert m.level == 3
        assert m.hitroll == 0
        assert m.armor_class == 10
        assert m.hp_dice.num == 4
        assert m.hp_dice.size == 0
        assert m.hp_dice.bonus == 87
        assert m.damage_dice.num == 3
        assert m.damage_dice.size == 15
        assert m.damage_dice.bonus == 1
        assert m.gold == 2163
        assert m.experience == 0
        assert m.sex == 2

    def test_parse_extensions(self, sample_mob):
        mobs = parse_mob_text(sample_mob)
        m = mobs[0]
        assert m.extensions["Str"] == 18
        assert m.extensions["StrAdd"] == 100
        assert m.extensions["Dex"] == 18
        assert m.extensions["Int"] == 18
        assert m.extensions["Wis"] == 18
        assert m.extensions["Con"] == 18
        assert m.extensions["Cha"] == 18

    def test_parse_no_extensions(self, sample_mob):
        mobs = parse_mob_text(sample_mob)
        m = mobs[1]
        assert m.vnum == 201
        assert len(m.extensions) == 0
        assert m.level == 5

    def test_parse_bare_hand_attack(self):
        text = """\
#0
도적~
도적~
도적이 당신을 노려보고 있습니다.
~
특별한점을 찾아볼수 없습니다.
~
136314888 0 -250 E
100 -5 0 4d6+2534 3d8+28
29400 10200
8 8 1
BareHandAttack: 1
E
$
"""
        mobs = parse_mob_text(text)
        assert len(mobs) == 1
        assert mobs[0].bare_hand_attack == 1

    def test_parse_with_all_extensions(self):
        text = """\
#1
박물 관장~
박물관장~
박물관의 관장이 박물관 내부를 이곳저곳 둘러 보고 있습니다.
~
나이가 지긋한 동네 옆집 아저씨 같은 인상이 풍깁니다.
~
33554441 0 -300 E
300 -80 20 3d20+8385 3d8+100
116100 30200
8 8 1
BareHandAttack: 13
Str: 9
Dex: 8
Int: 6
Wis: 4
Con: 10
Cha: 3
Att1: 100
Att2: 100
Att3: 100
E
$
"""
        mobs = parse_mob_text(text)
        assert len(mobs) == 1
        m = mobs[0]
        assert m.bare_hand_attack == 13
        assert m.extensions["Str"] == 9
        assert m.extensions["Att1"] == 100
        assert m.extensions["Att2"] == 100
        assert m.extensions["Att3"] == 100


class TestObjParser:
    @pytest.fixture
    def sample_obj(self):
        return """\
#100
콜라코카~
코카콜라~
아주 시원하고 감미로워 보이는 코카콜라입니다.~
물방울이 뚝!뚝! 떨어집니다.
~
17 21 1
16 0 1 0
10 1000 0
#119
비검(파워업)~
비검(파워업)~
비검(파워업)때문에 당신은 무적이 됩니다..~
음냐....
~
5 1073741836 8193
0 0 20 0
1 0 1
A
1 10
A
2 10
$~
"""

    def test_parse_basic(self, sample_obj):
        items = parse_obj_text(sample_obj)
        assert len(items) == 2

        i = items[0]
        assert i.vnum == 100
        assert "콜라" in i.keywords
        assert i.item_type == 17  # drinkcon
        assert i.weight == 10
        assert i.cost == 1000
        assert i.values[0] == 16

    def test_parse_flags(self, sample_obj):
        items = parse_obj_text(sample_obj)
        i = items[0]
        # extra_flags = 21 = 0b10101 → bits 0, 2, 4
        assert 0 in i.extra_flags
        assert 2 in i.extra_flags
        assert 4 in i.extra_flags
        # wear_flags = 1 → bit 0
        assert 0 in i.wear_flags

    def test_parse_affects(self, sample_obj):
        items = parse_obj_text(sample_obj)
        i = items[1]
        assert i.vnum == 119
        assert len(i.affects) == 2
        assert i.affects[0].location == 1
        assert i.affects[0].modifier == 10
        assert i.affects[1].location == 2

    def test_parse_extra_desc(self):
        text = """\
#105
민들레~
민들레~
민들레가 피어 있습니다.~
~
13 0 0
0 0 0 0
1000 0 0
E
민들레~
사람들의 발길에 짖밟혀도 끈질기게 자라나고 있는 민들레입니다.
~
$~
"""
        items = parse_obj_text(text)
        assert len(items) == 1
        assert len(items[0].extra_descriptions) == 1
        assert "민들레" in items[0].extra_descriptions[0].keywords


class TestZonParser:
    @pytest.fixture
    def sample_zon(self):
        return """\
#1
평화주의자~
치킨~
199 30 2
O 0 702 3 137 \t(전투식량)
M 0 116 5 111 \t(사향노루)
M 0 112 3 120 \t(애기 호랑이)
G 1 110 100 -1 \t(열목어 알)
E 1 108 100 16 \t(K2 소총)
S
$
"""

    def test_parse_basic(self, sample_zon):
        zones = parse_zon_text(sample_zon)
        assert len(zones) == 1

        z = zones[0]
        assert z.vnum == 1
        assert "평화주의자" in z.name
        assert z.builders == "치킨"
        assert z.top == 199
        assert z.lifespan == 30
        assert z.reset_mode == 2
        assert z.bot == 100  # vnum * 100

    def test_parse_reset_commands(self, sample_zon):
        zones = parse_zon_text(sample_zon)
        z = zones[0]
        assert len(z.reset_commands) == 5

        assert z.reset_commands[0].command == "O"
        assert z.reset_commands[0].arg1 == 702
        assert z.reset_commands[1].command == "M"
        assert z.reset_commands[1].arg1 == 116
        assert z.reset_commands[1].arg3 == 111
        assert z.reset_commands[3].command == "G"
        assert z.reset_commands[4].command == "E"

    def test_parse_comments(self, sample_zon):
        zones = parse_zon_text(sample_zon)
        z = zones[0]
        assert "(전투식량)" in z.reset_commands[0].comment


class TestQstParser:
    @pytest.fixture
    def sample_qst(self):
        return """\
#1
칼슈타인을 찾아라~
칼슈타인을 찾아라~
칼슈타인을 찾아 없애 주시오..
~
임무수행을 완수 해서 당신은 경험치를 얻었습니다.
~
3 18622 0 20190 100000 -1 20
0 0 0 0
S
#2
잠자리를 찾아라~
과수원 어딘가에 있을 잠자리를 찾아 주세요..~
과수원을 통과하세요..
~
임무완수를 축하 드립니다..
~
2 0 0 27 10000 -1 0
0 0 0 0
S
$~
"""

    def test_parse_basic(self, sample_qst):
        quests = parse_qst_text(sample_qst)
        assert len(quests) == 2

        q = quests[0]
        assert q.vnum == 1
        assert "칼슈타인" in q.name
        assert "칼슈타인" in q.keywords
        assert "없애" in q.description
        assert "경험치" in q.completion_message
        assert q.quest_type == 3
        assert q.mob_vnum == 18622
        assert q.target_vnum == 20190
        assert q.reward_exp == 100000
        assert q.next_quest == -1
        assert q.min_level == 20

    def test_parse_values(self, sample_qst):
        quests = parse_qst_text(sample_qst)
        q = quests[0]
        assert q.value0 == 0
        assert q.value1 == 0
        assert q.value2 == 0
        assert q.value3 == 0


# ── Integration Tests (real data) ──────────────────────────────────


@pytest.mark.skipif(
    not os.path.exists(SIMOON_ROOT),
    reason="Simoon source not available",
)
class TestSimoonAdapterIntegration:
    def test_detect(self):
        adapter = SimoonAdapter(SIMOON_ROOT)
        assert adapter.detect() is True

    def test_detect_auto(self):
        adapter = detect_mud_type(SIMOON_ROOT)
        assert adapter is not None
        assert isinstance(adapter, SimoonAdapter)

    def test_detect_wrong_dir(self):
        adapter = SimoonAdapter("/tmp")
        assert adapter.detect() is False

    def test_analyze(self):
        adapter = SimoonAdapter(SIMOON_ROOT)
        report = adapter.analyze()
        assert "Simoon" in report.mud_type
        assert report.room_count > 1000
        assert report.item_count > 100
        assert report.mob_count > 100
        assert report.zone_count > 10

    def test_parse_full(self):
        adapter = SimoonAdapter(SIMOON_ROOT)
        uir = adapter.parse()

        assert uir.source_mud is not None
        assert uir.source_mud.name == "Simoon"
        assert "CircleMUD" in uir.source_mud.codebase

        assert len(uir.rooms) > 1000
        assert len(uir.items) > 100
        assert len(uir.monsters) > 100
        assert len(uir.zones) > 10
        assert len(uir.character_classes) == 7

        assert uir.migration_stats.total_rooms == len(uir.rooms)
        assert uir.migration_stats.total_items == len(uir.items)
        assert uir.migration_stats.total_monsters == len(uir.monsters)

    def test_parse_korean_strings(self):
        adapter = SimoonAdapter(SIMOON_ROOT)
        uir = adapter.parse()

        # At least some rooms should have Korean names
        korean_rooms = [r for r in uir.rooms if any(
            '\uac00' <= c <= '\ud7a3' for c in r.name
        )]
        assert len(korean_rooms) > 100

    def test_parse_mob_extensions(self):
        adapter = SimoonAdapter(SIMOON_ROOT)
        uir = adapter.parse()

        # Find mobs with extensions
        mobs_with_ext = [m for m in uir.monsters if m.extensions]
        assert len(mobs_with_ext) > 0
        # Check a mob has Str attribute
        str_mobs = [m for m in mobs_with_ext if "Str" in m.extensions]
        assert len(str_mobs) > 0

    def test_parse_shops(self):
        adapter = SimoonAdapter(SIMOON_ROOT)
        uir = adapter.parse()
        assert len(uir.shops) > 10

    def test_parse_quests(self):
        adapter = SimoonAdapter(SIMOON_ROOT)
        uir = adapter.parse()
        assert len(uir.quests) > 0

    def test_validate_parsed_uir(self):
        adapter = SimoonAdapter(SIMOON_ROOT)
        uir = adapter.parse()
        result = validate_uir(uir)
        assert result.valid is True


@pytest.mark.skipif(
    not os.path.exists(TBAMUD_ROOT),
    reason="tbaMUD source not available",
)
class TestTbaMudNotDetectedAsSimoon:
    def test_simoon_rejects_tbamud(self):
        adapter = SimoonAdapter(TBAMUD_ROOT)
        assert adapter.detect() is False
