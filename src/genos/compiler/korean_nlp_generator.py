"""Korean NLP Lua generator.

Generates two Lua files:
- korean_nlp.lua: UTF-8 hangul utilities (batchim, particles, verb stems)
- korean_commands.lua: SOV command parser with verb/direction mappings
"""

from __future__ import annotations

from typing import TextIO

from genos.uir.schema import UIR

from .lua_generator import _lua_str


# ── Python reference implementations (used by tests) ─────────────────────


def has_batchim(s: str) -> bool:
    """Check if the last hangul syllable in *s* has a final consonant (받침)."""
    for ch in reversed(s):
        cp = ord(ch)
        if 0xAC00 <= cp <= 0xD7A3:
            return (cp - 0xAC00) % 28 != 0
    return False


def strip_particle(token: str) -> tuple[str, str | None]:
    """Strip a Korean particle from *token*, return (stem, role).

    Particles are matched longest-first.  If stripping would leave an
    empty stem or the stem doesn't end with a hangul syllable, the
    particle is not stripped (returns (token, None)).
    """
    particles = [
        ("에게서", "from_target"),
        ("에게", "target"),
        ("한테", "target"),
        ("에서", "from_loc"),
        ("으로", "dir"),
        ("로", "dir"),
        ("을", "object"),
        ("를", "object"),
        ("이", "subject"),
        ("가", "subject"),
        ("은", "topic"),
        ("는", "topic"),
        ("과", "comit"),
        ("와", "comit"),
        ("에", "location"),
        ("의", "possess"),
    ]
    for suffix, role in particles:
        if token.endswith(suffix):
            stem = token[: -len(suffix)]
            if not stem:
                continue
            # stem must end with a hangul syllable
            last_cp = ord(stem[-1])
            if 0xAC00 <= last_cp <= 0xD7A3:
                return stem, role
    return token, None


def extract_stem(verb: str) -> str:
    """Extract verb stem by removing conjugation endings."""
    endings = ["해줘", "해라", "하다", "하자", "하지", "해", "어", "아", "기"]
    for ending in endings:
        if verb.endswith(ending) and len(verb) > len(ending):
            return verb[: -len(ending)]
    return verb


# ── Standard verb vocabulary ─────────────────────────────────────────────

VERBS: dict[str, str] = {
    # 이동
    "가": "go",
    "떠나": "flee",
    # 전투
    "공격": "attack",
    "죽": "kill",
    "죽이": "kill",
    "싸우": "attack",
    "피하": "flee",
    "구원": "rescue",
    "구해": "rescue",
    # 아이템
    "주워": "get",
    "습득": "get",
    "가져": "get",
    "집": "get",
    "빼": "drop",
    "버려": "drop",
    "놔": "drop",
    "입": "wear",
    "착용": "wear",
    "벗": "remove",
    "들": "hold",
    "챙기": "wield",
    "줘": "give",
    "주": "give",
    "넣": "put",
    "마시": "drink",
    "먹": "eat",
    "사": "buy",
    "팔": "sell",
    # 정보
    "봐": "look",
    "보": "look",
    "건강": "score",
    "정보": "info",
    "주머니": "inventory",
    "꺼내": "equipment",
    "누가": "who",
    "누구": "who",
    "시간": "time",
    "날씨": "weather",
    # 소통
    "말": "say",
    "말하": "say",
    "귓": "tell",
    "외치": "shout",
    "속삭이": "whisper",
    # 상호작용
    "열": "open",
    "닫": "close",
    "잠그": "lock",
    "잠가": "lock",
    "풀": "unlock",
    "찾": "search",
    "앉": "sit",
    "쉬": "rest",
    "자": "sleep",
    "일어나": "stand",
    "서": "stand",
    # 사회
    "따라가": "follow",
    "무리": "group",
    "배우": "practice",
    "학습": "practice",
    # 시스템
    "도움": "help",
    "그만": "quit",
    "저장": "save",
    "별칭": "alias",
    # 마법
    "시전": "cast",
    "주문": "cast",
}

DIRECTIONS: dict[str, int] = {
    "북": 0,
    "북쪽": 0,
    "동": 1,
    "동쪽": 1,
    "남": 2,
    "남쪽": 2,
    "서": 3,
    "서쪽": 3,
    "위": 4,
    "위쪽": 4,
    "아래": 5,
    "아래쪽": 5,
    # 대각선
    "북서": 6,
    "북동": 7,
    "남동": 8,
    "남서": 9,
}


def find_verb(token: str) -> str | None:
    """Look up *token* in VERBS, trying direct match then stem extraction."""
    if token in VERBS:
        return VERBS[token]
    stem = extract_stem(token)
    if stem != token and stem in VERBS:
        return VERBS[stem]
    return None


