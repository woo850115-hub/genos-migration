# 파서 구현 노트 — 삽질 기록과 교훈

이 문서는 tbaMUD 파서를 구현하면서 발견한 함정, 비직관적인 형식 특성, 디버깅 과정에서 배운 교훈을 기록합니다.

---

## 1. T (Trigger) 라인은 S 이후에 온다 (wld_parser)

### 문제
처음에는 T 라인이 S(end marker) 이전에 올 것으로 예상하고 D/E/T/S를 순서 없이 파싱했습니다. 그러나 실제 tbaMUD 데이터에서는 **T 라인이 항상 S 이후**에 위치합니다.

### 실제 형식
```
#91
Aristotle's Prison Cell~
   What used to be a shower stall...
~
0 8 0 0 0 0
E
shower head cap~
   The metal shower head has a plastic...
~
S                    ← 방 데이터 끝
T 171                ← S 이후에 트리거!
T 172                ← 여러 개 가능
#92                  ← 다음 방 시작
```

### 근거
`db.c`의 `parse_room()`:
```c
case 'S':  /* end of room */
  letter = fread_letter(fl);
  ungetc(letter, fl);
  while (letter=='T') {
    dg_read_trigger(fl, &world[room_nr], WLD_TRIGGER);
    letter = fread_letter(fl);
    ungetc(letter, fl);
  }
```

### 해결
S를 만나면 즉시 break하지 않고, S 직후의 T 라인들을 추가로 스캔합니다:

```python
if line == "S":
    i += 1
    while i < len(lines):
        tline = lines[i].rstrip()
        if tline.startswith("T "):
            room.trigger_vnums.append(int(tline.split()[1]))
            i += 1
        else:
            break
    break
```

---

## 2. 128-bit Bitvector의 Wear Flags 위치 (obj_parser)

### 문제
tbaMUD의 obj type/flags 라인이 CircleMUD 원본과 **다른 형식**입니다.

### 기존 CircleMUD (3-4 필드)
```
<type> <extra_flags> <wear_flags> [<affect_flags>]
```

### tbaMUD 128-bit (13 필드)
```
<type> <ef0> <ef1> <ef2> <ef3> <wf0> <wf1> <wf2> <wf3> <af0> <af1> <af2> <af3>
```

**wear_flags는 인덱스 2가 아니라 인덱스 5에 있습니다!**

### 실제 예시
```
9 0 0 0 0 ae 0 0 0 0 0 0 0
```
- `9` = ITEM_ARMOR (type)
- `0 0 0 0` = extra_flags (모두 0)
- `ae` = wear_flags[0] → a(bit0=TAKE) + e(bit4=HEAD)
- `0 0 0` = wear_flags[1-3] (미사용)
- `0 0 0 0` = affect bitvector (모두 0)

### 해결
필드 수로 형식을 자동 감지합니다:

```python
if len(parts) >= 13:
    # tbaMUD 128-bit: wear at index 5
    item.item_type = int(parts[0])
    extra_int = asciiflag_to_int(parts[1])
    wear_int = asciiflag_to_int(parts[5])  # ← 핵심!
elif len(parts) >= 3:
    # Old CircleMUD: wear at index 2
    wear_int = asciiflag_to_int(parts[2])
```

---

## 3. Shop VNUM에는 Tilde가 붙는다 (shp_parser)

### 문제
다른 모든 데이터 타입은 `#123` 형태로 VNUM을 표시하지만, **shop만 `#123~` 형태**입니다.

### 실제 예시
```
CircleMUD v3.0 Shop File~   ← 헤더 라인
#0~                          ← 여기! ~가 붙음
82
-1
1.20
```

### 해결
파싱 시 `~`를 제거합니다:
```python
vnum_str = line[1:].rstrip("~").strip()
```

또한 카운팅 로직도 별도로 구현해야 합니다 (`_count_shop_entries`).

---

## 4. Mob 파서의 E 마커 중복 (mob_parser)

### 문제
Enhanced 포맷에서 'E'가 두 군데 쓰입니다:
1. Flags 라인의 **마지막 필드**로서 포맷 표시: `516106 0 0 0 2128 0 0 0 1000 E`
2. 데이터 블록 끝의 **종료 마커**: 단독 `E` 라인

### 주의점
- T(trigger) 라인은 종료 마커 `E` 이후에 올 수 있음
- BareHandAttack은 종료 마커 이전에 위치

```
516106 0 0 0 2128 0 0 0 1000 E   ← 포맷 표시
34 9 -10 6d6+340 5d5+5
340 115600
8 8 2
BareHandAttack: 12                ← E 이전
E                                 ← 종료 마커
T 95                              ← E 이후
```

