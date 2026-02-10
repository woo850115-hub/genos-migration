"""Tests for room parser."""

import tempfile
from pathlib import Path

import pytest

from genos.adapters.lpmud.room_parser import parse_room_file, resolve_exits
from genos.adapters.lpmud.vnum_generator import VnumGenerator

SAMPLE_ROOM = """\
#include <구조.h>
inherit LIB_ROOM;

void create()
{
  room::create();
  setShort("곤륜산 기슭");
  setLong(
    "곤륜산 산자락으로 작은 계곡과 언덕이 여기저기에 퍼져있다."
  );
  setExits(([
    "남" : "/방/곤륜산/grs10186",
    "북서" : "/방/곤륜산/grs10145",
  ]));
  setRoomAttr(0);
  setOutSide();
  setMp(40);
  reset();
}
"""

SAMPLE_ROOM_INVENTORY = """\
#include <구조.h>
inherit LIB_ROOM;

void create()
{
  room::create();
  setShort("곰 동굴");
  setLong("장백산일대에 서식하는 곰들의 서식지이다.");
  setExits(([
    "북" : "/방/곰/bbar0313",
  ]));
  setRoomInventory(([
    "/방/늑대/mob/곰" : 1,
    "/방/늑대/mob/백사" : 2,
  ]));
  setLight();
  setRoomAttr(1);
  reset();
}
"""

SAMPLE_ROOM_PROPS = """\
#include <구조.h>
inherit LIB_ROOM;

void create()
{
  room::create();
  setShort("외개방");
  setLong("개방의 내부입니다.");
  setExits(([
    "회혼실" : "/방/문파/개방/회혼실",
    "서" : "/방/문파/개방/외개방04",
  ]));
  setLight();
  setRoomAttr(20);
  setProp("FREE_PK", 1);
  setProp("문파내부", "개방");
  reset();
}
"""


def _write_room_file(tmpdir: Path, rel_path: str, content: str) -> Path:
    """Write a room .c file and return its path."""
    filepath = tmpdir / rel_path
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_bytes(content.encode("euc-kr"))
    return filepath


class TestRoomParser:
    def test_basic_room(self, tmp_path):
        lib_dir = tmp_path
        filepath = _write_room_file(lib_dir, "방/곤륜산/grs10166.c", SAMPLE_ROOM)
        vnum_gen = VnumGenerator()

        room, pending = parse_room_file(filepath, lib_dir, vnum_gen)

        assert room is not None
        assert room.name == "곤륜산 기슭"
        assert "계곡과 언덕" in room.description
        assert room.sector_type == 0  # outdoor
        assert room.extensions.get("movement_cost") == 40

        # Exits pending resolution
        assert "남" in pending
        assert "북서" in pending
        assert pending["남"] == "/방/곤륜산/grs10186"

    def test_room_inventory(self, tmp_path):
        lib_dir = tmp_path
        filepath = _write_room_file(lib_dir, "방/곰/bbar0333.c", SAMPLE_ROOM_INVENTORY)
        vnum_gen = VnumGenerator()

        room, pending = parse_room_file(filepath, lib_dir, vnum_gen)

        assert room is not None
        assert room.name == "곰 동굴"
        inv = room.extensions.get("room_inventory", {})
        assert inv["/방/늑대/mob/곰"] == 1
        assert inv["/방/늑대/mob/백사"] == 2
        # Light flag should be present
        assert 100 in room.room_flags

    def test_room_props(self, tmp_path):
        lib_dir = tmp_path
        filepath = _write_room_file(lib_dir, "방/문파/개방/외개방05.c", SAMPLE_ROOM_PROPS)
        vnum_gen = VnumGenerator()

        room, pending = parse_room_file(filepath, lib_dir, vnum_gen)

        assert room is not None
        props = room.extensions.get("props", {})
        assert props["FREE_PK"] == 1
        assert props["문파내부"] == "개방"

        # Named entrance
        assert "회혼실" in pending

    def test_exit_resolution(self, tmp_path):
        lib_dir = tmp_path
        _write_room_file(lib_dir, "방/곤륜산/grs10166.c", SAMPLE_ROOM)
        _write_room_file(lib_dir, "방/곤륜산/grs10186.c", SAMPLE_ROOM.replace("grs10166", "grs10186"))

        vnum_gen = VnumGenerator()
        filepath1 = lib_dir / "방/곤륜산/grs10166.c"
        filepath2 = lib_dir / "방/곤륜산/grs10186.c"

        room1, pending1 = parse_room_file(filepath1, lib_dir, vnum_gen)
        room2, _ = parse_room_file(filepath2, lib_dir, vnum_gen)

        rooms = [room1, room2]
        resolve_exits(rooms, {room1.vnum: pending1}, vnum_gen)

        # Room1 should now have exits with VNUMs
        assert len(room1.exits) == 2
        dest_vnums = {e.destination for e in room1.exits}
        expected_vnum = vnum_gen.path_to_vnum("/방/곤륜산/grs10186")
        assert expected_vnum in dest_vnums

    def test_non_room_file(self, tmp_path):
        lib_dir = tmp_path
        content = '#include <구조.h>\ninherit LIB_MONSTER;\nvoid create() {}'
        filepath = _write_room_file(lib_dir, "방/mob/test.c", content)
        vnum_gen = VnumGenerator()

        room, pending = parse_room_file(filepath, lib_dir, vnum_gen)
        assert room is None
