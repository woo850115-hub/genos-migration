# GenOS Migration Tool 아키텍처 가이드

**Version**: 3.0
**Last Updated**: 2026-02-10

---

## 전체 아키텍처

```
                          ┌──────────────────┐
                          │   CLI (cli.py)   │
                          │ analyze / migrate│
                          └────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                     ▼
   ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │   Detector       │  │    Adapter        │  │   Compiler        │
   │ (auto-detect)    │  │ (parse → UIR)     │  │ (UIR → artifacts) │
   └─────────────────┘  └──────────────────┘  └──────────────────┘
                                   │                     │
                                   ▼                     ▼
                          ┌──────────────┐     ┌──────────────────┐
                          │   UIR Schema  │     │ SQL DDL + Seed   │
                          │  (dataclass)  │     │ Lua Scripts      │
                          └──────────────┘     │ UIR YAML/JSON    │
                                               └──────────────────┘
```

---

## 디렉토리 구조

```
src/genos/
├── __init__.py              # 패키지 + 버전
├── cli.py                   # Click CLI (analyze, migrate)
│
├── uir/                     # Universal Intermediate Representation
│   ├── __init__.py
│   ├── schema.py            # 20+ 데이터클래스 정의
│   └── validator.py         # UIR 내부 일관성 검증
│
├── adapters/                # 소스 MUD 어댑터
│   ├── __init__.py
│   ├── base.py              # BaseAdapter ABC + AnalysisReport
│   ├── detector.py          # MUD 타입 자동 감지
│   │
│   ├── circlemud/           # CircleMUD/tbaMUD 어댑터 (11 파서)
│   │   ├── __init__.py
│   │   ├── adapter.py       # CircleMudAdapter (통합 오케스트레이터)
│   │   ├── constants.py     # 상수 매핑 + bitvector 변환
│   │   ├── wld_parser.py    # .wld 파서 (Room)
│   │   ├── obj_parser.py    # .obj 파서 (Item, 128-bit 지원)
│   │   ├── mob_parser.py    # .mob 파서 (Monster, Enhanced)
│   │   ├── zon_parser.py    # .zon 파서 (Zone + reset commands)
│   │   ├── trg_parser.py    # .trg 파서 (DG Script)
│   │   ├── shp_parser.py    # .shp 파서 (Shop, #vnum~ 형식)
│   │   ├── qst_parser.py    # .qst 파서 (Quest)
│   │   ├── social_parser.py # Socials 파서 (Phase 2)
│   │   ├── help_parser.py   # Help 파서 (Phase 2)
│   │   ├── cmd_parser.py    # Commands 파서 — C 소스 (Phase 2)
│   │   └── skill_parser.py  # Skills 파서 — C 소스 (Phase 2)
│   │
│   ├── simoon/              # Simoon 어댑터 (10 파서, 일부 circlemud 재사용)
│   │   ├── __init__.py
│   │   ├── adapter.py       # SimoonAdapter (EUC-KR + 확장 포맷)
│   │   ├── wld_parser.py    # Simoon WLD (3필드)
│   │   ├── obj_parser.py    # Simoon OBJ (3필드)
│   │   ├── mob_parser.py    # Simoon MOB (커스텀 속성)
│   │   ├── zon_parser.py    # Simoon ZON (3필드 params)
│   │   ├── qst_parser.py    # Simoon QST (4 tilde, 7+4 params)
│   │   ├── help_parser.py   # Simoon Help — EUC-KR wrapper (Phase 2)
│   │   └── cmd_parser.py    # Simoon Commands — EUC-KR + 5필드 (Phase 2)
│   │
│   └── threeeyes/           # 3eyes 어댑터 (7 파서, 바이너리 C 구조체)
│       ├── __init__.py
│       ├── adapter.py       # ThreeEyesAdapter (바이너리 파싱 오케스트레이터)
│       ├── binary_utils.py  # struct 읽기, EUC-KR 문자열, 플래그 변환
│       ├── constants.py     # 플래그/타입/클래스/종족/스펠 매핑
│       ├── obj_parser.py    # 352-byte object 바이너리 파서
│       ├── mob_parser.py    # 1184-byte creature 바이너리 파서
│       ├── room_parser.py   # 480-byte + 가변길이 room 바이너리 파서
│       ├── help_parser.py   # EUC-KR 텍스트 도움말 파서
│       └── talk_parser.py   # 몬스터 대화/설명 텍스트 파서
│
└── compiler/                # UIR → 타겟 변환
    ├── __init__.py
    ├── compiler.py          # GenosCompiler (출력 오케스트레이터)
    ├── db_generator.py      # PostgreSQL DDL(14 테이블) + INSERT 생성
    └── lua_generator.py     # Lua 스크립트 생성
```

