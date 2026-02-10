"""Tests for the 3eyes MUD binary adapter.

Unit tests use in-memory binary records.
Integration tests use the actual 3eyes data directory.
"""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from genos.adapters.threeeyes.binary_utils import (
    flags_to_bit_positions,
    read_byte,
    read_cstring,
    read_cstring_array,
    read_int,
    read_short,
    read_ubyte,
)
from genos.adapters.threeeyes.constants import (
    SIZEOF_CREATURE,
    SIZEOF_EXIT,
    SIZEOF_OBJECT,
    SIZEOF_ROOM,
    RECORDS_PER_FILE,
)
from genos.adapters.threeeyes.obj_parser import parse_obj_file
from genos.adapters.threeeyes.mob_parser import parse_mob_file
from genos.adapters.threeeyes.room_parser import parse_room_file
from genos.adapters.threeeyes.help_parser import parse_help_file
from genos.adapters.threeeyes.talk_parser import (
    parse_talk_file,
    parse_ddesc_file,
    parse_talk_filename,
    parse_ddesc_filename,
)

THREEEYES_DIR = Path("/home/genos/workspace/3eyes")
OBJMON_DIR = THREEEYES_DIR / "objmon"
ROOMS_DIR = THREEEYES_DIR / "rooms"
HELP_DIR = THREEEYES_DIR / "help"


# ── binary_utils unit tests ─────────────────────────────────────────


