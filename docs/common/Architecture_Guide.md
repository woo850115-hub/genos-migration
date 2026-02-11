# GenOS Migration Tool 아키텍처 가이드

**Version**: 6.0
**Last Updated**: 2026-02-12

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
│   ├── schema.py            # 25 데이터클래스 정의
│   └── validator.py         # UIR 내부 일관성 검증
│
├── adapters/                # 소스 MUD 어댑터
│   ├── __init__.py
│   ├── base.py              # BaseAdapter ABC + AnalysisReport
│   ├── detector.py          # MUD 타입 자동 감지
│   │
│   ├── circlemud/           # CircleMUD/tbaMUD 어댑터 (12 파서)
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
│   │   ├── skill_parser.py  # Skills 파서 — C 소스 (Phase 2)
│   │   └── config_parser.py # Game Config 파서 — C 소스 3파일 (Phase 3)
│   │
│   ├── simoon/              # Simoon 어댑터 (11 파서, 일부 circlemud 재사용)
│   │   ├── __init__.py
│   │   ├── adapter.py       # SimoonAdapter (EUC-KR + 확장 포맷)
│   │   ├── wld_parser.py    # Simoon WLD (3필드)
│   │   ├── obj_parser.py    # Simoon OBJ (3필드)
│   │   ├── mob_parser.py    # Simoon MOB (커스텀 속성)
│   │   ├── zon_parser.py    # Simoon ZON (3필드 params)
│   │   ├── qst_parser.py    # Simoon QST (4 tilde, 7+4 params)
│   │   ├── help_parser.py   # Simoon Help — EUC-KR wrapper (Phase 2)
│   │   ├── cmd_parser.py    # Simoon Commands — EUC-KR + 5필드 (Phase 2)
│   │   └── config_parser.py # Simoon Config — circlemud 재사용 + titles 파서 (Phase 3)
│   │
│   ├── threeeyes/           # 3eyes 어댑터 (8 파서, 바이너리 C 구조체)
│   │   ├── __init__.py
│   │   ├── adapter.py       # ThreeEyesAdapter (바이너리 파싱 오케스트레이터)
│   │   ├── binary_utils.py  # struct 읽기, EUC-KR 문자열, 플래그 변환
│   │   ├── constants.py     # 플래그/타입/클래스/종족/스펠 매핑
│   │   ├── obj_parser.py    # 352-byte object 바이너리 파서
│   │   ├── mob_parser.py    # 1184-byte creature 바이너리 파서
│   │   ├── room_parser.py   # 480-byte + 가변길이 room 바이너리 파서
│   │   ├── help_parser.py   # EUC-KR 텍스트 도움말 파서
│   │   ├── talk_parser.py   # 몬스터 대화/설명 텍스트 파서
│   │   └── config_parser.py # 3eyes Config — global.c 배열 파싱 (Phase 3)
│   │
│   └── lpmud/               # LP-MUD/FluffOS 어댑터 (9 파서, LPC 소스 코드)
│       ├── __init__.py
│       ├── adapter.py       # LPMudAdapter (LPC 파싱 오케스트레이터)
│       ├── lpc_parser.py    # LPC 코드 파싱 유틸 (14개 함수)
│       ├── vnum_generator.py # 파일 경로 → SHA-256 VNUM 생성
│       ├── room_parser.py   # LIB_ROOM 파싱 (2-패스 출구 해결)
│       ├── mob_parser.py    # LIB_MONSTER 파싱 (randomStat 레벨)
│       ├── obj_parser.py    # LIB_WEAPON/ARMOR/ITEM 파싱
│       ├── class_parser.py  # 직업.h JobData 매핑 파싱 (14 직업)
│       ├── skill_parser.py  # 기술.h SkillData 매핑 파싱 (51 기술)
│       ├── help_parser.py   # .help 파일 파싱
│       ├── command_parser.py # getCMD() 명령어 파싱
│       └── config_parser.py # 세팅.h + woong.cfg + 전투.h + monster.c 공식
│
└── compiler/                # UIR → 타겟 변환
    ├── __init__.py
    ├── compiler.py              # GenosCompiler (출력 오케스트레이터)
    ├── db_generator.py          # PostgreSQL DDL(21 테이블) + INSERT 생성
    ├── lua_generator.py         # Lua 스크립트 생성 (6종류)
    └── korean_nlp_generator.py  # 한국어 NLP Lua 생성 (Phase 4: korean_nlp.lua + korean_commands.lua)
