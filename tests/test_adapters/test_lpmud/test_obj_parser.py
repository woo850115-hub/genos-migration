"""Tests for object/item parser."""

from pathlib import Path

from genos.adapters.lpmud.obj_parser import _parse_item_file
from genos.adapters.lpmud.vnum_generator import VnumGenerator

SAMPLE_WEAPON = """\
#include <구조.h>
#include <전투.h>
inherit LIB_WEAPON;

void create()
{
    ::create();
    setName("유부마검");
    setID( ({ "마검", }) );
    setShort("검은 어둠의 검신에 마기가 있는 유부마검이 있다.");
    setLong("검을 빼내어 들면 귀신의 울음 소리같은 마찰음이 들린다.");
    setMass(25);
    setSpWeapon(17);
    setValue(18000);
    setType("왼손");
    setMaxLifeCircle(3);
    setLimitLevel(150);
}
"""

SAMPLE_ARMOR = """\
#include <구조.h>
#include <전투.h>
inherit LIB_ARMOR;

void create()
{
    ::create();
    setName("무위갑주");
    setID( ({ "무위갑주" }) );
    setShort("특별한 장식을 찾아볼 수 없는 무위갑주이다.");
    setLong("하체를 보호하여 내상을 입지 않도록 도와주는 갑옷이다.");
    setMass(20);
    setValue(100000);
    setSpArmor(10);
    setType("하체");
    setLimitLevel(150);
    setMaxLifeCircle(3);
}
"""


def _write_item(tmpdir, rel, content):
    p = tmpdir / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content.encode("euc-kr"))
    return p


class TestObjParser:
    def test_weapon(self, tmp_path):
        lib_dir = tmp_path
        fp = _write_item(lib_dir, "물체/내력무기/유부마검.c", SAMPLE_WEAPON)
        vnum_gen = VnumGenerator()

        item = _parse_item_file(fp, lib_dir, vnum_gen, "euc-kr")

        assert item is not None
        assert item.item_type == 5  # WEAPON
        assert item.keywords == "마검"
        assert item.weight == 25
        assert item.cost == 18000
        assert item.min_level == 150
        assert item.values[1] == 17  # spWeapon
        assert 12 in item.wear_flags  # 왼손
        assert item.timer == 3  # maxLifeCircle

    def test_armor(self, tmp_path):
        lib_dir = tmp_path
        fp = _write_item(lib_dir, "물체/내력갑옷/무위갑주.c", SAMPLE_ARMOR)
        vnum_gen = VnumGenerator()

        item = _parse_item_file(fp, lib_dir, vnum_gen, "euc-kr")

        assert item is not None
        assert item.item_type == 9  # ARMOR
        assert item.keywords == "무위갑주"
        assert item.values[1] == 10  # spArmor
        assert 10 in item.wear_flags  # 하체
        assert item.min_level == 150

    def test_non_item_file(self, tmp_path):
        lib_dir = tmp_path
        content = '#include <구조.h>\ninherit LIB_ROOM;\nvoid create() {}'
        fp = _write_item(lib_dir, "물체/test.c", content)
        vnum_gen = VnumGenerator()

        item = _parse_item_file(fp, lib_dir, vnum_gen, "euc-kr")
        assert item is None
