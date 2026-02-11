"""Tests for LP-MUD adapter (detect, analyze, parse)."""

import shutil
from pathlib import Path

import pytest

from genos.adapters.lpmud.adapter import LPMudAdapter


def _create_minimal_lpmud(tmp_path: Path) -> Path:
    """Create a minimal LP-MUD directory structure for testing."""
    root = tmp_path / "lpmud"
    root.mkdir()

    # bin/ with driver
    bin_dir = root / "bin"
    bin_dir.mkdir()
    (bin_dir / "driver").touch()
    (bin_dir / "fluffos-han-test").touch()

    # lib/
    lib_dir = root / "lib"
    lib_dir.mkdir()

    # lib/구조/
    (lib_dir / "구조").mkdir()
    (lib_dir / "구조" / "room.c").write_text("// base room")

    # lib/삽입파일/
    header_dir = lib_dir / "삽입파일"
    header_dir.mkdir()

    # 직업.h
    job_h = '''\
#ifndef __JOBH__
#define __JOBH__
static mapping *JobData = ({
([ "직업명" : "투사", "선행능력" : ({ 0, 0, 0, 0, 0, 0 }),
   "주요능력" : ({ 1,1,0,0,0,0 }), "기본유닛" : 6, "증가유닛" : 2,
   "증가멈춤" : 10, "직결직업" : ({ "전사" }),
   "관계직업" : ({ }), "선행직업" : ({ }) ]),
});
#endif
'''
    (header_dir / "직업.h").write_bytes(job_h.encode("euc-kr"))

    # 기술.h
    skill_h = '''\
#ifndef __SKILLH__
#define __SKILLH__
static mapping *SkillData = ({
([ "기술명" : "패리L1", "최대" : 20, "단위" : 2, "직업" : "투사", "레벨" : 8 ]),
});
#endif
'''
    (header_dir / "기술.h").write_bytes(skill_h.encode("euc-kr"))

    # lib/방/ with room files
    room_dir = lib_dir / "방" / "테스트"
    room_dir.mkdir(parents=True)

    room1 = '''\
#include <구조.h>
inherit LIB_ROOM;
void create() {
  room::create();
  setShort("테스트 방");
  setLong("테스트 방 설명입니다.");
  setExits(([ "남" : "/방/테스트/room02" ]));
  setOutSide();
  reset();
}
'''
    (room_dir / "room01.c").write_bytes(room1.encode("euc-kr"))

    room2 = '''\
#include <구조.h>
inherit LIB_ROOM;
void create() {
  room::create();
  setShort("테스트 방 2");
  setLong("두번째 테스트 방입니다.");
  setExits(([ "북" : "/방/테스트/room01" ]));
  setRoomAttr(1);
  reset();
}
'''
    (room_dir / "room02.c").write_bytes(room2.encode("euc-kr"))

    # lib/방/테스트/mob/ with monster
    mob_dir = room_dir / "mob"
    mob_dir.mkdir()
    mob1 = '''\
#include <구조.h>
inherit LIB_MONSTER;
void create() {
  ::create();
  setName("테스트몹");
  setID(({ "몹" }));
  setShort("테스트 몬스터가 있다.");
  setGender("남자");
  randomStat(10);
  setExp(100);
}
'''
    (mob_dir / "test_mob.c").write_bytes(mob1.encode("euc-kr"))

    # lib/물체/ with item
    item_dir = lib_dir / "물체" / "무기"
    item_dir.mkdir(parents=True)
    weapon1 = '''\
#include <구조.h>
inherit LIB_WEAPON;
void create() {
  ::create();
  setName("테스트검");
  setID(({ "검" }));
  setShort("테스트 검이 있다.");
  setMass(10);
  setValue(500);
  setSpWeapon(5);
  setType("왼손");
  setLimitLevel(10);
}
'''
    (item_dir / "test_weapon.c").write_bytes(weapon1.encode("euc-kr"))

    # lib/도움말/
    help_dir = lib_dir / "도움말"
    help_dir.mkdir()
    (help_dir / "테스트.help").write_bytes("테스트 도움말입니다.".encode("euc-kr"))

    # lib/명령어/플레이어/
    cmd_dir = lib_dir / "명령어" / "플레이어"
    cmd_dir.mkdir(parents=True)
    cmd1 = '''\
#include <구조.h>
inherit LIB_DAEMON;
string *getCMD() { return ({ "때", "때려" }); }
mixed CMD(string str) { return 1; }
'''
    (cmd_dir / "때려.c").write_bytes(cmd1.encode("euc-kr"))

    return root


