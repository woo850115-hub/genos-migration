# 10woongi (십웅기) LP-MUD 마이그레이션 리포트

**Version**: 1.0
**Last Updated**: 2026-02-10

---

## 1. 개요

**십웅기 (10woongi)**는 FluffOS 기반 한국어 LP-MUD 무협 게임입니다. 기존 3개 어댑터(CircleMUD, Simoon, 3eyes)와 완전히 다른 **LPC 소스 코드** 형식으로, GenOS 마이그레이션 도구의 4번째 어댑터로 구현되었습니다.

### 게임 특성

| 항목 | 내용 |
|------|------|
| 게임명 | 십웅기 (10woongi) |
| 엔진 | FluffOS (LP-MUD, 한국어 패치) |
| 언어 | LPC (Lars Pensjoe C) |
| 인코딩 | EUC-KR |
| 장르 | 무협 (중국 배경, 문파 시스템) |
| 포트 | 9999 |
| 최대 접속자 | 50 |

### 마이그레이션 결과 요약

| 엔티티 | 수량 |
|--------|------|
| 방 (Rooms) | 17,590 |
| 아이템 (Items) | 969 |
| 몬스터 (Monsters) | 947 |
| 존 (Zones) | 122 |
| 도움말 (Help) | 72 |
| 기술 (Skills) | 51 |
| 명령어 (Commands) | 51 |
| 직업 (Classes) | 14 |
| 게임 설정 (Game Configs) | 98 |
| **총 엔티티** | **19,914** |

### 출력 파일

| 파일 | 크기 | 줄 수 | 설명 |
|------|------|-------|------|
| `sql/schema.sql` | 8 KB | 224 | DDL (21 테이블) |
| `sql/seed_data.sql` | 14 MB | 21,657 | INSERT 문 |
| `lua/classes.lua` | 3.2 KB | 163 | 14개 직업 정의 |
| `lua/combat.lua` | 1.8 KB | 58 | 전투 시스템 |
| `lua/config.lua` | 3.4 KB | 137 | 98개 게임 설정 (11 카테고리) |
| `lua/korean_nlp.lua` | 3.6 KB | 132 | 한국어 NLP 유틸 |
| `lua/korean_commands.lua` | 5.6 KB | 214 | SOV 명령어 파서 |
| `uir.yaml` | 16 MB | 575,439 | UIR 중간 표현 |

---

## 2. 소스 형식 비교

10woongi는 기존 3개 소스와 근본적으로 다른 데이터 형식을 사용합니다.

| | CircleMUD/tbaMUD | Simoon | 3eyes | **10woongi** |
|---|---|---|---|---|
| 데이터 형식 | 텍스트 파일 | 텍스트 파일 | 바이너리 C 구조체 | **LPC 소스 코드** |
| 파일 구조 | .wld/.obj/.mob | .wld/.obj/.mob | rooms/r{nn} | **개별 .c 파일** |
| VNUM 체계 | 파일 내 명시 | 파일 내 명시 | 배열 인덱스 | **파일 경로 SHA-256 해시** |
| 인코딩 | ASCII | EUC-KR | EUC-KR | **EUC-KR** |
| 파싱 방식 | 줄 단위 상태 머신 | 줄 단위 상태 머신 | struct.unpack | **regex 기반 setXxx() 추출** |
| 엔티티 정의 | `#vnum` + 데이터 블록 | `#vnum` + 데이터 블록 | 고정 크기 레코드 | **`inherit LIB_XXX` + `setXxx()` 호출** |

### LPC 파일 형식 예시

```c
// lib/방/관도/hwab0324.c — 방 파일
inherit LIB_ROOM;

void create() {
    setShort("대기실");
    setLong("강호로 나가기 전 자신의 장비를 점검하는 곳이다.");
    setExits(([ "북" : DIR_DOMAIN "/관도/hwab0325",
                "남" : DIR_DOMAIN "/관도/hwab0323" ]));
    setRoomAttr(1);
}
```

