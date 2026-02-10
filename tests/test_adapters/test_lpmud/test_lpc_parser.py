"""Tests for LPC source code parsing utilities."""

import pytest

from genos.adapters.lpmud.lpc_parser import (
    extract_all_string_pair_calls,
    extract_array,
    extract_clone_items,
    extract_float_call,
    extract_inherit,
    extract_int_call,
    extract_mapping,
    extract_prop_calls,
    extract_string_call,
    extract_void_call,
    strip_color_codes,
    strip_help_color_codes,
    strip_lpc_comments,
)


class TestStripComments:
    def test_line_comments(self):
        text = 'code(); // comment\nmore();'
        assert strip_lpc_comments(text) == "code(); \nmore();"

    def test_block_comments(self):
        text = 'before /* block\ncomment */ after'
        assert strip_lpc_comments(text) == "before  after"

    def test_nested_block(self):
        text = 'a /* outer /* inner */ b */ c'
        # Non-greedy: first */ closes
        assert "c" in strip_lpc_comments(text)


class TestExtractInherit:
    def test_lib_room(self):
        text = '#include <구조.h>\ninherit LIB_ROOM;\n'
        assert extract_inherit(text) == "LIB_ROOM"

    def test_lib_monster(self):
        text = 'inherit LIB_MONSTER;'
        assert extract_inherit(text) == "LIB_MONSTER"

    def test_lib_weapon(self):
        text = 'inherit LIB_WEAPON;'
        assert extract_inherit(text) == "LIB_WEAPON"

    def test_no_inherit(self):
        text = 'void create() {}'
        assert extract_inherit(text) is None


class TestExtractStringCall:
    def test_simple(self):
        text = 'setShort("대기실");'
        assert extract_string_call(text, "setShort") == "대기실"

    def test_multiline(self):
        text = (
            'setLong("넓고 평탄한 길 위에"\n'
            '        "사람들이 지나다닌다.");'
        )
        assert extract_string_call(text, "setLong") == "넓고 평탄한 길 위에사람들이 지나다닌다."

    def test_with_escapes(self):
        text = r'setShort("line1\nline2");'
        assert extract_string_call(text, "setShort") == "line1\nline2"

    def test_not_found(self):
        text = 'setShort("test");'
        assert extract_string_call(text, "setLong") is None

    def test_color_codes_in_string(self):
        text = 'setLong("%^CYAN%^귀환%^RESET%^이라고 치면");'
        result = extract_string_call(text, "setLong")
        assert result == "%^CYAN%^귀환%^RESET%^이라고 치면"


class TestExtractIntCall:
    def test_positive(self):
        text = "setRoomAttr(20);"
        assert extract_int_call(text, "setRoomAttr") == 20

    def test_negative(self):
        text = "setMp(-1);"
        assert extract_int_call(text, "setMp") == -1

    def test_not_found(self):
        text = "setLevel(10);"
        assert extract_int_call(text, "setRoomAttr") is None


class TestExtractFloatCall:
    def test_float(self):
        text = "setAdjExp(2.7);"
        assert extract_float_call(text, "setAdjExp") == pytest.approx(2.7)

    def test_int_as_float(self):
        text = "setAdjExp(3);"
        assert extract_float_call(text, "setAdjExp") == pytest.approx(3.0)


class TestExtractVoidCall:
    def test_present(self):
        text = "setLight();"
        assert extract_void_call(text, "setLight") is True

    def test_absent(self):
        text = "setRoomAttr(1);"
        assert extract_void_call(text, "setLight") is False

    def test_with_args(self):
        text = "setOutSide();"
        assert extract_void_call(text, "setOutSide") is True


class TestExtractMapping:
    def test_simple_exits(self):
        text = '''setExits(([
            "남" : "/방/곤륜산/grs10186",
            "북서" : "/방/곤륜산/grs10145",
        ]));'''
        result = extract_mapping(text, "setExits")
        assert result == {
            "남": "/방/곤륜산/grs10186",
            "북서": "/방/곤륜산/grs10145",
        }

    def test_named_entrance(self):
        text = '''setExits(([
            "회혼실" : "/방/문파/개방/회혼실",
            "서" : "/방/문파/개방/외개방04",
        ]));'''
        result = extract_mapping(text, "setExits")
        assert result is not None
        assert result["회혼실"] == "/방/문파/개방/회혼실"
        assert result["서"] == "/방/문파/개방/외개방04"

    def test_room_inventory(self):
        text = '''setRoomInventory(([
            "/방/늑대/mob/곰" : 1,
            "/방/늑대/mob/백사" : 2,
        ]));'''
        result = extract_mapping(text, "setRoomInventory")
        assert result is not None
        assert result["/방/늑대/mob/곰"] == 1
        assert result["/방/늑대/mob/백사"] == 2

    def test_not_found(self):
        text = "setShort(...);"
        assert extract_mapping(text, "setExits") is None


class TestExtractArray:
    def test_string_array(self):
        text = 'setID(({ "곰", "동물" }));'
        result = extract_array(text, "setID")
        assert result == ["곰", "동물"]

    def test_single_element(self):
        text = 'setID(({ "마검" }));'
        result = extract_array(text, "setID")
        assert result == ["마검"]

    def test_trailing_comma(self):
        text = 'setID(({ "마검", }));'
        result = extract_array(text, "setID")
        assert result == ["마검"]

    def test_not_found(self):
        text = "setName(...);"
        assert extract_array(text, "setID") is None


class TestExtractCloneItems:
    def test_single(self):
        text = 'cloneItem("/방/늑대/obj/웅담");'
        assert extract_clone_items(text) == ["/방/늑대/obj/웅담"]

    def test_multiple(self):
        text = 'cloneItem("/a/b");\ncloneItem("/c/d");'
        assert extract_clone_items(text) == ["/a/b", "/c/d"]

    def test_none(self):
        text = "setName(...);"
        assert extract_clone_items(text) == []


class TestExtractPropCalls:
    def test_string_prop(self):
        text = 'setProp("문파내부", "개방");'
        result = extract_prop_calls(text)
        assert result["문파내부"] == "개방"

    def test_int_prop(self):
        text = 'setProp("FREE_PK", 1);'
        result = extract_prop_calls(text)
        assert result["FREE_PK"] == 1

    def test_multiple(self):
        text = 'setProp("FREE_PK", 1);\nsetProp("문파내부", "개방");'
        result = extract_prop_calls(text)
        assert result["FREE_PK"] == 1
        assert result["문파내부"] == "개방"


class TestExtractStringPairCalls:
    def test_set_stat(self):
        text = '''
        setStat("힘", 50);
        setStat("민첩", 15);
        setStat("기골", 20);
        '''
        result = extract_all_string_pair_calls(text, "setStat")
        assert ("힘", 50) in result
        assert ("민첩", 15) in result
        assert ("기골", 20) in result


class TestStripColorCodes:
    def test_fluffos(self):
        text = "%^CYAN%^귀환%^RESET%^이라고 치면"
        assert strip_color_codes(text) == "귀환이라고 치면"

    def test_help_codes(self):
        text = "!C신선 때려!RR"
        assert strip_help_color_codes(text) == "신선 때려"

    def test_help_codes_at(self):
        text = "!C도움!@!RR"
        assert strip_help_color_codes(text) == "도움"
