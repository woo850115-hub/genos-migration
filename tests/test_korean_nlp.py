"""Tests for Korean NLP command system (Phase 4)."""

import io
import os

import pytest

from genos.compiler.korean_nlp_generator import (
    DIRECTIONS,
    VERBS,
    extract_stem,
    find_verb,
    generate_korean_commands_lua,
    generate_korean_nlp_lua,
    has_batchim,
    parse,
    strip_particle,
)
from genos.uir.schema import (
    CharacterClass,
    CombatSystem,
    Skill,
    UIR,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


def _make_test_uir() -> UIR:
    uir = UIR()
    uir.character_classes = [
        CharacterClass(id=0, name="Magic User", abbreviation="Mu",
                        extensions={"base_thac0": 20, "thac0_gain": 0.66}),
    ]
    uir.combat_system = CombatSystem(
        type="thac0", damage_types=["hit", "slash"],
    )
    return uir


def _make_uir_with_korean_skills() -> UIR:
    uir = _make_test_uir()
    uir.skills = [
        Skill(id=1, name="armor", extensions={"korean_name": "갑옷"}),
        Skill(id=2, name="teleport", extensions={"korean_name": "텔레포트"}),
        Skill(id=3, name="fireball", extensions={}),  # no korean name
    ]
    return uir


# ══════════════════════════════════════════════════════════════════════════
# Unit Tests — Python reference implementations
# ══════════════════════════════════════════════════════════════════════════


class TestBatchimDetection:
    """받침 검사 테스트."""

    def test_has_batchim_with_final_consonant(self):
        assert has_batchim("고블린") is True   # 린 → ㄴ 받침
        assert has_batchim("검") is True       # 검 → ㅁ 받침
        assert has_batchim("북") is True       # 북 → ㄱ 받침
        assert has_batchim("상인") is True     # 인 → ㄴ 받침

    def test_no_batchim(self):
        assert has_batchim("고라니") is False  # 니 → 받침 없음
        assert has_batchim("마나") is False    # 나 → 받침 없음
        assert has_batchim("위") is False      # 위 → 받침 없음

    def test_single_char(self):
        assert has_batchim("강") is True
        assert has_batchim("가") is False

    def test_non_hangul(self):
        assert has_batchim("abc") is False
        assert has_batchim("123") is False
        assert has_batchim("") is False

    def test_mixed_hangul_ascii(self):
        # Last hangul char determines
        assert has_batchim("HP검") is True
        assert has_batchim("MP바") is False


class TestParticleStripping:
    """조사 스트리핑 테스트."""

    def test_object_particle_eul(self):
        assert strip_particle("고블린을") == ("고블린", "object")

    def test_object_particle_reul(self):
        assert strip_particle("고라니를") == ("고라니", "object")

    def test_target_particle_ege(self):
        assert strip_particle("상인에게") == ("상인", "target")

    def test_target_particle_hante(self):
        assert strip_particle("상인한테") == ("상인", "target")

    def test_from_target_particle(self):
        assert strip_particle("상인에게서") == ("상인", "from_target")

    def test_direction_particle_euro(self):
        assert strip_particle("북으로") == ("북", "dir")

    def test_direction_particle_ro(self):
        assert strip_particle("위로") == ("위", "dir")

    def test_topic_particle(self):
        assert strip_particle("검은") == ("검", "topic")
        assert strip_particle("나는") == ("나", "topic")

    def test_subject_particle(self):
        assert strip_particle("검이") == ("검", "subject")
        assert strip_particle("나가") == ("나", "subject")

    def test_location_particle(self):
        assert strip_particle("마을에") == ("마을", "location")

    def test_from_loc_particle(self):
        assert strip_particle("마을에서") == ("마을", "from_loc")

    def test_comitative_particle(self):
        assert strip_particle("검과") == ("검", "comit")
        assert strip_particle("나와") == ("나", "comit")

    def test_no_particle(self):
        assert strip_particle("고블린") == ("고블린", None)

    def test_single_char_not_stripped(self):
        # "이" alone — stripping "이" would leave empty stem
        assert strip_particle("이") == ("이", None)

    def test_non_hangul_stem_not_stripped(self):
        # "abc를" — stem "abc" doesn't end with hangul
        assert strip_particle("abc를") == ("abc를", None)


class TestVerbStemExtraction:
    """동사 어간 추출 테스트."""

    def test_hae_ending(self):
        assert extract_stem("공격해") == "공격"

    def test_haera_ending(self):
        assert extract_stem("공격해라") == "공격"

    def test_haejwo_ending(self):
        assert extract_stem("공격해줘") == "공격"

    def test_hada_ending(self):
        assert extract_stem("공격하다") == "공격"

    def test_haja_ending(self):
        assert extract_stem("공격하자") == "공격"

    def test_haji_ending(self):
        assert extract_stem("공격하지") == "공격"

    def test_gi_ending(self):
        assert extract_stem("죽이기") == "죽이"
        assert extract_stem("던지기") == "던지"

    def test_eo_ending(self):
        assert extract_stem("먹어") == "먹"

    def test_a_ending(self):
        assert extract_stem("봐") == "봐"  # single char stem not stripped

    def test_no_ending(self):
        assert extract_stem("공격") == "공격"

    def test_short_verb_not_stripped(self):
        # "해" alone — would leave empty stem
        assert extract_stem("해") == "해"


class TestFindVerb:
    """동사 탐색 테스트."""

    def test_direct_match(self):
        assert find_verb("공격") == "attack"
        assert find_verb("봐") == "look"

    def test_stem_match(self):
        assert find_verb("공격해") == "attack"
        assert find_verb("공격하다") == "attack"
        assert find_verb("공격해라") == "attack"
        assert find_verb("공격해줘") == "attack"

    def test_no_match(self):
        assert find_verb("알수없는단어") is None

    def test_direction_not_verb(self):
        # "북" is in DIRECTIONS but should only be a verb if in VERBS
        assert find_verb("북") is None


class TestSOVParsing:
    """SOV 파서 통합 테스트."""

    def test_single_direction(self):
        result = parse("북")
        assert result is not None
        assert result["handler"] == "go"
        assert result["direction"] == 0

    def test_single_direction_with_particle(self):
        result = parse("북으로")
        assert result is not None
        assert result["handler"] == "go"
        assert result["direction"] == 0

    def test_single_verb(self):
        result = parse("봐")
        assert result is not None
        assert result["handler"] == "look"

    def test_simple_sov(self):
        # "고블린을 공격해" → attack, object=고블린
        result = parse("고블린을 공격해")
        assert result is not None
        assert result["handler"] == "attack"
        assert result["roles"]["object"] == "고블린"

    def test_complex_sov(self):
        # "상인에게 검을 줘" → give, target=상인, object=검
        result = parse("상인에게 검을 줘")
        assert result is not None
        assert result["handler"] == "give"
        assert result["roles"]["target"] == "상인"
        assert result["roles"]["object"] == "검"

    def test_direction_sov(self):
        # "북쪽으로 가" → go, direction=0
        result = parse("북쪽으로 가")
        assert result is not None
        assert result["handler"] == "go"
        assert result["roles"]["direction"] == 0

    def test_svo_fallback(self):
        # "봐 고블린" → look (SVO fallback)
        result = parse("봐 고블린")
        assert result is not None
        assert result["handler"] == "look"
        assert "고블린" in result["ordered"]

    def test_conjugated_verb_sov(self):
        # "고블린을 공격하다" → attack
        result = parse("고블린을 공격하다")
        assert result is not None
        assert result["handler"] == "attack"
        assert result["roles"]["object"] == "고블린"

    def test_empty_input(self):
        assert parse("") is None
        assert parse("   ") is None

    def test_unknown_input(self):
        assert parse("알수없는단어") is None

    def test_three_arg_command(self):
        # "상인에게서 검을 가져" → get, from_target=상인, object=검
        result = parse("상인에게서 검을 가져")
        assert result is not None
        assert result["handler"] == "get"
        assert result["roles"]["from_target"] == "상인"
        assert result["roles"]["object"] == "검"

    def test_direction_in_ordered(self):
        # "위로 가" → go
        result = parse("위로 가")
        assert result is not None
        assert result["handler"] == "go"
        assert result["roles"]["direction"] == 4


# ══════════════════════════════════════════════════════════════════════════
# Verb vocabulary coverage tests
# ══════════════════════════════════════════════════════════════════════════


class TestVerbVocabulary:
    """표준 동사 어휘 검증."""

    def test_verb_count(self):
        assert len(VERBS) >= 55

    def test_direction_count(self):
        assert len(DIRECTIONS) >= 14

    def test_all_actions_are_strings(self):
        for kr, en in VERBS.items():
            assert isinstance(kr, str)
            assert isinstance(en, str)
            assert len(kr) > 0
            assert len(en) > 0

    def test_essential_verbs_present(self):
        essential = {
            "공격": "attack", "봐": "look", "가": "go",
            "줘": "give", "먹": "eat", "마시": "drink",
            "입": "wear", "벗": "remove", "열": "open",
            "닫": "close", "도움": "help", "말": "say",
        }
        for kr, en in essential.items():
            assert VERBS[kr] == en


# ══════════════════════════════════════════════════════════════════════════
# Lua generation tests
# ══════════════════════════════════════════════════════════════════════════


class TestKoreanNLPGeneration:
    """생성된 korean_nlp.lua 검증."""

    def test_nlp_lua_structure(self):
        out = io.StringIO()
        generate_korean_nlp_lua(out)
        lua = out.getvalue()
        assert "local KoreanNLP = {}" in lua
        assert "KoreanNLP.has_batchim" in lua
        assert "KoreanNLP.strip_particle" in lua
        assert "KoreanNLP.particle" in lua
        assert "KoreanNLP.extract_stem" in lua
        assert "KoreanNLP.utf8_decode" in lua
        assert "return KoreanNLP" in lua

    def test_nlp_lua_particle_types(self):
        out = io.StringIO()
        generate_korean_nlp_lua(out)
        lua = out.getvalue()
        for ptype in ["subject", "object", "topic", "comit", "dir", "copula"]:
            assert ptype in lua

    def test_nlp_lua_input_particles(self):
        out = io.StringIO()
        generate_korean_nlp_lua(out)
        lua = out.getvalue()
        for suffix in ["에게서", "에게", "한테", "을", "를", "으로", "로"]:
            assert suffix in lua

    def test_nlp_lua_verb_endings(self):
        out = io.StringIO()
        generate_korean_nlp_lua(out)
        lua = out.getvalue()
        for ending in ["해줘", "해라", "하다", "하자", "하지", "해"]:
            assert ending in lua


class TestKoreanCommandsGeneration:
    """생성된 korean_commands.lua 검증."""

    def test_commands_lua_structure(self):
        uir = _make_test_uir()
        out = io.StringIO()
        generate_korean_commands_lua(uir, out)
        lua = out.getvalue()
        assert "local Commands = {}" in lua
        assert "Commands.VERBS" in lua
        assert "Commands.DIRECTIONS" in lua
        assert "Commands.SPELL_NAMES" in lua
        assert "Commands.parse" in lua
        assert "Commands.find_verb" in lua
        assert "return Commands" in lua

    def test_commands_lua_verbs(self):
        uir = _make_test_uir()
        out = io.StringIO()
        generate_korean_commands_lua(uir, out)
        lua = out.getvalue()
        assert '"공격"' in lua
        assert '"attack"' in lua
        assert '"봐"' in lua
        assert '"look"' in lua

    def test_commands_lua_directions(self):
        uir = _make_test_uir()
        out = io.StringIO()
        generate_korean_commands_lua(uir, out)
        lua = out.getvalue()
        assert '"북"' in lua
        assert '"남"' in lua
        assert '"동"' in lua
        assert '"서"' in lua

    def test_commands_lua_numpad(self):
        uir = _make_test_uir()
        out = io.StringIO()
        generate_korean_commands_lua(uir, out)
        lua = out.getvalue()
        assert '"8"' in lua  # north
        assert '"2"' in lua  # south

    def test_commands_lua_with_korean_skills(self):
        uir = _make_uir_with_korean_skills()
        out = io.StringIO()
        generate_korean_commands_lua(uir, out)
        lua = out.getvalue()
        assert '"갑옷"' in lua
        assert '"텔레포트"' in lua
        # fireball has no korean_name — should not appear as korean
        assert "fireball" not in lua

    def test_commands_lua_empty_skills(self):
        uir = _make_test_uir()
        out = io.StringIO()
        generate_korean_commands_lua(uir, out)
        lua = out.getvalue()
        # SPELL_NAMES section should exist but be empty
        assert "Commands.SPELL_NAMES" in lua

    def test_commands_lua_requires_nlp(self):
        uir = _make_test_uir()
        out = io.StringIO()
        generate_korean_commands_lua(uir, out)
        lua = out.getvalue()
        assert 'require("korean_nlp")' in lua

    def test_commands_lua_sov_parser(self):
        uir = _make_test_uir()
        out = io.StringIO()
        generate_korean_commands_lua(uir, out)
        lua = out.getvalue()
        # SOV: search from end
        assert "for i = #tokens, 1, -1" in lua
        # SVO fallback
        assert "tokens[1]" in lua


# ══════════════════════════════════════════════════════════════════════════
# Compiler integration tests
# ══════════════════════════════════════════════════════════════════════════


class TestCompilerIntegration:
    """컴파일러 파이프라인에서 한국어 Lua 생성 검증."""

    def test_compiler_generates_korean_files(self, tmp_path):
        from genos.compiler.compiler import GenosCompiler

        uir = _make_test_uir()
        compiler = GenosCompiler(uir, tmp_path)
        generated = compiler.compile()

        assert any("korean_nlp.lua" in k for k in generated)
        assert any("korean_commands.lua" in k for k in generated)
        assert generated[str(tmp_path / "lua" / "korean_nlp.lua")] == "Korean NLP utilities"
        assert generated[str(tmp_path / "lua" / "korean_commands.lua")] == "Korean command interpreter"

    def test_compiler_korean_files_exist(self, tmp_path):
        from genos.compiler.compiler import GenosCompiler

        uir = _make_test_uir()
        compiler = GenosCompiler(uir, tmp_path)
        compiler.compile()

        nlp_path = tmp_path / "lua" / "korean_nlp.lua"
        cmd_path = tmp_path / "lua" / "korean_commands.lua"
        assert nlp_path.exists()
        assert cmd_path.exists()

        nlp_lua = nlp_path.read_text()
        assert "KoreanNLP" in nlp_lua

        cmd_lua = cmd_path.read_text()
        assert "Commands" in cmd_lua

    def test_compiler_always_generates_korean(self, tmp_path):
        """Korean files are always generated, even with minimal UIR."""
        from genos.compiler.compiler import GenosCompiler

        uir = _make_test_uir()
        uir.skills = []  # no skills
        compiler = GenosCompiler(uir, tmp_path)
        generated = compiler.compile()

        assert any("korean_nlp.lua" in k for k in generated)
        assert any("korean_commands.lua" in k for k in generated)


# ══════════════════════════════════════════════════════════════════════════
# Full pipeline integration tests (real data sources)
# ══════════════════════════════════════════════════════════════════════════

TBAMUD_ROOT = "/home/genos/workspace/tbamud"
SIMOON_ROOT = "/home/genos/workspace/simoon"
THREEEYES_ROOT = "/home/genos/workspace/3eyes"


@pytest.mark.skipif(
    not os.path.exists(TBAMUD_ROOT),
    reason="tbaMUD source not available",
)
class TestTbaMUDPipeline:

    def test_tbamud_generates_korean(self, tmp_path):
        from genos.adapters.circlemud.adapter import CircleMudAdapter
        from genos.compiler.compiler import GenosCompiler

        adapter = CircleMudAdapter(TBAMUD_ROOT)
        uir = adapter.parse()
        compiler = GenosCompiler(uir, tmp_path)
        generated = compiler.compile()

        assert any("korean_nlp.lua" in k for k in generated)
        assert any("korean_commands.lua" in k for k in generated)

        # Verify content
        nlp_lua = (tmp_path / "lua" / "korean_nlp.lua").read_text()
        assert "KoreanNLP.has_batchim" in nlp_lua

        cmd_lua = (tmp_path / "lua" / "korean_commands.lua").read_text()
        assert "Commands.VERBS" in cmd_lua


@pytest.mark.skipif(
    not os.path.exists(SIMOON_ROOT),
    reason="Simoon source not available",
)
class TestSimoonPipeline:

    def test_simoon_generates_korean(self, tmp_path):
        from genos.adapters.simoon.adapter import SimoonAdapter
        from genos.compiler.compiler import GenosCompiler

        adapter = SimoonAdapter(SIMOON_ROOT)
        uir = adapter.parse()
        compiler = GenosCompiler(uir, tmp_path)
        generated = compiler.compile()

        assert any("korean_nlp.lua" in k for k in generated)
        assert any("korean_commands.lua" in k for k in generated)


@pytest.mark.skipif(
    not os.path.exists(THREEEYES_ROOT),
    reason="3eyes source not available",
)
class TestThreeEyesPipeline:

    def test_threeeyes_generates_korean(self, tmp_path):
        from genos.adapters.threeeyes.adapter import ThreeEyesAdapter
        from genos.compiler.compiler import GenosCompiler

        adapter = ThreeEyesAdapter(THREEEYES_ROOT)
        uir = adapter.parse()
        compiler = GenosCompiler(uir, tmp_path)
        generated = compiler.compile()

        assert any("korean_nlp.lua" in k for k in generated)
        assert any("korean_commands.lua" in k for k in generated)