```c
// lib/방/곤륜산/mob/곰.c — 몬스터 파일
inherit LIB_MONSTER;

void create() {
    setName("곰");
    setID(({"곰"}));
    setShort("큰 곰이 으르렁거리고 있다.");
    setGender("동물");
    randomStat(80);
    setupBody();
}
```

---

## 3. VNUM 생성 시스템

LP-MUD은 VNUM이 없으므로 `VnumGenerator`로 파일 경로에서 안정적 정수 ID를 생성합니다.

### 알고리즘

```python
# 1. 경로 정규화: .c 확장자 제거, 선행 / 제거
# 2. SHA-256 해시 → 상위 31비트 정수
# 3. 충돌 시 linear probing으로 자동 해결
vnum = int.from_bytes(sha256(normalized_path.encode()).digest()[:4]) >> 1
```

### 특성
- **결정적**: 같은 경로 → 항상 같은 VNUM
- **충돌 해결**: 해시 충돌 시 +1씩 증가하며 빈 VNUM 탐색
- **Zone ID**: 디렉토리 경로의 해시 // 100
- **역매핑**: VNUM → 원본 경로 역추적 가능 (디버깅용)

---

## 4. 디렉토리 구조

```
/home/genos/workspace/10woongi/
├── bin/
│   ├── driver                    # FluffOS 드라이버 바이너리
│   ├── fluffos-han-fin-220401    # 한국어 패치 드라이버
│   └── woong.cfg                 # 드라이버 설정 (십웅기, 포트 9999)
│
└── lib/
    ├── 방/                        # 방 파일 (56개 하위 디렉토리 = 존)
    │   ├── 관도/                  #   ├── hwab*.c (방 파일)
    │   │   ├── mob/              #   ├── mob/*.c (몬스터)
    │   │   └── obj/              #   └── obj/*.c (아이템)
    │   ├── 곤륜산/
    │   ├── 문파/
    │   │   ├── 개방/
    │   │   ├── 무당파/
    │   │   └── ...
    │   └── ...                   #   (56개 존 디렉토리)
    │
    ├── 물체/                      # 전역 아이템 파일 (392개)
    ├── 명령어/플레이어/             # 플레이어 명령어 (51개 .c)
    ├── 도움말/                     # 도움말 파일 (72개 .help)
    │
    ├── 삽입파일/                   # 헤더 파일
    │   ├── 직업.h                 #   14개 직업 정의
    │   ├── 기술.h                 #   51개 기술 정의
    │   ├── 세팅.h                 #   START_ROOM, YEAR_TIME 등
    │   ├── 전투.h                 #   무기/방어구/크리티컬 상수
    │   ├── 구조.h                 #   LIB_* 매크로 정의
    │   └── 디렉토리.h             #   DIR_* 경로 매크로
    │
    └── 구조/                      # 라이브러리 베이스 클래스
        ├── monster.c              #   HP/SP/MP 공식, randomStat()
        ├── room.c
        └── ...
```

### 소스 파일 수

| 분류 | 파일 수 |
|------|---------|
| 방 .c 파일 (mob/obj 제외) | 17,835 |
| 몬스터 .c 파일 (방/*/mob/) | 947 |
| 아이템 .c 파일 (물체/) | 392 |
| 아이템 .c 파일 (방/*/obj/) | 702 |
| 명령어 .c 파일 | 51 |
| 도움말 .help 파일 | 72 |
| 존 디렉토리 | 56 |
| **총 소스 파일** | **~20,049** |

---

## 5. 방 (Rooms) 통계

### 총 17,590개 방

방은 `lib/방/` 하위에 개별 `.c` 파일로 존재합니다. `inherit LIB_ROOM` 패턴으로 식별됩니다.

### 섹터 타입 분포

| sector_type | 수 | 비율 | 의미 |
|-------------|---|------|------|
| 0 (실내) | 5,470 | 31.1% | 건물/동굴 내부 |
| 1 (야외) | 12,120 | 68.9% | 야외/도시 |