def parse(input_text: str) -> dict | None:
    """SOV parser — Python reference implementation matching the generated Lua."""
    tokens = input_text.split()
    if not tokens:
        return None

    # Single token
    if len(tokens) == 1:
        stripped, _role = strip_particle(tokens[0])
        if stripped in DIRECTIONS:
            return {"handler": "go", "direction": DIRECTIONS[stripped]}
        action = find_verb(tokens[0])
        if action:
            return {"handler": action, "ordered": []}
        return None

    # Multi-token: SOV (search verb from the end)
    verb_handler = None
    verb_idx = None
    for i in range(len(tokens) - 1, -1, -1):
        vh = find_verb(tokens[i])
        if vh:
            verb_handler = vh
            verb_idx = i
            break

    # SVO fallback (first token)
    if verb_handler is None:
        vh = find_verb(tokens[0])
        if vh:
            verb_handler = vh
            verb_idx = 0

    if verb_handler is None:
        return None

    args: dict = {"handler": verb_handler, "roles": {}, "ordered": []}
    for i, token in enumerate(tokens):
        if i == verb_idx:
            continue
        noun, role = strip_particle(token)
        if noun in DIRECTIONS:
            args["roles"]["direction"] = DIRECTIONS[noun]
        elif role:
            args["roles"][role] = noun
        args["ordered"].append(noun)

    return args


# ── Lua generators ───────────────────────────────────────────────────────


def generate_korean_nlp_lua(out: TextIO) -> None:
    """Generate korean_nlp.lua — Korean NLP utility library."""
    out.write("""\
-- GenOS Korean NLP Utilities
-- Auto-generated — do not edit
-- UTF-8 hangul analysis, particle handling, verb stem extraction

local KoreanNLP = {}

-- ═══ UTF-8 helpers ═══

--- Decode a single UTF-8 character starting at position *i* in *s*.
--- Returns (codepoint, next_index).
function KoreanNLP.utf8_decode(s, i)
    local b = s:byte(i)
    if not b then return nil, i end
    if b < 0x80 then return b, i + 1 end
    if b < 0xE0 then
        return (b - 0xC0) * 64 + (s:byte(i + 1) - 0x80), i + 2
    end
    if b < 0xF0 then
        return (b - 0xE0) * 4096 + (s:byte(i + 1) - 0x80) * 64 + (s:byte(i + 2) - 0x80), i + 3
    end
    return (b - 0xF0) * 262144 + (s:byte(i + 1) - 0x80) * 4096
        + (s:byte(i + 2) - 0x80) * 64 + (s:byte(i + 3) - 0x80), i + 4
end

--- Return the codepoint of the *last* character in *s*.
function KoreanNLP.last_codepoint(s)
    local cp, last_cp = nil, nil
    local i = 1
    while i <= #s do
        cp, i = KoreanNLP.utf8_decode(s, i)
        if cp then last_cp = cp end
    end
    return last_cp
end

--- True if codepoint is a Hangul syllable (U+AC00..U+D7A3).
function KoreanNLP.is_hangul_syllable(cp)
    return cp >= 0xAC00 and cp <= 0xD7A3
end

-- ═══ 받침 (final consonant) detection ═══

--- True if the last Hangul syllable in *str* has a final consonant.
function KoreanNLP.has_batchim(str)
    local cp = KoreanNLP.last_codepoint(str)
    if not cp or not KoreanNLP.is_hangul_syllable(cp) then return false end
    return (cp - 0xAC00) % 28 ~= 0
end

-- ═══ Output particle selection ═══

KoreanNLP.PARTICLE_TYPES = {
""")
    particles = [
        ("subject", "이", "가"),
        ("object", "을", "를"),
        ("topic", "은", "는"),
        ("comit", "과", "와"),
        ("dir", "으로", "로"),
        ("copula", "이다", "다"),
    ]
    for name, with_bat, without_bat in particles:
        out.write(f'    {name} = {{{_lua_str(with_bat)}, {_lua_str(without_bat)}}},\n')
    out.write("""\
}

--- Select the correct output particle for *noun* of type *ptype*.
function KoreanNLP.particle(noun, ptype)
    local pair = KoreanNLP.PARTICLE_TYPES[ptype]
    if not pair then return "" end
    if KoreanNLP.has_batchim(noun) then return pair[1] else return pair[2] end
end

-- ═══ Input particle stripping ═══

KoreanNLP.INPUT_PARTICLES = {
""")
    input_particles = [
        ("에게서", "from_target"),
        ("에게", "target"),
        ("한테", "target"),
        ("에서", "from_loc"),
        ("으로", "dir"),
        ("로", "dir"),
        ("을", "object"),
        ("를", "object"),
        ("이", "subject"),
        ("가", "subject"),
        ("은", "topic"),
        ("는", "topic"),
        ("과", "comit"),
        ("와", "comit"),
        ("에", "location"),
        ("의", "possess"),
    ]
    for suffix, role in input_particles:
        out.write(f'    {{{_lua_str(suffix)}, {_lua_str(role)}}},\n')
    out.write("""\
}

--- Strip a trailing particle from *token*.
--- Returns stem, role (or token, nil if no particle found).
function KoreanNLP.strip_particle(token)
    for _, pair in ipairs(KoreanNLP.INPUT_PARTICLES) do
        local suffix, role = pair[1], pair[2]
        local slen = #suffix
        if #token > slen and token:sub(-slen) == suffix then
            local stem = token:sub(1, -(slen + 1))
            -- verify stem ends with a hangul syllable
            local cp = KoreanNLP.last_codepoint(stem)
            if cp and KoreanNLP.is_hangul_syllable(cp) then
                return stem, role
            end
        end
    end
    return token, nil
end

-- ═══ Verb stem extraction ═══

KoreanNLP.VERB_ENDINGS = {
""")
    verb_endings = ["해줘", "해라", "하다", "하자", "하지", "해", "어", "아", "기"]
    for ending in verb_endings:
        out.write(f'    {_lua_str(ending)},\n')
    out.write("""\
}

--- Remove conjugation endings from *verb*, returning the stem.
function KoreanNLP.extract_stem(verb)
    for _, ending in ipairs(KoreanNLP.VERB_ENDINGS) do
        local elen = #ending
        if #verb > elen and verb:sub(-elen) == ending then
            return verb:sub(1, -(elen + 1))
        end
    end
    return verb
end

return KoreanNLP
""")