---

## 5. Asciiflag는 숫자도 될 수 있다

### 문제
Room flags가 `8`이면 이것은 asciiflag가 아니라 **정수 8**입니다. `8`을 asciiflag로 해석하면 아무 비트도 안 서는 것이 아니라, `int('8') = 8`로 처리해야 합니다.

### 로직
```python
def asciiflag_to_int(flag_str):
    try:
        return int(flag_str)  # 숫자면 그대로 반환
    except ValueError:
        pass
    # 문자열이면 비트 변환
    result = 0
    for ch in flag_str:
        if ch.islower():
            result |= 1 << (ord(ch) - ord('a'))
        elif ch.isupper():
            result |= 1 << (26 + ord(ch) - ord('A'))
    return result
```

### 주의
- `"8"` → 8 (정수)
- `"d"` → 8 (비트 3)
- 이 둘은 같은 값이지만 다른 경로로 도달

---

## 6. Zone 파라미터 라인의 가변 필드 수

### 문제
Zone 파라미터 라인은 버전에 따라 필드 수가 다릅니다:

```
# 기본 (4 필드)
0 99 30 2

# tbaMUD 확장 (10 필드)
0 99 30 2 d 0 0 0 -1 -1
```

### 해결
`len(parts)` 체크로 순차적으로 파싱:

```python
if len(parts) >= 4:   # bot, top, lifespan, reset_mode
if len(parts) >= 5:   # zone_flags
if len(parts) >= 9:   # min_level
if len(parts) >= 10:  # max_level
```

---

## 7. Zone Reset 커맨드의 탭 코멘트

### 문제
Zone 리셋 커맨드 뒤에 TAB으로 구분된 코멘트가 있을 수 있습니다:

```
M 0 34 1 8 	(Chuck Norris)
               ^tab    ^comment
```

### 해결
TAB 기준으로 분리 후 파싱:
```python
if "\t" in line:
    cmd_part, comment = line.split("\t", 1)
else:
    cmd_part, comment = line, ""
```

---

## 8. Tilde 문자열 읽기의 엣지 케이스

### 빈 문자열
```
~       ← action_description이 비어있음
```
→ 빈 문자열 반환

### 여러 줄 + 마지막 줄에 내용
```
A long description
that spans multiple
lines~
```
→ `"A long description\nthat spans multiple\nlines"`

### ~가 줄 끝이 아닌 중간에 있는 경우
tbaMUD에서는 `~`가 항상 줄 끝에 위치합니다. 줄 중간의 `~`는 발생하지 않습니다 (OLC 에디터가 이를 방지).

---

## 9. .obj 파일이 바이너리로 감지되는 문제

### 문제
일부 도구(파일 리더 포함)가 `.obj` 확장자를 바이너리 오브젝트 파일로 오인합니다.

### 해결
- 파일 읽기 시 `encoding="utf-8", errors="replace"` 사용
- 또는 확장자가 아닌 내용 기반 감지 사용

---

## 10. pyproject.toml의 build-backend

### 문제
`setuptools.backends._legacy:_Backend`는 존재하지 않습니다.

### 올바른 설정
```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"
```

이것은 tbaMUD와 직접 관련은 없지만, 프로젝트 셋업 시 자주 발생하는 실수입니다.

---

---

## 11. Socials 파서: Short Form 처리 (social_parser)

### 문제
소셜은 full form(8개 메시지)과 short form(2개 메시지 + `#` 종료)이 혼재합니다.

### 형식
```
# Full form: 헤더 + 8줄 메시지 + 빈줄
smile 8 0
You smile happily.
$n smiles happily.
You smile at $N.
$n beams a smile at $N.
$n smiles at you.
I don't see that person here.
You smile at yourself.
$n smiles at $n self.
                              ← 빈줄로 종료

# Short form: 헤더 + 2줄 + #
ack 0 0
You gasp!
$n gasps!
#                             ← 즉시 종료
```

### 해결
`#`을 만나면 나머지 필드를 빈 문자열로 채우고 종료합니다. `$`는 파일 전체 종료.

---

## 12. Help 파서: 키워드 라인 vs 본문 구분 (help_parser)

### 문제
Help 항목에서 키워드 라인과 본문 시작 사이의 빈 줄 처리가 중요합니다.

### 형식
```
MAGIC MISSILE         ← 키워드 라인
                      ← 빈 줄 (본문의 일부)
Usage: cast 'magic ...'
...

#0                    ← 종료 + 레벨
```

### 핵심
- `#<숫자>` 라인이 종료 마커 (숫자 = min_level)
- `#0`은 레벨 0 (누구나 열람 가능)
- Simoon은 EUC-KR + 다수 .hlp 파일, tbaMUD는 help.hlp 1개에 거의 모든 항목