---

## 데이터 흐름

### 1단계: 감지 (Detection)

```
detector.py (_ADAPTER_ORDER 우선순위)
  ├─ ThreeEyesAdapter.detect()   ← 가장 구체적
  │   └─ rooms/r{nn}/ + objmon/m{nn},o{nn} + 파일 크기가 struct_size의 배수
  ├─ SimoonAdapter.detect()
  │   └─ lib/world/ + EUC-KR .zon 파일 존재 확인
  └─ CircleMudAdapter.detect()
      └─ lib/world/wld/ + lib/world/mob/ 존재 확인
```

### 2단계: 파싱 (Parse)

```
CircleMudAdapter.parse()
  │
  │ Phase 1 — 월드 데이터 (lib/world/)
  ├─ wld_parser.parse_wld_file() × N files  →  list[Room]
  ├─ obj_parser.parse_obj_file() × N files  →  list[Item]
  ├─ mob_parser.parse_mob_file() × N files  →  list[Monster]
  ├─ zon_parser.parse_zon_file() × N files  →  list[Zone]
  ├─ trg_parser.parse_trg_file() × N files  →  list[Trigger]
  ├─ shp_parser.parse_shp_file() × N files  →  list[Shop]
  ├─ qst_parser.parse_qst_file() × N files  →  list[Quest]
  ├─ _default_classes()                      →  list[CharacterClass]
  │
  │ Phase 2 — 확장 데이터 (lib/misc/, lib/text/, src/)
  ├─ social_parser.parse_social_file()       →  list[Social]
  ├─ help_parser.parse_help_dir()            →  list[HelpEntry]
  ├─ cmd_parser.parse_cmd_file()             →  list[Command]
  ├─ skill_parser.parse_skills()             →  list[Skill]
  │
  └─ 조합 → UIR 객체

SimoonAdapter.parse()
  │ (위와 동일 구조, EUC-KR 인코딩 + Simoon 포맷 차이)
  │ 추가: _default_races() → list[Race] (5종족 하드코딩)
  │ 추가: _simoon_classes() → list[CharacterClass] (7클래스)
  └─ 조합 → UIR 객체

ThreeEyesAdapter.parse()    ★ 바이너리 C 구조체 파싱
  │
  │ Phase 1 — 바이너리 월드 데이터
  ├─ obj_parser.parse_all_objects(objmon/)     →  list[Item]
  │   └─ o{nn} 파일: 352-byte 고정 레코드 × ≤100
  ├─ mob_parser.parse_all_monsters(objmon/)    →  list[Monster]
  │   └─ m{nn} 파일: 1184-byte 고정 레코드 × ≤100
  ├─ room_parser.parse_all_rooms(rooms/)       →  list[Room]
  │   └─ r{nn}/r{nnnnn} 파일: 480-byte + 가변길이 (exits/mobs/objs/descs)
  │
  │ Phase 2 — 텍스트 데이터
  ├─ help_parser.parse_help_dir(help/)         →  list[HelpEntry]
  ├─ talk_parser.parse_talk_dir(objmon/talk/)  →  Monster.extensions 머지
  ├─ talk_parser.parse_ddesc_dir(objmon/ddesc/) → Monster.detailed_desc 머지
  │
  │ 하드코딩 데이터
  ├─ _threeeyes_classes()                      →  list[CharacterClass] (8클래스)
  ├─ _threeeyes_races()                        →  list[Race] (8종족)
  ├─ _threeeyes_spells()                       →  list[Skill] (63스펠)
  │
  └─ 조합 → UIR 객체
```