실내/야외 2가지 타입만 사용합니다. 무협 월드의 특성상 야외가 다수를 차지합니다.

### 존 분포

122개 존으로 분류됩니다. 방 디렉토리 경로에서 자동 추론합니다.

대표 존: 감숙관도, 감숙성, 곤륜산, 관도, 대통산, 도적존, 명교입구, 문파(개방/무당파/소림사/...), 장백성, 천산 등

### 출구 (Exits)

`setExits()` 매핑에서 출구를 추출합니다. 10방향 지원:
- 기본 6방향: 북(0), 동(1), 남(2), 서(3), 위(4), 아래(5)
- 확장 4방향: 북동(6), 북서(7), 남동(8), 남서(9)
- 명명 출구: 한국어 이름 ("입구", "다리" 등) → 방향 10+

2-패스 출구 해결:
1. 1패스: 모든 방 파싱, 출구 경로(문자열) 수집
2. 2패스: 출구 경로 → VnumGenerator로 정수 VNUM 변환

### 방 추가 속성

| LPC 호출 | 추출 필드 | 비고 |
|---|---|---|
| `setShort("이름")` | name | |
| `setLong("설명")` | description | |
| `setExits(([ ... ]))` | exits | 2-패스 VNUM 해결 |
| `setRoomAttr(N)` | sector_type | 0=야외, 1=실내 |
| `setOutSide()` | sector_type=0 | 야외 마커 |
| `setMp(N)` | extensions["movement_cost"] | 이동 비용 |
| `setRoomInventory(...)` | extensions["room_inventory"] | 방 내 아이템 |
| `setLimitMob(...)` | extensions["limit_mob"] | 확률 스폰 몬스터 |
| `setProp("k", v)` | extensions | 커스텀 속성 |

---

## 6. 아이템 (Items) 통계

### 총 969개 아이템

아이템은 `lib/물체/` (전역) + `lib/방/*/obj/` (존별)에 분포합니다.

### 아이템 타입 분포

| item_type | 수 | 비율 | 의미 | inherit 타입 |
|-----------|---|------|------|---|
| 9 (ARMOR) | 372 | 38.4% | 방어구 | LIB_ARMOR |
| 12 (OTHER) | 288 | 29.7% | 기타 아이템 | LIB_ITEM |
| 5 (WEAPON) | 246 | 25.4% | 무기 | LIB_WEAPON, LIB_AMGI |
| 19 (FOOD) | 63 | 6.5% | 음식 | LIB_FOOD |

### inherit 타입 → item_type 매핑

```python
INHERIT_TO_ITEM_TYPE = {
    "LIB_WEAPON": 5,    # WEAPON
    "LIB_ARMOR":  9,    # ARMOR
    "LIB_FOOD":   19,   # FOOD
    "LIB_DRINK":  17,   # DRINKCON
    "LIB_ITEM":   12,   # OTHER
    "LIB_TORCH":  1,    # LIGHT
    "LIB_AMGI":   5,    # 암기 (투척 무기) → WEAPON
}
```

### 무기 시스템

10woongi의 무기는 두 가지 데미지 유형을 가집니다:

| 호출 | 의미 |
|------|------|
| `setWeapon(N)` | 체력 기반 데미지 (values[1]) |
| `setSpWeapon(N)` | 내력 기반 데미지 (values[2]) |

### 방어구 슬롯 (22종)

`전투.h`에 정의된 22개 방어구 슬롯:
```
HELMET(1), EARRING(2), PENDANT(3), BODY_ARMOR(4), BELT(5),
ARM_ARMOR(6), GAUNTLET(7), ARMLET(8), RING(9), LEG_ARMOR(10),
SHOES(11), EARRING2(12), RING2-10(13-21), ARMLET2(22)
```

특이사항: 반지만 9개 슬롯(RING~RING10)을 차지합니다.