def generate_korean_commands_lua(uir: UIR, out: TextIO) -> None:
    """Generate korean_commands.lua — SOV command parser."""
    out.write("""\
-- GenOS Korean Command System (SOV parser)
-- Auto-generated — do not edit

local KoreanNLP = require("korean_nlp")
local Commands = {}

-- ═══ Standard Korean verb → action mapping ═══
Commands.VERBS = {
""")
    for kr, en in sorted(VERBS.items()):
        out.write(f'    [{_lua_str(kr)}] = {_lua_str(en)},\n')
    out.write("""\
}

-- ═══ Direction mapping ═══
Commands.DIRECTIONS = {
""")
    for kr, idx in sorted(DIRECTIONS.items(), key=lambda kv: (kv[1], kv[0])):
        out.write(f'    [{_lua_str(kr)}] = {idx},\n')
    # numpad directions
    numpad = [("8", 0), ("6", 1), ("2", 2), ("4", 3), ("9", 7), ("3", 8)]
    for key, idx in numpad:
        out.write(f'    [{_lua_str(key)}] = {idx},\n')
    out.write("""\
}

-- ═══ Skill / spell name mapping (from UIR) ═══
Commands.SPELL_NAMES = {
""")
    for skill in uir.skills:
        kr_name = skill.extensions.get("korean_name", "")
        if kr_name:
            out.write(f'    [{_lua_str(kr_name)}] = {skill.id},\n')
    out.write("""\
}

-- ═══ Verb lookup (direct match → stem extraction → match) ═══
function Commands.find_verb(token)
    if Commands.VERBS[token] then return Commands.VERBS[token] end
    local stem = KoreanNLP.extract_stem(token)
    if stem and Commands.VERBS[stem] then return Commands.VERBS[stem] end
    return nil
end

-- ═══ SOV parser ═══
function Commands.parse(input)
    local tokens = {}
    for token in input:gmatch("%S+") do table.insert(tokens, token) end
    if #tokens == 0 then return nil end

    -- Single token: direction or verb
    if #tokens == 1 then
        local stripped, _role = KoreanNLP.strip_particle(tokens[1])
        if Commands.DIRECTIONS[stripped] then
            return {handler = "go", direction = Commands.DIRECTIONS[stripped]}
        end
        local action = Commands.find_verb(tokens[1])
        if action then return {handler = action, ordered = {}} end
        if Commands.SPELL_NAMES[tokens[1]] then
            return {handler = "cast", spell_id = Commands.SPELL_NAMES[tokens[1]]}
        end
        return nil
    end

    -- Multi-token: search verb from the end (SOV)
    local verb_handler, verb_idx = nil, nil
    for i = #tokens, 1, -1 do
        verb_handler = Commands.find_verb(tokens[i])
        if verb_handler then verb_idx = i; break end
    end

    -- SVO fallback: first token as verb
    if not verb_handler then
        verb_handler = Commands.find_verb(tokens[1])
        verb_idx = 1
    end
    if not verb_handler then return nil end

    -- Remaining tokens: strip particles and assign semantic roles
    local args = {handler = verb_handler, roles = {}, ordered = {}}
    for i, token in ipairs(tokens) do
        if i ~= verb_idx then
            local noun, role = KoreanNLP.strip_particle(token)
            if Commands.DIRECTIONS[noun] then
                args.roles["direction"] = Commands.DIRECTIONS[noun]
            elseif role then
                args.roles[role] = noun
            end
            table.insert(args.ordered, noun)
        end
    end
    return args
end

return Commands
""")