### 3단계: 검증 (Validate)

```
validator.validate_uir(uir)
  ├─ Exit 참조 무결성
  ├─ Trigger 참조 검증
  ├─ Zone 리셋 커맨드 검증
  └─ Shop keeper 검증
```

### 4단계: 컴파일 (Compile)

```
GenosCompiler.compile()
  ├─ db_generator.generate_ddl()         →  sql/schema.sql (14 테이블)
  ├─ db_generator.generate_seed_data()   →  sql/seed_data.sql
  ├─ lua_generator.generate_combat_lua() →  lua/combat.lua
  ├─ lua_generator.generate_class_lua()  →  lua/classes.lua
  └─ lua_generator.generate_trigger_lua()→  lua/triggers.lua
```

**SQL 테이블 목록** (Phase 1 + Phase 2):
```
rooms, items, monsters, classes, zones, shops, triggers, quests,
socials, help_entries, commands, skills, races
```

---

## 핵심 설계 결정

### 1. UIR이 중심이다

모든 데이터는 소스 형식에서 UIR로, UIR에서 타겟 형식으로 변환됩니다. 이렇게 하면:
- 새 소스 추가 = 새 어댑터만 작성 (UIR 변환만 구현)
- 새 타겟 추가 = 새 컴파일러만 작성 (UIR 읽기만 구현)
- N 소스 × M 타겟 = N+M 구현 (N×M이 아님)

### 1.5. Phase 2: 데이터 파일 + C 소스 파싱