---

## 7. 몬스터 (Monsters) 통계

### 총 947개 몬스터

몬스터는 `lib/방/*/mob/` 디렉토리에 존재합니다. `inherit LIB_MONSTER` 패턴으로 식별됩니다.

### 스탯 시스템

10woongi는 **6개 능력치** 기반입니다:

| 스탯 | 한국어 | 역할 |
|------|--------|------|
| 힘 | 힘 | 물리 공격력 |
| 민첩 | 민첩 | MP, 회피 |
| 지혜 | 지혜 | SP 보조 |
| 기골 | 기골 | HP |
| 내공 | 내공 | SP 주요 |
| 투지 | 투지 | 전투 의지 |

### 레벨 → 스탯 생성 (`randomStat`)

대부분의 몬스터는 `randomStat(N)`으로 레벨에서 자동 스탯 생성:

```
stat = (level - level/10) + random(level/5)
ArmorClass = level / 4
WeaponClass = level / 4
```

### 몬스터 추가 속성

| LPC 호출 | UIR 필드 |
|---|---|
| `setName("곰")` | short_description |
| `setID(({"곰"}))` | keywords |
| `setGender("남자"/"여자"/"동물")` | sex (1/2/0) |
| `randomStat(N)` | level = N |
| `setStat("힘", N)` | extensions["stats"] |
| `setAggresive()` / `setAggresiveMunpa("파")` | action_flags |
| `setMunpa("무당파")` | extensions["faction"] |
| `setWander(N)` | extensions["wander_prob"] |
| `setChat("대화") / setChatChance(N)` | extensions["chat"] |
| `cloneItem("경로")` | extensions["inventory"] |
| `setBasicAttackMessage(N)` | extensions["attack_type"] |

### 성별 분포

```python
GENDER_MAP = {"남자": 1, "여자": 2, "동물": 0}
```

---

## 8. 직업 (Classes) 시스템

### 14개 직업

10woongi의 직업은 `lib/삽입파일/직업.h`의 `JobData` 매핑 배열에 정의됩니다.

| ID | 직업명 | 계열 | HP 증가 |
|----|--------|------|---------|
| 1 | 투사 | 전사 기본 | 6~26 |
| 2 | 전사 | 전사 중급 | 10~30 |
| 3 | 기사 | 전사 상급 | 12~32 |
| 4 | 상급기사 | 전사 최고 | 10~40 |
| 5 | 신관기사 | 성직/전사 하이브리드 | 12~32 |
| 6 | 사제 | 성직 기본 | 6~26 |
| 7 | 성직자 | 성직 중급 | 10~30 |
| 8 | 아바타 | 성직 최고 | 12~52 |
| 9 | 도둑 | 도적 기본 | 6~26 |
| 10 | 사냥꾼 | 도적 중급 | 10~30 |
| 11 | 암살자 | 도적 최고 | 10~40 |
| 12 | 마술사 | 마법 기본 | 6~26 |
| 13 | 마법사 | 마법 중급 | 10~30 |
| 14 | 시공술사 | 마법 최고 | 12~52 |

### 직업 진급 트리

```
전사 계열: 투사 → 전사 → 기사 → 상급기사
성직 계열: 사제 → 성직자 → 아바타
             └→ 신관기사 (전사/성직 하이브리드)
도적 계열: 도둑 → 사냥꾼 → 암살자
마법 계열: 마술사 → 마법사 → 시공술사
```

### 직업 데이터 필드

`직업.h`에서 추출되는 필드:
- **선행능력**: 6개 스탯 최소 요구치
- **주요능력**: 6개 스탯 가중치
- **기본유닛/증가유닛/증가멈춤**: HP 성장 범위
- **직결직업**: 바로 진급 가능한 직업
- **관계직업**: 관련된 직업 목록
- **선행직업**: 진급 전 필수 직업

---

## 9. 기술 (Skills) 시스템

### 51개 기술