```

---

## 데이터 흐름

### 1단계: 감지 (Detection)

```
detector.py (_ADAPTER_ORDER 우선순위)
  ├─ LPMudAdapter.detect()       ← 가장 구체적 (bin/driver + lib/구조/ + inherit LIB_)
  │   └─ bin/driver OR bin/fluffos* + lib/구조/ OR lib/삽입파일/ + .c에 inherit LIB_
  ├─ ThreeEyesAdapter.detect()
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
  │ Phase 3 — 게임 설정/시스템 테이블 (src/config.c, class.c, constants.c)
  ├─ config_parser.parse_game_config()       →  list[GameConfig]           (54항목)
  ├─ config_parser.parse_exp_table()         →  list[ExperienceEntry]      (128항목)
  ├─ config_parser.parse_thac0_table()       →  list[ThacOEntry]           (140항목)
  ├─ config_parser.parse_saving_throws()     →  list[SavingThrowEntry]     (870항목)
  ├─ config_parser.parse_level_titles()      →  list[LevelTitle]           (204항목)
  ├─ config_parser.parse_attribute_modifiers()→  list[AttributeModifier]   (161항목)
  ├─ config_parser.parse_practice_params()   →  list[PracticeParams]       (4항목)
  │
  └─ 조합 → UIR 객체

SimoonAdapter.parse()
  │ (위와 동일 구조, EUC-KR 인코딩 + Simoon 포맷 차이)
  │ 추가: _default_races() → list[Race] (5종족 하드코딩)
  │ 추가: _simoon_classes() → list[CharacterClass] (7클래스)
  │
  │ Phase 3 — 게임 설정/시스템 테이블 (src/config.c, class.c, constants.c)
  ├─ config_parser.parse_game_config()       →  list[GameConfig]           (36항목)
  ├─ config_parser.parse_simoon_titles()     →  tuple[list[LevelTitle],    (628칭호)
  │                                                  list[ExperienceEntry]] (314경험치)
  ├─ config_parser.parse_attribute_modifiers()→  list[AttributeModifier]   (168항목)
  ├─ config_parser.parse_practice_params()   →  list[PracticeParams]       (7항목)
  ├─ config_parser.parse_train_params()      →  PracticeParams.extensions 머지
  │
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
  │ Phase 3 — 게임 설정/시스템 테이블 (src/global.c)
  ├─ config_parser.parse_thac0_table()        →  list[ThacOEntry]          (160항목)
  ├─ config_parser.parse_exp_table()          →  list[ExperienceEntry]     (203항목)
  ├─ config_parser.parse_bonus_table()        →  list[AttributeModifier]   (160항목)
  ├─ config_parser.parse_class_stats()        →  CharacterClass.extensions 머지
  ├─ config_parser.parse_level_cycle()        →  uir.extensions["level_cycle"]
  │
  │ 하드코딩 데이터
  ├─ _threeeyes_classes()                      →  list[CharacterClass] (8클래스)
  ├─ _threeeyes_races()                        →  list[Race] (8종족)
  ├─ _threeeyes_spells()                       →  list[Skill] (63스펠)
  │
  └─ 조합 → UIR 객체