Phase 1은 `lib/world/` 하위 데이터 파일만 파싱하지만, Phase 2는 소스 범위를 확장합니다:
- **데이터 파일**: `lib/misc/socials`, `lib/text/help/*.hlp`
- **C 소스 코드**: `src/interpreter.c` (cmd_info[]), `src/spell_parser.c` (spello()), `src/class.c` (spell_level()), `src/spells.h` (#define)

C 소스 파싱은 정규식 기반이며, 완전한 C 파서가 아닌 특정 패턴(배열 초기화, 함수 호출, #define)만 추출합니다. 이 접근은 표준 CircleMUD/tbaMUD 코드에서는 잘 동작하지만, 소스가 크게 수정된 경우 정규식 조정이 필요할 수 있습니다.

### 2. Bitvector → 비트 위치 리스트

소스에서는 정수 비트마스크(`8`, `ae` 등)를 사용하지만, UIR에서는 설정된 비트 위치의 리스트(`[3, 4]`)로 변환합니다. 이유:
- 사람이 읽기 쉬움
- JSON/YAML 직렬화에 자연스러움
- 비트 위치에서 의미를 즉시 조회 가능

### 3. 텍스트 파서는 줄 단위 상태 머신

CircleMUD/Simoon 파서는 `lines[i]`를 순회하며 현재 상태에 따라 다음 동작을 결정합니다.
- `_read_tilde_string()`: `~`까지 여러 줄 읽기 (모든 텍스트 파서 공통)
- 블록 시작은 `#`, `D`, `E`, `A`, `T`, `S` 등의 마커로 식별
- 에러 발생시 해당 엔티티를 건너뛰고 경고 기록

### 3.5. 바이너리 파서는 오프셋 기반

3eyes 파서는 고정 크기 C 구조체를 `struct.unpack_from()`으로 읽습니다.
- **구조체 패딩**: 32-bit Linux natural alignment 규칙 (short=2B, int/ptr=4B 정렬)
- **EUC-KR 문자열**: null-terminated C 문자열을 `read_cstring(data, offset, max_len)`으로 추출
- **플래그 변환**: `flags_to_bit_positions(flag_bytes)` — F_ISSET 매크로 호환
- **가변길이 Room**: 480-byte 고정부 + exits + 재귀적 creature/object + 설명 문자열
- VNUM 계산: `file_index × 100 + record_index`

### 4. 128-bit 자동 감지

obj_parser는 type/flags 라인의 필드 수로 형식을 자동 감지합니다:
- 13 필드 → tbaMUD 128-bit 형식 (wear_flags at index 5)
- 3-4 필드 → 기존 CircleMUD 형식 (wear_flags at index 2)

### 5. DG Script → Lua 변환은 부분적

DG Script의 모든 구문을 Lua로 자동 변환하는 것은 불가능합니다. 현재 전략:
- 단순 패턴 (say, wait, if/else/end) → 직접 변환
- 복잡한 패턴 (%load%, %purge%, eval 등) → `-- TODO:` 주석으로 표시
- 원본 스크립트는 트리거 테이블에 보존

---

## 확장 가이드

### 새 MUD 어댑터 추가

1. `src/genos/adapters/<mudname>/` 디렉토리 생성
2. `adapter.py`에서 `BaseAdapter` 상속, `detect()`/`analyze()`/`parse()` 구현
3. 필요한 파서들 작성
4. `detector.py`의 `_ADAPTER_CLASSES`에 등록

```python
class MyMudAdapter(BaseAdapter):
    def detect(self) -> bool:
        # 소스 디렉토리 구조로 감지
        ...

    def analyze(self) -> AnalysisReport:
        # 빠른 카운팅
        ...

    def parse(self) -> UIR:
        # 전체 파싱 → UIR 변환
        ...
```

### 새 컴파일러 타겟 추가

1. `src/genos/compiler/` 에 새 generator 추가
2. `GenosCompiler.compile()`에서 호출

---

## 어댑터 현황

| 어댑터 | 파서 수 | 파싱 방식 | 주요 파서 | 비고 |
|--------|---------|-----------|-----------|------|
| ThreeEyesAdapter | 7 | 바이너리 (struct.unpack) | obj/mob/room/help/talk | EUC-KR, 8클래스/8종족/63스펠 |
| SimoonAdapter | 10 | 텍스트 (줄 단위) | wld/obj/mob/zon/qst + shp(공유) + help/cmd/skill | EUC-KR, 5종족/7클래스 |
| CircleMudAdapter | 11 | 텍스트 (줄 단위) | wld/obj/mob/zon/trg/shp/qst + social/help/cmd/skill | tbaMUD 128-bit |

**감지 우선순위**: ThreeEyes > Simoon > CircleMud (구체적 → 일반적 순서).
**공유 파서**: social_parser는 circlemud 패키지에 구현, Simoon이 encoding 파라미터만 다르게 호출.
**Simoon 래퍼**: help_parser, cmd_parser는 simoon/ 에 thin wrapper로 존재 (EUC-KR + 포맷 차이 대응).
**3eyes 특이점**: 텍스트 파일이 아닌 바이너리 C 구조체 — 다른 두 어댑터와 완전히 다른 파싱 전략 사용.

---

## 성능 특성

| 소스 | 엔티티 수 | parse 시간 | 전체 migrate |
|------|-----------|-----------|-------------|
| tbaMUD | ~23K | ~2초 | ~5초 |
| Simoon | ~10K | ~1초 | ~3초 |
| 3eyes | ~10K | ~2초 | ~4초 |

tbaMUD 출력 크기 (가장 큰 소스):
- UIR YAML: ~878K lines, ~40MB
- SQL seed: ~91K lines, ~16MB
- Lua triggers: ~1.5MB

## 데이터 규모 비교

| 항목 | tbaMUD | Simoon | 3eyes |
|------|--------|--------|-------|
| Rooms | 12,700 | 6,508 | 7,439 |
| Items | 4,765 | 1,753 | 1,362 |
| Monsters | 3,705 | 1,374 | 1,394 |
| Zones | 189 | 128 | 103 |
| Shops | 334 | 103 | — |
| Help | 721 | 2,220 | 116 |
| Triggers | 1,461 | — | — |
| Classes | 14 | 7 | 8 |
| Races | — | 5 | 8 |
| Spells/Skills | 54 | 79 | 63 |