`lib/삽입파일/기술.h`의 `SkillData` 배열에서 추출됩니다.

### 기술 분류

| 계열 | 기술 예시 | 수 |
|------|-----------|---|
| 방어 | 패리L1~L3, 방패방어L1, 절대방어L1 | 6 |
| 전투 | 카운터L1~L2, 연타L1, 파이널어택L1, 크리티컬L1 | 5 |
| 전술 | 전술L1~L2, 집중L1~L2, 양손무장L1 | 5 |
| 치유 | 치료L1~L3, 기도L1~L3, 부활L1 | 7 |
| 은밀 | 훔치기L1, 스텔스L1, 도주술L1, 백스탭L1~L2 | 5 |
| 마법방어 | 마법방어L1~L3, 멘탈피스L1~L3, 텔레실드L1 | 7 |
| 공격 마법 | 매직미셜L1, 파이어볼L1, 라이트닝볼트L1, 아이스스톰L1 | 4 |
| 유틸 마법 | 인첸트L1, 디멘젼도어L1, 헤이스트L1, 소환L1, 귀환L1 | 5 |
| 디버프 | 현혹L1, 사일런스L1, 스탑L1 | 3 |
| 기타 | 요리L1, 일루젼소드L1, 파이어싱L1, 홀리실드L1, 홀리워드L1 | 4 |

### 기술 데이터 필드

- **기술명**: 한국어 이름 (korean_nlp의 SPELL_NAMES에 자동 포함)
- **최대**: 해당 기술의 최대 레벨
- **단위**: 수련에 필요한 포인트
- **직업**: 습득 가능 직업 (다중 가능: "기사&사냥꾼", "모두")
- **레벨**: 습득 최소 레벨

---

## 10. 게임 설정 (Game Configs) — 98개

### 4개 소스 파일에서 추출

#### 10.1 세팅.h — 기본 설정

| 키 | 값 | 타입 |
|----|---|------|
| START_ROOM | 장백성/마을광장 | room_vnum |
| NOVICE_ROOM | 초보지역/선택의방 | room_vnum |
| FREEZER_ROOM | 냉동실 | room_vnum |
| REVITAL_ROOM | 파르티타/병원 | room_vnum |
| YEAR_TIME | 86400 | int |

#### 10.2 woong.cfg — 드라이버 설정

| 카테고리 | 항목 수 | 대표 값 |
|----------|---------|---------|
| game | 12 | name: 십웅기, time to reset: 900 |
| limits | 19 | maximum users: 50, max array: 15000 |
| paths | 9 | mudlib: ../lib, log: /기록 |
| port | 2 | address server port: 2994 |

#### 10.3 전투.h — 전투 상수

| 카테고리 | 항목 수 | 내용 |
|----------|---------|------|
| weapon_size | 5 | TINY(1)~HUGE(5) |
| damage_type | 5 | NONE(0), PIECING(1), SLASH(2), BLUDGE(3), SHOOT(4) |
| armor_slot | 23 | HELMET(1)~MAX_ARMOR_NUM(22) |
| critical_type | 8 | HIT_SELF(1)~KILL(8) |
| unbalanced_type | 3 | SHIELD/PARRY/TWO_HAND |

#### 10.4 monster.c — 스탯 공식 (8개)

```
sigma_formula   = sum(1..n-1), cap at 150 then linear
hp_formula      = hp = 80 + 6 * (sigma(기골) / 30); defense_type: x2, attack_type: x4
sp_formula      = sp = 80 + ((sigma(내공)*2 + sigma(지혜)) / 30)
mp_formula      = mp = 50 + (sigma(민첩) / 15)
random_stat     = stat = (level - level/10) + random(level/5)
adj_exp         = exp = ((avg_stat^2) / 12) * adjust
heal_normal     = hp: 8%, sp: 9%, mp: 13% per tick
heal_fast       = hp: 16%, sp: 18%, mp: 26% per tick
```

---