LPMudAdapter.parse()    ★ LPC 소스 코드 파싱 (regex 기반 setXxx() 추출)
  │
  │ Phase 1 — 헤더 데이터 (lib/삽입파일/)
  ├─ class_parser.parse_classes(직업.h)         →  list[CharacterClass] (14직업)
  ├─ skill_parser.parse_skills(기술.h)          →  list[Skill] (51기술)
  │
  │ Phase 2 — 월드 데이터 (lib/방/, lib/물체/)
  ├─ room_parser.parse_all_rooms()              →  list[Room] (17,590방)
  │   └─ 2-패스: 1패스(파싱+경로수집), 2패스(VNUM 해결)
  ├─ mob_parser.parse_all_monsters()            →  list[Monster] (947몬스터)
  │   └─ lib/방/*/mob/*.c + lib/물체/ 중 inherit LIB_MONSTER
  ├─ obj_parser.parse_all_items()               →  list[Item] (969아이템)
  │   └─ lib/물체/*.c + lib/방/*/obj/*.c
  │
  │ Phase 3 — 보조 데이터
  ├─ help_parser.parse_all_help(도움말/)         →  list[HelpEntry] (72항목)
  ├─ command_parser.parse_all_commands(명령어/)  →  list[Command] (51항목)
  │
  │ Phase 4 — 게임 설정 (세팅.h + woong.cfg + 전투.h + monster.c)
  ├─ config_parser.parse_settings_header()      →  list[GameConfig] (설정)
  ├─ config_parser.parse_driver_config()        →  list[GameConfig] (드라이버)
  ├─ config_parser.parse_combat_header()        →  list[GameConfig] (전투상수)
  ├─ config_parser.parse_stat_formulas()        →  list[GameConfig] (공식)
  │
  │ 추론 데이터
  ├─ _infer_zones()                             →  list[Zone] (122존, 디렉토리 기반)
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
  ├─ db_generator.generate_ddl()              →  sql/schema.sql (21 테이블)
  ├─ db_generator.generate_seed_data()        →  sql/seed_data.sql
  ├─ lua_generator.generate_combat_lua()      →  lua/combat.lua
  ├─ lua_generator.generate_class_lua()       →  lua/classes.lua
  ├─ lua_generator.generate_trigger_lua()     →  lua/triggers.lua
  ├─ lua_generator.generate_config_lua()      →  lua/config.lua          (Phase 3)
  ├─ lua_generator.generate_exp_table_lua()   →  lua/exp_tables.lua      (Phase 3)
  ├─ lua_generator.generate_stat_tables_lua() →  lua/stat_tables.lua     (Phase 3)
  ├─ korean_nlp_generator.generate_korean_nlp_lua()      →  lua/korean_nlp.lua       (Phase 4, 항상)
  └─ korean_nlp_generator.generate_korean_commands_lua() →  lua/korean_commands.lua  (Phase 4, 항상)
```

**SQL 테이블 목록** (Phase 1 + Phase 2 + Phase 3):
```
Phase 1: rooms, items, monsters, classes, zones, shops, triggers, quests
Phase 2: socials, help_entries, commands, skills, races
Phase 3: game_configs, experience_table, thac0_table, saving_throws,
         level_titles, attribute_modifiers, practice_params
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

### 1.6. Phase 3: 게임 설정/시스템 테이블

Phase 3는 C 소스 코드에서 게임 밸런스/설정 데이터를 추출합니다:
- **config.c**: 게임 설정 변수 (~40개, `int/bool/room_vnum` 타입)
- **class.c**: 경험치 테이블, THAC0, 세이빙 스로우, 레벨 칭호, 연습 파라미터
- **constants.c**: 능력치 보정 테이블 (str_app, dex_app, con_app 등 6종)
- **global.c** (3eyes): thaco_list, level_exp, bonus, class_stats, level_cycle 배열

핵심 설계 결정:
- **GameConfig은 key-value 구조**: 설정이 이질적(int/bool/vnum/str)이므로 유연한 구조
- **Flat entry 패턴**: ExperienceEntry 등은 SQL 행에 직접 매핑
- **class_id=0 = 공유**: 3eyes/Simoon처럼 단일 테이블을 전 클래스가 공유하는 경우
- **Simoon은 CircleMUD 파서 재사용**: encoding 파라미터만 `euc-kr`로 전달
- **triple-nested switch 파싱**: saving_throws 함수의 class→save_type→level 3중 중첩 switch/case 파싱
- **3eyes level_cycle은 extensions**: 다른 소스에 없는 고유 데이터는 `uir.extensions`에 저장

### 1.7. Phase 4: 한국어 자연어순 명령어 체계 (Korean NLP Command System)

Phase 4는 한국어 SOV(주어-목적어-동사) 어순 명령어 파서를 위한 Lua를 생성합니다:
- **korean_nlp.lua**: UTF-8 한글 유틸리티 (받침 검사, 조사 선택/스트리핑, 동사 어간 추출)
- **korean_commands.lua**: 표준 동사 매핑 (~60개) + 방향어 + SOV 파서 + SVO 폴백

핵심 설계 결정:
- **항상 생성**: 조건부가 아님. 영어 소스(tbaMUD)에서도 한국어 명령어 Lua를 생성
- **UIR 스키마 변경 없음**: 한국어 동사 어휘는 GenOS 표준이므로 소스별 데이터가 아닌 컴파일러 내장
- **UTF-8 기반**: Unicode 수학으로 받침 판별 `(cp - 0xAC00) % 28`
- **SOV 우선 + SVO 폴백**: 마지막 토큰부터 동사 탐색, 실패 시 첫 토큰 시도 (기존 MUD 호환)
- **의미역(semantic role) 기반**: 조사에서 target/object/instrument/location/direction 추출
- **UIR 스킬 연동**: `skill.extensions["korean_name"]`이 있으면 `SPELL_NAMES` 테이블에 자동 포함
- **Python 참조 구현**: `korean_nlp_generator.py`에 Lua 로직을 미러링한 Python 함수 포함 → 단위 테스트 가능
- **엔진 분리 예정**: NLP 로직은 향후 엔진 빌트인으로 이동, 마이그레이션 출력은 데이터 테이블만 유지

### 1.8. LP-MUD/FluffOS 어댑터 (LPC 소스 코드 파싱)

10woongi LP-MUD는 기존 3개 어댑터와 근본적으로 다른 데이터 형식입니다:
- **LPC 소스 코드**: 각 엔티티가 개별 `.c` 파일, `setXxx()` 호출로 데이터 정의
- **VNUM 없음**: 파일 경로 SHA-256 해시로 안정적 정수 VNUM 생성 (VnumGenerator)
- **2-패스 출구 해결**: 1패스에서 경로 수집, 2패스에서 VNUM 변환
- **LPC 매핑/배열**: `([ key : value ])`, `({ elem })` 구문을 regex로 파싱

핵심 설계 결정:
- **regex 기반 파싱**: 완전한 LPC 파서 대신 `setXxx()` 패턴만 추출 — 충분하고 빠름
- **inherit 기반 타입 분류**: `inherit LIB_WEAPON` → item_type=5 등으로 엔티티 타입 결정
- **VnumGenerator 충돌 해결**: SHA-256 해시 충돌 시 linear probing으로 자동 해결
- **Zone 추론**: 디렉토리 구조에서 존을 자동 추론 (lib/방/관도/ → 관도 존)
- **백업 디렉토리 무시**: `방0~방5`는 스킵, `방`만 파싱

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
| LPMudAdapter | 9 | LPC 소스 (regex setXxx()) | lpc/room/mob/obj/class/skill/help/cmd + config | EUC-KR, SHA-256 VNUM, 14직업/51기술 |
| ThreeEyesAdapter | 8 | 바이너리 (struct.unpack) + C소스 | obj/mob/room/help/talk + config | EUC-KR, 8클래스/8종족/63스펠 |
| SimoonAdapter | 11 | 텍스트 (줄 단위) + C소스 | wld/obj/mob/zon/qst + shp(공유) + help/cmd/skill + config | EUC-KR, 5종족/7클래스 |
| CircleMudAdapter | 12 | 텍스트 (줄 단위) + C소스 | wld/obj/mob/zon/trg/shp/qst + social/help/cmd/skill + config | tbaMUD 128-bit |

**감지 우선순위**: LPMud > ThreeEyes > Simoon > CircleMud (구체적 → 일반적 순서).
**LP-MUD 특이점**: 데이터 파일이 아닌 LPC 소스 코드 파싱 — VNUM이 없어 파일 경로 해시로 생성, 2-패스 출구 해결 필요.
**LP-MUD config**: 4개 소스 파일 통합 (세팅.h + woong.cfg + 전투.h + monster.c 공식).
**공유 파서**: social_parser, config_parser(일부)는 circlemud 패키지에 구현, Simoon이 encoding 파라미터만 다르게 호출.
**Simoon 래퍼**: help_parser, cmd_parser는 simoon/ 에 thin wrapper로 존재 (EUC-KR + 포맷 차이 대응).
**Simoon config**: circlemud config_parser 재사용 + titles/train_params 고유 파서.
**3eyes config**: global.c의 C 배열 이니셜라이저 직접 파싱 (thaco_list, level_exp, bonus, class_stats, level_cycle).
**3eyes 특이점**: 텍스트 파일이 아닌 바이너리 C 구조체 — 다른 두 어댑터와 완전히 다른 파싱 전략 사용.

### 향후 어댑터 (3개 추가 예정)

| 어댑터 | 대상 | 파싱 방식 | 재사용 | 난이도 |
|--------|------|-----------|--------|--------|
| Muhan13Adapter | muhan13 | 바이너리 (struct offset 재배치) | 3eyes 파일 탐색/존 분류 | 중 |
| MurimAdapter | murim | 바이너리 (3,380B creature) | 없음 (새 struct) | 상 |
| SmaugAdapter | 99hunter | 텍스트 (에리어 파일) + 외부 .dat | 없음 (새 엔진) | 상 |

상세 갭 분석: `docs/audit/gap-analysis.md` 참조.

---

## 성능 특성

| 소스 | 엔티티 수 | parse 시간 | 전체 migrate |
|------|-----------|-----------|-------------|
| tbaMUD | ~23K | ~2초 | ~5초 |
| Simoon | ~10K | ~1초 | ~3초 |
| 3eyes | ~10K | ~2초 | ~4초 |
| 10woongi | ~20K | ~3초 | ~6초 |

출력 크기 비교:
| 소스 | UIR YAML | SQL seed | Lua |
|------|----------|----------|-----|
| tbaMUD | ~40MB | ~17MB | ~1.6MB (8개) |
| 10woongi | ~16MB | ~14MB | ~17KB (5개) |

## 데이터 규모 비교

### 파서 구현 완료 (4개 게임)

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi |
|------|--------|--------|-------|----------|
| Rooms | 12,700 | 6,508 | 7,439 | **17,590** |
| Items | 4,765 | 1,753 | 1,362 | 969 |
| Monsters | 3,705 | 1,374 | 1,394 | 947 |
| Zones | 189 | 128 | 103 | 122 |
| Shops | 334 | 103 | — | — |
| Help | 721 | 2,220 | 116 | 72 |
| Triggers | 1,461 | — | — | — |
| Commands | 275 | 546 | — | 51 |
| Classes | 14 | 7 | 8 | 14 |
| Races | — | 5 | 8 | — |
| Spells/Skills | 65 | 121 | 63 | 51 |
| **Phase 3** | | | | |
| Game Configs | 54 | 36 | — | 98 |
| Exp Table | 128 | 314 | 203 | — |
| THAC0 Table | 140 | — | 160 | — |
| Saving Throws | 870 | — | — | — |
| Level Titles | 204 | 628 | — | — |
| Attr Modifiers | 161 | 168 | 160 | — |
| Practice Params | 4 | 7 | — | — |

### 분석 완료, 파서 미구현 (3개 게임)

| 항목 | muhan13 | murim | 99hunter |
|------|---------|-------|----------|
| 엔진 | Mordor 2.0 | Mordor 2.0 확장 | SMAUG 1.4 |
| Rooms | 3,218 | 미포함* | ~2,750 |
| Items | 907 | ~1,077 | ~1,750 |
| Monsters | 1,049 | ~683 | ~1,750 |
| Zones | 10 | 11(맵) | 53 |
| Help | ~228 | 30 | ~326 |
| Skills | 56 | 126+ | 54 |
| Commands | 350 | ~300 | 488 |
| Classes | 8 | **21** (진급제) | **30** (6+24) |
| Races | 8 | 4 | 8 (+91 NPC) |

\* murim rooms/ 디렉토리 스냅샷 미포함

### 7게임 합계

| 항목 | 합계 |
|------|------|
| Rooms | **~50,000+** |
| Items | **~12,300+** |
| Monsters | **~10,650+** |
| Skills | **~799+** |
| Commands | **~2,415** |

상세 분석: `docs/audit/universal-data-model.md` (런타임 메커닉 포함), `docs/audit/gap-analysis.md` (갭 분석) 참조.