class TestLPMudAdapter:
    def test_detect_valid(self, tmp_path):
        root = _create_minimal_lpmud(tmp_path)
        adapter = LPMudAdapter(root)
        assert adapter.detect() is True

    def test_detect_no_driver(self, tmp_path):
        root = _create_minimal_lpmud(tmp_path)
        # Remove driver
        shutil.rmtree(root / "bin")
        (root / "bin").mkdir()
        adapter = LPMudAdapter(root)
        assert adapter.detect() is False

    def test_detect_no_lib(self, tmp_path):
        root = tmp_path / "empty"
        root.mkdir()
        (root / "bin").mkdir()
        (root / "bin" / "driver").touch()
        adapter = LPMudAdapter(root)
        assert adapter.detect() is False

    def test_analyze(self, tmp_path):
        root = _create_minimal_lpmud(tmp_path)
        adapter = LPMudAdapter(root)
        report = adapter.analyze()

        assert report.mud_type == "LP-MUD/FluffOS (LPC Source)"
        assert report.room_count == 2
        assert report.mob_count == 1
        assert report.item_count >= 1
        assert report.help_count == 1
        assert report.command_count == 1
        assert report.skill_count == 1

    def test_parse(self, tmp_path):
        root = _create_minimal_lpmud(tmp_path)
        adapter = LPMudAdapter(root)
        uir = adapter.parse()

        assert uir.source_mud.codebase == "LP-MUD (FluffOS/MudOS)"

        # Rooms
        assert len(uir.rooms) == 2
        room_names = {r.name for r in uir.rooms}
        assert "테스트 방" in room_names
        assert "테스트 방 2" in room_names

        # Exits should be resolved
        room1 = next(r for r in uir.rooms if r.name == "테스트 방")
        assert len(room1.exits) == 1
        assert room1.exits[0].direction == 2  # 남 = South

        # Monsters
        assert len(uir.monsters) == 1
        assert uir.monsters[0].short_description == "테스트 몬스터가 있다."
        assert uir.monsters[0].level == 10

        # Items
        assert len(uir.items) >= 1
        weapon = next((i for i in uir.items if "검" in i.keywords), None)
        assert weapon is not None
        assert weapon.item_type == 5  # WEAPON
        assert weapon.values[1] == 5  # spWeapon

        # Classes and Skills
        assert len(uir.character_classes) == 1
        assert uir.character_classes[0].name == "투사"
        assert len(uir.skills) == 1

        # Help and Commands
        assert len(uir.help_entries) == 1
        assert len(uir.commands) == 1

        # Zones
        assert len(uir.zones) >= 1

        # Stats
        assert uir.migration_stats.total_rooms == 2
        assert uir.migration_stats.total_monsters == 1

    def test_build_reset_commands_mob(self, tmp_path):
        """room_inventory의 mob 경로 → M reset command 생성."""
        root = _create_minimal_lpmud(tmp_path)
        # room01에 setRoomInventory 추가 (mob 스폰)
        room_dir = root / "lib" / "방" / "테스트"
        room1 = '''\
#include <구조.h>
inherit LIB_ROOM;
void create() {
  room::create();
  setShort("테스트 방");
  setLong("테스트 방 설명입니다.");
  setExits(([ "남" : "/방/테스트/room02" ]));
  setRoomInventory(([ "/방/테스트/mob/test_mob" : 2 ]));
  setOutSide();
  reset();
}
'''
        (room_dir / "room01.c").write_bytes(room1.encode("euc-kr"))

        adapter = LPMudAdapter(root)
        uir = adapter.parse()

        # Find zone that has reset commands
        cmds = []
        for z in uir.zones:
            cmds.extend(z.reset_commands)

        m_cmds = [c for c in cmds if c.command == "M"]
        assert len(m_cmds) >= 1
        # arg1 = mob vnum, arg2 = max_existing (2), arg3 = room vnum
        assert m_cmds[0].arg2 == 2

    def test_build_reset_commands_item(self, tmp_path):
        """room_inventory의 item 경로 → O reset command 생성."""
        root = _create_minimal_lpmud(tmp_path)
        room_dir = root / "lib" / "방" / "테스트"
        room1 = '''\
#include <구조.h>
inherit LIB_ROOM;
void create() {
  room::create();
  setShort("테스트 방");
  setLong("테스트 방 설명입니다.");
  setExits(([ "남" : "/방/테스트/room02" ]));
  setRoomInventory(([ "/물체/무기/test_weapon" : 1 ]));
  setOutSide();
  reset();
}
'''
        (room_dir / "room01.c").write_bytes(room1.encode("euc-kr"))

        adapter = LPMudAdapter(root)
        uir = adapter.parse()

        cmds = []
        for z in uir.zones:
            cmds.extend(z.reset_commands)

        o_cmds = [c for c in cmds if c.command == "O"]
        assert len(o_cmds) >= 1
        assert o_cmds[0].arg2 == 1

    def test_build_reset_commands_limit_mob(self, tmp_path):
        """setLimitMob이 있으면 M 명령의 arg2를 오버라이드."""
        root = _create_minimal_lpmud(tmp_path)
        room_dir = root / "lib" / "방" / "테스트"
        room1 = '''\
#include <구조.h>
inherit LIB_ROOM;
void create() {
  room::create();
  setShort("테스트 방");
  setLong("테스트 방 설명입니다.");
  setExits(([ "남" : "/방/테스트/room02" ]));
  setRoomInventory(([ "/방/테스트/mob/test_mob" : 3 ]));
  setLimitMob(([ "/방/테스트/mob/test_mob" : 10 ]));
  setOutSide();
  reset();
}
'''
        (room_dir / "room01.c").write_bytes(room1.encode("euc-kr"))

        adapter = LPMudAdapter(root)
        uir = adapter.parse()

        cmds = []
        for z in uir.zones:
            cmds.extend(z.reset_commands)

        m_cmds = [c for c in cmds if c.command == "M"]
        assert len(m_cmds) >= 1
        # arg2 should be 10 (limit_mob), not 3 (room_inventory count)
        assert m_cmds[0].arg2 == 10

    def test_real_data_detect(self):
        """Test detection on actual 10woongi data."""
        real_path = Path("/home/genos/workspace/10woongi")
        if not real_path.exists():
            pytest.skip("10woongi data not available")
        adapter = LPMudAdapter(real_path)
        assert adapter.detect() is True

    def test_real_data_analyze(self):
        """Test analysis on actual 10woongi data."""
        real_path = Path("/home/genos/workspace/10woongi")
        if not real_path.exists():
            pytest.skip("10woongi data not available")
        adapter = LPMudAdapter(real_path)
        report = adapter.analyze()
        assert report.room_count > 10000
        assert report.mob_count > 500
        assert report.help_count >= 70
        assert report.command_count >= 50
        assert report.skill_count >= 48