---

## 13. C 소스 파서: cmd_info[] 추출 (cmd_parser)

### 문제
C 소스의 배열 초기화 구문에서 정규식으로 데이터를 추출해야 합니다.

### tbaMUD cmd_info[] (6필드)
```c
{ "look"    , "l"       , POS_RESTING , do_look     , 0, 0 },
```

### Simoon cmd_info[] (5필드, min_match 없음)
```c
{ "look"   , POS_RESTING , do_look    , 0, 0 },
```

### 해결
```python
_ENTRY_RE = re.compile(
    r'\{\s*"(\w+)"\s*,\s*'  # name
    r'"?(\w*)"?\s*,\s*'     # min_match (있으면)
    r'(POS_\w+|\d+)\s*,\s*' # position
    ...
)
```

`has_min_match` 파라미터로 6필드/5필드를 구분하며, POS_STANDING 등 C 상수를 정수로 변환하는 내부 매핑 테이블(`_POS_MAP`, `_LEVEL_MAP`)을 사용합니다.

### 주의점
- `"RESERVED"` 엔트리 건너뛰기
- `"\n"` 등 특수 이름 무시
- Simoon은 EUC-KR 인코딩

---

## 14. C 소스 파서: spello() 추출 (skill_parser)

### 문제
스킬 메타데이터가 3개 C 파일에 분산되어 있어 결합 파싱이 필요합니다.

### 3단계 파싱

1. **spells.h**: `#define SPELL_MAGIC_MISSILE 32` → ID 매핑
2. **spell_parser.c**: `spello(SPELL_MAGIC_MISSILE, ...)` → 메타데이터
3. **class.c**: `spell_level(SPELL_*, CLASS_*, level)` → 클래스별 레벨

### tbaMUD vs Simoon spello() 차이

| | tbaMUD (10 인자) | Simoon (8 인자) |
|---|---|---|
| 인자 2 | **spell name** (문자열) | max_mana (정수) |
| 마지막 인자 | **wearoff_msg** (문자열) | routines (정수) |
| 이름 소스 | spello() 내 | `han_spells[]` 별도 배열 |

```c
// tbaMUD
spello(SPELL_ARMOR, "armor", 30, 15, 3, POS_FIGHTING,
       TAR_CHAR_ROOM, FALSE, MAG_AFFECTS, "You feel less protected.");

// Simoon — name과 wearoff 없음
spello(SPELL_ARMOR, 30, 15, 3, POS_FIGHTING,
       TAR_CHAR_ROOM, FALSE, MAG_AFFECTS);
```

### Simoon 한글 이름 처리
```c
const char *han_spells[] = {
    "!RESERVED!",   // 0
    "방어",         // 1
    "텔레포트",     // 2
    ...
};
```

인덱스가 spell ID와 일치. 파서가 이 배열을 추출하여 `skill.extensions["korean_name"]`에 저장합니다.

### _constant_to_name() 변환
`SPELL_MAGIC_MISSILE` → `"magic missile"` (접두사 제거 + underscore→space + lowercase)
이것은 tbaMUD에서 스펠 이름이 없는 경우 (ID만 있을 때) 폴백으로 사용합니다.

---

## 요약: 파서 작성시 체크리스트

### Phase 1 (월드 데이터)
- [ ] Tilde 구분자로 끝나는 문자열 처리
- [ ] VNUM 블록 (`#N`) 파싱 + `$~` 종료 처리
- [ ] Asciiflag ↔ 정수 양방향 변환
- [ ] 128-bit 확장 형식 (13필드) vs 기존 형식 자동 감지
- [ ] 마커 이후의 T 라인 (wld: S 이후, mob: E 이후)
- [ ] Shop의 `#N~` 형식
- [ ] TAB 코멘트 분리
- [ ] 가변 필드 수 허용 (zone params 등)
- [ ] 파일 인코딩: UTF-8 + 에러 대체
- [ ] 에러 시 건너뛰기 + 경고 기록

### Phase 2 (확장 데이터)
- [ ] Socials short form (`#` 조기 종료) 처리
- [ ] Help `#<level>` 종료 마커 파싱
- [ ] C 소스 정규식 파싱 (cmd_info[], spello(), spell_level())
- [ ] tbaMUD/Simoon 필드 수 차이 (`has_min_match`, `has_spell_name`)
- [ ] Simoon han_spells[] 한글 이름 추출
- [ ] C 상수 → 정수 매핑 (POS_*, TAR_*, MAG_*, SCMD_*)
- [ ] EUC-KR 인코딩 (Simoon 전용 파서)