## 11. 도움말 (Help) — 72개

`lib/도움말/*.help` 파일에서 추출됩니다.

- 파일명(확장자 제외) → keywords
- 파일 내용 → text (색상 코드 `!C`, `!O`, `!RR` 제거)
- 인코딩: EUC-KR → UTF-8 변환

---

## 12. 명령어 (Commands) — 51개

`lib/명령어/플레이어/*.c` 파일에서 추출됩니다.

각 명령어 파일은 `getCMD()` 함수에서 명령어 이름과 별칭을 반환합니다:

```c
string *getCMD() { return ({"때려", "때리"}); }
```

- 첫 번째 요소 → primary name
- 나머지 → extensions["aliases"]
- 파일명 → handler

---

## 13. 어댑터 구현 상세

### LPMudAdapter (9개 파서)

| 파서 | 소스 | 출력 | 비고 |
|------|------|------|------|
| lpc_parser | (유틸) | — | LPC 코드 파싱 핵심 (14개 함수) |
| vnum_generator | (유틸) | — | SHA-256 해시 VNUM 생성 |
| room_parser | lib/방/**/*.c | Room | 2-패스 출구 해결 |
| mob_parser | lib/방/*/mob/*.c | Monster | randomStat 레벨 추출 |
| obj_parser | lib/물체/*.c + lib/방/*/obj/*.c | Item | inherit 타입으로 분류 |
| class_parser | lib/삽입파일/직업.h | CharacterClass | JobData 매핑 파싱 |
| skill_parser | lib/삽입파일/기술.h | Skill | SkillData 매핑 파싱 |
| help_parser | lib/도움말/*.help | HelpEntry | 색상 코드 제거 |
| command_parser | lib/명령어/플레이어/*.c | Command | getCMD() 추출 |
| config_parser | 세팅.h + woong.cfg + 전투.h + monster.c | GameConfig | 4개 소스 통합 |

### 감지 기준

```
1. bin/driver 또는 bin/fluffos* 존재
2. lib/구조/ 또는 lib/삽입파일/ 디렉토리 존재
3. .c 파일에서 'inherit LIB_' 패턴 발견
```

### LPC 파싱 핵심 함수

| 함수 | 역할 |
|------|------|
| `read_lpc_file()` | EUC-KR 디코딩 + 주석 제거 |
| `extract_inherit()` | `inherit LIB_ROOM;` → `"LIB_ROOM"` |
| `extract_string_call()` | `setShort("대기실")` → `"대기실"` |
| `extract_int_call()` | `setLevel(10)` → `10` |
| `extract_mapping()` | `([ "북":"/방/길" ])` → `{"북":"/방/길"}` |
| `extract_array()` | `({ "검" })` → `["검"]` |
| `strip_color_codes()` | `%^CYAN%^텍스트%^RESET%^` → `텍스트` |

---

## 14. 10woongi 고유 시스템

### 14.1 문파 (Faction) 시스템

몬스터와 플레이어가 문파(무당파, 소림사, 개방 등)에 소속됩니다.
- `setMunpa("무당파")` → `extensions["faction"]`
- `setAggresiveMunpa("적대문파")` → 특정 문파에만 공격적

### 14.2 체력/내력 이중 데미지

무기가 두 가지 데미지를 가집니다:
- `setWeapon(N)` — 체력(HP) 기반 물리 데미지
- `setSpWeapon(N)` — 내력(SP) 기반 내공 데미지

### 14.3 방어구 내구도

`setMaxLifeCircle(N)` — 아이템 최대 내구도 (수리 가능 횟수)

### 14.4 확률 스폰

`setLimitMob("몬스터경로", 확률)` — 방에 확률적으로 몬스터 배치

### 14.5 빠른 회복 지역

`setFastHeal()` — 특정 방에서 회복 속도 2배

---

## 15. 검증 이슈

마이그레이션 시 2,183개 검증 경고가 발생합니다 (대부분 경미):

- **빈 이름**: 일부 방에 `setShort()` 미호출 → 빈 문자열 이름
- **댕글링 출구**: 출구 경로가 존재하지 않는 .c 파일을 가리킴
- **VNUM 범위**: SHA-256 해시 기반이므로 전통적 존 범위(bot~top)와 정렬되지 않음

---

## 16. 다른 소스와의 규모 비교

| 항목 | tbaMUD | Simoon | 3eyes | **10woongi** |
|------|--------|--------|-------|-------------|
| Rooms | 12,700 | 6,508 | 7,439 | **17,590** |
| Items | 4,765 | 1,753 | 1,362 | **969** |
| Monsters | 3,705 | 1,374 | 1,394 | **947** |
| Zones | 189 | 128 | 103 | **122** |
| Shops | 334 | 103 | — | **—** |
| Help | 721 | 2,220 | 116 | **72** |
| Classes | 14 | 7 | 8 | **14** |
| Skills | 65 | 121 | 63 | **51** |
| Game Configs | 54 | 36 | — | **98** |
| **총 엔티티** | ~24K | ~11K | ~10K | **~20K** |

10woongi는 **방 수로는 4개 소스 중 최대**(17,590개)이지만, 아이템과 몬스터는 상대적으로 적습니다. LP-MUD 특성상 shop/trigger/quest 시스템이 없어 해당 데이터는 0입니다.

---

## 17. 마이그레이션 주의사항

### 17.1 백업 디렉토리 무시

`lib/방0/` ~ `lib/방5/`는 백업/버전 디렉토리입니다. `ROOM_DIRS = ["방"]`으로 메인 데이터만 파싱합니다.

### 17.2 EUC-KR 인코딩

모든 소스 파일이 EUC-KR입니다. `errors="replace"`로 디코딩 실패 시 대체 문자 처리합니다.

### 17.3 LPC 매크로 미해석

`DIR_DOMAIN`, `DIR_OBJECT` 등 LPC 매크로는 실제 값으로 치환하지 않고 문자열 수준에서 처리합니다. 대부분의 경로 매크로는 정규식으로 충분히 처리 가능합니다.

### 17.4 shop/trigger/quest 미지원

LP-MUD의 상점/트리거/퀘스트 시스템은 LPC 코드 로직에 내장되어 있어 데이터 레벨에서 자동 추출이 어렵습니다. 이 부분은 수동 마이그레이션이 필요합니다.

---

## 18. 테스트

### LP-MUD 어댑터 전용: 94개 테스트

| 테스트 파일 | 테스트 수 | 대상 |
|------------|----------|------|
| test_lpc_parser.py | 37 | LPC 코드 파싱 유틸 |
| test_vnum_generator.py | 8 | VNUM 생성/충돌/정규화 |
| test_class_parser.py | 2 | 직업 파싱 (샘플 + 실데이터) |
| test_skill_parser.py | 2 | 기술 파싱 (샘플 + 실데이터) |
| test_room_parser.py | 5 | 방 파싱/출구 해결 |
| test_mob_parser.py | 3 | 몬스터 파싱 |
| test_obj_parser.py | 3 | 아이템 파싱 |
| test_help_parser.py | 3 | 도움말 파싱 |
| test_command_parser.py | 3 | 명령어 파싱 |
| test_adapter.py | 7 | 어댑터 통합/감지/파싱 |
| test_config_parser.py | 20 | 설정 파싱 (4개 소스) |
| **합계** | **94** | |

### 전체 테스트: 354개 통과

```
Phase 1 (기본):  72 tests
Phase 2 (확장):  41 tests
3eyes:          31 tests
Phase 3 (설정):  47 tests
Phase 4 (NLP):  69 tests
LP-MUD:         94 tests
─────────────────────────
총합:           354 tests
```

---

**문서 버전**: 1.0
**최종 업데이트**: 2026-02-10
**피드백**: 마이그레이션 진행하면서 계속 개선
