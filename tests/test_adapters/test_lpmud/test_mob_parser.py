"""Tests for monster parser."""

import tempfile
from pathlib import Path

from genos.adapters.lpmud.mob_parser import _parse_mob_file
from genos.adapters.lpmud.vnum_generator import VnumGenerator

SAMPLE_MOB_SIMPLE = """\
#include <구조.h>
inherit LIB_MONSTER;

void create()
{
    ::create();
    setName("곰");
    setID(({ "곰", "동물" }));
    setShort("곰이 한가로이 서 있다.");
    setLong("좀전에 먹이를 먹었는지 졸린듯한 눈빛으로 바라보고 있다.");
    setGender("동물");
    setRace("동물");
    setStat("힘", 50);
    setStat("민첩", 15);
    setStat("기골", 20);
    setMaxHp(100);
    setMaxSp(25);
    setMaxMp(20);
    setHp(100);
    setSp(25);
    setMp(20);
    cloneItem("/방/늑대/obj/웅담");
    setBasicAttackMessage(({ "이빨로 깨물었다.", "발톱으로 할퀴었다." }));
    setExp(25);
}
"""

SAMPLE_MOB_COMPLEX = """\
#include <구조.h>
inherit LIB_MONSTER;

void create()
{
  ::create();
  setName("서개");
  setID(({ "서개", "개방제자", "문지기" }));
  setShort("개방의 정문을 지키는 제자 서개가 있다.");
  setLong("구파일방에서 유일한 방파인 개방의 입구를 지키는 제자이다.");
  setGender("남자");
  setRace("인간");
  setMunpa("개방");
  randomStat(100);
  setStat("힘", 100);
  setStat("내공", 100);
  setupBody();
  setAggresiveMunpa();
  cloneItem("/방/문파/개방/obj/타구봉");
  setBasicAttackMessage(({ "한걸음 내딛으며 주먹으로 질러쳤다." }));
  setProp("도망불가", 1);
}
"""


def _write_mob(tmpdir, rel, content):
    p = tmpdir / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content.encode("euc-kr"))
    return p


class TestMobParser:
    def test_simple_mob(self, tmp_path):
        lib_dir = tmp_path
        fp = _write_mob(lib_dir, "방/늑대/mob/곰.c", SAMPLE_MOB_SIMPLE)
        vnum_gen = VnumGenerator()

        mob = _parse_mob_file(fp, lib_dir, vnum_gen, "euc-kr")

        assert mob is not None
        assert mob.short_description == "곰이 한가로이 서 있다."
        assert mob.keywords == "곰 동물"
        assert mob.sex == 0  # 동물
        assert mob.experience == 25
        assert mob.hp_dice.num > 0  # from max_hp=100
        assert mob.extensions["race"] == "동물"
        assert "/방/늑대/obj/웅담" in mob.extensions["inventory"]
        assert mob.extensions["stats"]["힘"] == 50

    def test_complex_mob(self, tmp_path):
        lib_dir = tmp_path
        fp = _write_mob(lib_dir, "방/문파/개방/mob/서개.c", SAMPLE_MOB_COMPLEX)
        vnum_gen = VnumGenerator()

        mob = _parse_mob_file(fp, lib_dir, vnum_gen, "euc-kr")

        assert mob is not None
        assert mob.level == 100  # from randomStat(100)
        assert mob.sex == 1  # 남자
        assert mob.extensions["faction"] == "개방"
        assert 2 in mob.action_flags  # AGGRESSIVE_MUNPA
        assert mob.extensions["props"]["도망불가"] == 1

    def test_non_monster_file(self, tmp_path):
        lib_dir = tmp_path
        content = '#include <구조.h>\ninherit LIB_ROOM;\nvoid create() {}'
        fp = _write_mob(lib_dir, "방/test.c", content)
        vnum_gen = VnumGenerator()

        mob = _parse_mob_file(fp, lib_dir, vnum_gen, "euc-kr")
        assert mob is None