class TestBinaryUtils:
    def test_read_byte(self):
        data = struct.pack("<b", -42)
        assert read_byte(data, 0) == -42

    def test_read_ubyte(self):
        data = struct.pack("<B", 200)
        assert read_ubyte(data, 0) == 200

    def test_read_short(self):
        data = struct.pack("<h", -1234)
        assert read_short(data, 0) == -1234

    def test_read_int(self):
        data = struct.pack("<i", 100000)
        assert read_int(data, 0) == 100000

    def test_read_cstring_basic(self):
        raw = "Hello".encode("euc-kr") + b"\x00" * 15
        assert read_cstring(raw, 0, 20) == "Hello"

    def test_read_cstring_korean(self):
        text = "파수꾼"
        raw = text.encode("euc-kr") + b"\x00" * 14
        assert read_cstring(raw, 0, 20) == text

    def test_read_cstring_array(self):
        key0 = "검".encode("euc-kr").ljust(20, b"\x00")
        key1 = "칼".encode("euc-kr").ljust(20, b"\x00")
        key2 = b"\x00" * 20
        data = key0 + key1 + key2
        result = read_cstring_array(data, 0, 3, 20)
        assert result[0] == "검"
        assert result[1] == "칼"
        assert result[2] == ""

    def test_flags_to_bit_positions_empty(self):
        assert flags_to_bit_positions(b"\x00\x00") == []

    def test_flags_to_bit_positions_single(self):
        # bit 0 set
        assert flags_to_bit_positions(b"\x01") == [0]

    def test_flags_to_bit_positions_multiple(self):
        # byte 0: bit 1 (0x02), byte 1: bit 0 (0x01) = bit 8
        assert flags_to_bit_positions(b"\x02\x01") == [1, 8]

    def test_flags_matches_f_isset(self):
        """Verify flags_to_bit_positions matches C F_ISSET macro."""
        # F_ISSET(p,f) => p->flags[f/8] & (1<<(f%8))
        flags = bytearray(8)
        # Set flag 6 (MAGGRE = aggressive)
        flags[6 // 8] |= 1 << (6 % 8)
        # Set flag 17 (MMAGIC = casts magic)
        flags[17 // 8] |= 1 << (17 % 8)
        positions = flags_to_bit_positions(bytes(flags))
        assert 6 in positions
        assert 17 in positions


# ── Object parser unit tests ────────────────────────────────────────


class TestObjParser:
    def _make_object_record(self, **kwargs) -> bytes:
        """Build a minimal 352-byte object record."""
        rec = bytearray(SIZEOF_OBJECT)
        name = kwargs.get("name", "테스트검")
        name_bytes = name.encode("euc-kr")
        rec[0 : len(name_bytes)] = name_bytes

        if "type" in kwargs:
            rec[306] = kwargs["type"] & 0xFF

        if "weight" in kwargs:
            struct.pack_into("<h", rec, 304, kwargs["weight"])

        if "wearflag" in kwargs:
            rec[319] = kwargs["wearflag"]

        if "value" in kwargs:
            struct.pack_into("<i", rec, 300, kwargs["value"])

        return bytes(rec)

    def test_parse_empty_record_skipped(self, tmp_path):
        """Empty records (all null name) should be skipped."""
        data = b"\x00" * SIZEOF_OBJECT * RECORDS_PER_FILE
        fpath = tmp_path / "o00"
        fpath.write_bytes(data)
        items = parse_obj_file(fpath, 0)
        assert len(items) == 0

    def test_parse_single_object(self, tmp_path):
        """Parse a single object with basic fields."""
        rec = self._make_object_record(
            name="동전", type=10, weight=1, value=100,
        )
        data = rec + b"\x00" * (SIZEOF_OBJECT * (RECORDS_PER_FILE - 1))
        fpath = tmp_path / "o05"
        fpath.write_bytes(data)
        items = parse_obj_file(fpath, 5)
        assert len(items) == 1
        item = items[0]
        assert item.vnum == 500  # file_index=5, record_index=0
        assert item.short_description == "동전"
        assert item.item_type == 10
        assert item.weight == 1

    def test_wearflag_mapping(self, tmp_path):
        rec = self._make_object_record(name="갑옷", wearflag=1)
        data = rec + b"\x00" * (SIZEOF_OBJECT * (RECORDS_PER_FILE - 1))
        fpath = tmp_path / "o00"
        fpath.write_bytes(data)
        items = parse_obj_file(fpath, 0)
        assert items[0].wear_flags == [1]  # BODY


# ── Monster parser unit tests ───────────────────────────────────────


class TestMobParser:
    def _make_creature_record(self, **kwargs) -> bytes:
        """Build a minimal 1184-byte creature record."""
        rec = bytearray(SIZEOF_CREATURE)

        # type at offset 3: default MONSTER=1
        rec[3] = kwargs.get("type", 1)
        # level at offset 2
        rec[2] = kwargs.get("level", 10)
        # alignment at offset 8
        struct.pack_into("<h", rec, 8, kwargs.get("alignment", 0))
        # name at offset 44
        name = kwargs.get("name", "테스트몹")
        name_bytes = name.encode("euc-kr")
        rec[44 : 44 + len(name_bytes)] = name_bytes
        # experience at offset 28
        struct.pack_into("<i", rec, 28, kwargs.get("experience", 100))
        # gold at offset 32
        struct.pack_into("<i", rec, 32, kwargs.get("gold", 50))
        # ndice/sdice/pdice at offsets 36/38/40
        struct.pack_into("<h", rec, 36, kwargs.get("ndice", 2))
        struct.pack_into("<h", rec, 38, kwargs.get("sdice", 6))
        struct.pack_into("<h", rec, 40, kwargs.get("pdice", 3))

        return bytes(rec)

    def test_player_type_skipped(self, tmp_path):
        """PLAYER type (0) records should be skipped."""
        rec = self._make_creature_record(type=0, name="PlayerChar")
        data = rec + b"\x00" * (SIZEOF_CREATURE * (RECORDS_PER_FILE - 1))
        fpath = tmp_path / "m00"
        fpath.write_bytes(data)
        monsters = parse_mob_file(fpath, 0)
        assert len(monsters) == 0

    def test_parse_single_monster(self, tmp_path):
        rec = self._make_creature_record(
            name="고블린", level=5, alignment=-200,
            experience=500, gold=100, ndice=3, sdice=4, pdice=2,
        )
        data = rec + b"\x00" * (SIZEOF_CREATURE * (RECORDS_PER_FILE - 1))
        fpath = tmp_path / "m02"
        fpath.write_bytes(data)
        monsters = parse_mob_file(fpath, 2)
        assert len(monsters) == 1
        mob = monsters[0]
        assert mob.vnum == 200
        assert mob.short_description == "고블린"
        assert mob.level == 5
        assert mob.alignment == -200
        assert mob.damage_dice.num == 3
        assert mob.damage_dice.size == 4
        assert mob.damage_dice.bonus == 2


# ── Room parser unit tests ──────────────────────────────────────────


class TestRoomParser:
    def _make_room_file(self, **kwargs) -> bytes:
        """Build a minimal room binary file."""
        # Room struct (480 bytes)
        room = bytearray(SIZEOF_ROOM)
        name = kwargs.get("name", "테스트방")
        name_bytes = name.encode("euc-kr")
        room[0 : len(name_bytes)] = name_bytes
        # rom_num at offset 80
        struct.pack_into("<h", room, 80, kwargs.get("rom_num", 1))

        buf = bytearray(room)

        # Exit count
        exits = kwargs.get("exits", [])
        buf += struct.pack("<i", len(exits))
        for ext in exits:
            ext_data = bytearray(SIZEOF_EXIT)
            ext_name = ext.get("name", "남")
            ext_name_bytes = ext_name.encode("euc-kr")
            ext_data[0 : len(ext_name_bytes)] = ext_name_bytes
            struct.pack_into("<h", ext_data, 20, ext.get("room", 0))
            buf += ext_data

        # Monster count = 0
        buf += struct.pack("<i", 0)
        # Object count = 0
        buf += struct.pack("<i", 0)

        # Descriptions (short, long, obj)
        for desc_key in ("short_desc", "long_desc", "obj_desc"):
            desc = kwargs.get(desc_key, "")
            if desc:
                desc_bytes = desc.encode("euc-kr") + b"\x00"
                buf += struct.pack("<i", len(desc_bytes))
                buf += desc_bytes
            else:
                buf += struct.pack("<i", 0)

        return bytes(buf)

    def test_parse_simple_room(self, tmp_path):
        data = self._make_room_file(
            name="초보학교", rom_num=42,
            long_desc="여기는 초보학교입니다.",
        )
        fpath = tmp_path / "r00042"
        fpath.write_bytes(data)
        room = parse_room_file(fpath)
        assert room is not None
        assert room.vnum == 42
        assert room.name == "초보학교"
        assert "초보학교" in room.description

    def test_parse_room_with_exit(self, tmp_path):
        data = self._make_room_file(
            name="방", rom_num=100,
            exits=[{"name": "동", "room": 101}],
        )
        fpath = tmp_path / "r00100"
        fpath.write_bytes(data)
        room = parse_room_file(fpath)
        assert room is not None
        assert len(room.exits) == 1
        assert room.exits[0].keyword == "동"
        assert room.exits[0].destination == 101


# ── Help parser unit tests ──────────────────────────────────────────


class TestHelpParser:
    def test_parse_help_file(self, tmp_path):
        text = "이동관련 명령어:\n\n동, 서, 남, 북으로 이동합니다.\n"
        fpath = tmp_path / "help.1"
        fpath.write_bytes(text.encode("euc-kr"))
        entry = parse_help_file(fpath)
        assert entry is not None
        assert "이동관련" in entry.keywords[0]
        assert "이동합니다" in entry.text


# ── Talk parser unit tests ──────────────────────────────────────────


class TestTalkParser:
    def test_parse_talk_file(self, tmp_path):
        text = "존\n지도를 점검합니다.\n엔젤\n새 인물이지.\n"
        fpath = tmp_path / "길라잡이-25"
        fpath.write_bytes(text.encode("euc-kr"))
        talks = parse_talk_file(fpath)
        assert "존" in talks
        assert "지도" in talks["존"]

    def test_parse_ddesc_file(self, tmp_path):
        text = "검은 알은 킹스파이더의 알이였다.\n"
        fpath = tmp_path / "검은_알_10"
        fpath.write_bytes(text.encode("euc-kr"))
        desc = parse_ddesc_file(fpath)
        assert "킹스파이더" in desc

    def test_parse_talk_filename(self):
        name, level = parse_talk_filename("길라잡이-25")
        assert name == "길라잡이"
        assert level == 25

    def test_parse_ddesc_filename(self):
        name, level = parse_ddesc_filename("검은_알_10")
        assert name == "검은_알"
        assert level == 10


# ── Integration tests (require actual 3eyes data) ──────────────────


@pytest.mark.skipif(
    not THREEEYES_DIR.is_dir(),
    reason="3eyes data directory not available",
)
class TestThreeEyesIntegration:
    def test_detect(self):
        from genos.adapters.threeeyes import ThreeEyesAdapter

        adapter = ThreeEyesAdapter(THREEEYES_DIR)
        assert adapter.detect() is True

    def test_auto_detect(self):
        from genos.adapters.detector import detect_mud_type

        adapter = detect_mud_type(THREEEYES_DIR)
        assert adapter is not None
        assert type(adapter).__name__ == "ThreeEyesAdapter"

    def test_analyze(self):
        from genos.adapters.threeeyes import ThreeEyesAdapter

        adapter = ThreeEyesAdapter(THREEEYES_DIR)
        report = adapter.analyze()
        assert report.room_count > 7000
        assert report.item_count > 1000
        assert report.mob_count > 1000
        assert report.help_count > 100

    def test_parse_rooms(self):
        from genos.adapters.threeeyes.room_parser import parse_all_rooms

        rooms = parse_all_rooms(ROOMS_DIR)
        assert len(rooms) > 7000
        # Verify Korean text decoding
        named = [r for r in rooms if r.name]
        assert len(named) > 7000

    def test_parse_objects(self):
        from genos.adapters.threeeyes.obj_parser import parse_all_objects

        items = parse_all_objects(OBJMON_DIR)
        assert len(items) > 1000
        # Verify item has proper fields
        for item in items[:10]:
            assert item.short_description != ""

    def test_parse_monsters(self):
        from genos.adapters.threeeyes.mob_parser import parse_all_monsters

        monsters = parse_all_monsters(OBJMON_DIR)
        assert len(monsters) > 1000
        for mob in monsters[:10]:
            assert mob.short_description != ""
            assert mob.level > 0

    def test_full_parse(self):
        from genos.adapters.threeeyes import ThreeEyesAdapter

        adapter = ThreeEyesAdapter(THREEEYES_DIR)
        uir = adapter.parse()
        assert len(uir.rooms) > 7000
        assert len(uir.items) > 1000
        assert len(uir.monsters) > 1000
        assert len(uir.help_entries) > 100
        assert len(uir.character_classes) == 8
        assert len(uir.races) == 8
        assert len(uir.skills) == 63
        assert uir.source_mud is not None
        assert uir.source_mud.name == "3eyes"

    def test_existing_adapters_not_broken(self):
        """Ensure adding ThreeEyesAdapter doesn't break existing adapters."""
        from genos.adapters.detector import detect_mud_type

        # tbaMUD should still be detected as CircleMUD
        tbamud_path = Path("/home/genos/workspace/tbamud")
        if tbamud_path.is_dir():
            adapter = detect_mud_type(tbamud_path)
            assert adapter is not None
            assert type(adapter).__name__ == "CircleMudAdapter"
