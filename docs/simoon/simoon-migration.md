# Simoon (시간의문) Migration Report

## 1. Overview

Simoon(시간의문)은 CircleMUD 3.0 기반 한국 커스텀 MUD이다. 원래 이름은 Tmud(텔머드)로 시작하여 천상대전 → 시간의문 1.1 → 시간의문 1.2로 발전했으며, 약 4년에 걸쳐 개발되었다. 250여 개의 zone을 보유한 대규모 한국어 MUD이다.

- **제작자**: 이성재 (닉네임: 심심해)
- **기반**: CircleMUD 3.0 (신세계 기반 수정)
- **인코딩**: EUC-KR
- **참여자**: 치킨, 심심해, 클로소, 골골차자, 현무, 지혀니, 슈퍼구기 등

### Migration 결과

| 항목 | 수량 | Phase |
|------|------|-------|
| Rooms | 6,508 | 1 |
| Monsters | 1,374 | 1 |
| Items | 1,753 | 1 |
| Zones | 128 | 1 |
| Shops | 103 | 1 |
| Quests | 16 | 1 |
| Triggers | 0 (미사용) | 1 |
| Classes | 7 | 1+2 |
| Socials | 104 | 2 |
| Help | 2,220 | 2 |
| Commands | 550 | 2 |
| Skills | 121 | 2 |
| Races | 5 | 2 |
| Game Configs | 36 | 3 |
| Exp Table | 314 | 3 |
| Level Titles | 628 | 3 |
| Attr Modifiers | 168 | 3 |
| Practice Params | 7 | 3 |

### 출력 파일

| 파일 | 크기 | 줄 수 |
|------|------|-------|
| uir.yaml | ~7 MB | ~320K |
| seed_data.sql | 7.2 MB | 42,876 |
| schema.sql | 8 KB | 224 |
| combat.lua | 1.7 KB | 62 |
| classes.lua | 2.0 KB | 93 |
| config.lua | 1.2 KB | 60 |
| exp_tables.lua | 6.8 KB | 329 |
| stat_tables.lua | 7.4 KB | 192 |

---

## 2. 한글/영문 콘텐츠 비율

| 데이터 | 한글 | 전체 | 비율 |
|--------|------|------|------|
| Rooms | 5,930 | 6,508 | 91.1% |
| Monsters | 1,244 | 1,374 | 90.5% |
| Items | 1,688 | 1,753 | 96.3% |
| Zones | 119 | 128 | 93.0% |

약 9%의 콘텐츠는 CircleMUD stock zone에서 가져온 영문 데이터이다.

---

## 3. 파일 포맷 차이점 (tbaMUD vs Simoon)

### 3-1. 인코딩

- tbaMUD: UTF-8/ASCII
- Simoon: EUC-KR (일부 파일은 CRLF 줄바꿈, 124개 중 22개)

### 3-2. 플래그 형식

- tbaMUD: asciiflag 인코딩 (`a`=bit0, `b`=bit1, ..., `A`=bit26)
- Simoon: **대부분 일반 정수**, 일부 stock zone에서 asciiflag 혼용 (`c`, `d`, `cd` 등)

파서는 정수 파싱 실패 시 asciiflag로 폴백하는 방식으로 처리한다.

### 3-3. WLD (Room) 포맷

```
# tbaMUD (7필드)
zone_num flags sector unlinked previous map_x [map_y]

# Simoon (3필드)
zone_num flags sector
```

### 3-4. OBJ (Item) 타입 라인

```
# tbaMUD (13필드, 128-bit bitvector)
type ef0 ef1 ef2 ef3 wf0 wf1 wf2 wf3 af0 af1 af2 af3

# Simoon (3필드)
type extra_flags wear_flags
```

### 3-5. ZON (Zone) 파라미터 라인

```
# tbaMUD (4-10필드)
bot top lifespan reset_mode [zone_flags ...] [min_level] [max_level]

# Simoon (3필드)
top lifespan reset_mode
```

Simoon에서 `bot`은 `zone_vnum * 100`으로 추론한다.

### 3-6. MOB (Monster) 커스텀 속성

Simoon mob은 E(end) 마커 전에 이름 기반 확장 속성을 가질 수 있다:

```
BareHandAttack: 13
Str: 9
StrAdd: 18
Dex: 8
Int: 6
Wis: 4
Con: 10
Cha: 3
Att1: 100
Att2: 100
Att3: 100
E
```

이 속성들은 `Monster.extensions` dict에 저장된다.

### 3-7. QST (Quest) 포맷

```
# tbaMUD: 5 tilde 문자열 + 8+7 params
name~ keywords~ description~ completion~ quit_message~
flags type target mob value0-3
reward_gold reward_exp reward_obj next prev min_level max_level

# Simoon: 4 tilde 문자열 + 7+4 params (quit_message 없음)
name~ keywords~ description~ completion~
quest_type mob_vnum obj_vnum target_vnum reward_exp next_quest min_level
value0 value1 value2 value3
```

### 3-8. SHP (Shop) 포맷

tbaMUD과 동일한 `CircleMUD v3.0 Shop File~` 형식. EUC-KR 읽기만 다르다.

### 3-9. 트리거 시스템

- tbaMUD: DG Script (1,461개 트리거)
- Simoon: MOBProg 시스템 (실질적 미사용, 파일 존재하나 데이터 없음)

---

## 4. Monster 상세 통계

### 4-1. 레벨 분포

| 레벨대 | 수량 |
|--------|------|
| 0-99 | 677 |
| 100-199 | 286 |
| 200-299 | 173 |
| 300-399 | 174 |
| 400-499 | 35 |
| 500-599 | 10 |
| 600-699 | 1 |
| 700-799 | 3 |
| 900-999 | 3 |
| 1000 | 12 |

- 최소 레벨: 0, 최대 레벨: 1000, 평균: 137.7

### 4-2. 확장 속성 (extensions)

1,374마리 중 112마리(8.2%)가 커스텀 능력치를 가진다.

| 속성 | 보유 수 |
|------|---------|
| Str | 94 |
| Int | 91 |
| Wis | 87 |
| Dex | 86 |
| Con | 86 |
| Cha | 80 |
| Att1 | 62 |
| Att2 | 62 |
| Att3 | 62 |
| StrAdd | 13 |

`Att1`/`Att2`/`Att3`는 Simoon 고유의 추가 공격 관련 속성으로 추정된다.

### 4-3. BareHandAttack 유형

118마리가 BareHandAttack을 사용한다. 가장 흔한 유형은 type 4(bite, 26마리), type 8(claw, 18마리), type 3(slash, 11마리).

---

## 5. Room 상세 통계

### 5-1. Sector 분포

| Sector | 이름 | 수량 |
|--------|------|------|
| 0 | inside | 4,892 (75.2%) |
| 1 | city | 520 |
| 2 | field | 200 |
| 3 | forest | 330 |
| 4 | hills | 126 |
| 5 | mountain | 210 |
| 6 | water_swim | 14 |
| 7 | water_noswim | 77 |
| 8 | flying | 30 |
| 9 | underwater | 78 |
| 10+ | Simoon 확장 | 31 |

전체의 75%가 indoor sector인 것이 특징이다. Simoon은 sector type 10 이상의 커스텀 sector를 사용한다 (총 31개 room).

### 5-2. Room Flag 분포

| Flag (bit) | 이름 | 수량 |
|------------|------|------|
| 0 | dark | 1,017 |
| 2 | nomob | 705 |
| 3 | indoors | 1,790 |
| 4 | peaceful | 301 |
| 5 | soundproof | 109 |
| 6 | notrack | 845 |
| 7 | nomagic | 595 |
| 9 | private | 125 |
| 13 | atrium | 140 |
| 15 | bfs_mark | 632 |
| 29 | (Simoon 확장) | 942 |

bit 17-29 영역에서 Simoon 고유 room flag가 확인된다 (bit 29: 942개 room). 이들의 정확한 의미는 Simoon 소스 코드에서 확인해야 한다.

### 5-3. 연결성

- 총 exit 수: 13,496 (room당 평균 2.07개)
- Extra description 보유 room: 447개

---

## 6. Item 상세 통계

### 6-1. 아이템 타입 분포

| Type | 이름 | 수량 |
|------|------|------|
| 9 | armor | 460 (26.2%) |
| 5 | weapon | 340 (19.4%) |
| 18 | key | 149 |
| 13 | trash | 97 |
| 19 | food | 87 |
| 15 | container | 84 |
| 0 | undefined | 71 |
| 8 | treasure | 57 |
| 17 | drinkcon | 50 |
| 1 | light | 44 |
| 10 | potion | 42 |
| 23 | fountain | 38 |

- armor + weapon이 전체의 45.6%를 차지
- 504개 아이템에 affect가 설정됨
- 448개 아이템에 extra description이 있음
- type 24 이상의 Simoon 커스텀 아이템 타입이 존재 (총 55개)

---

## 7. Zone 목록

128개 zone 중 주요 zone:

| Zone | 이름 | Rooms | Resets |
|------|------|-------|--------|
| 0 | 영원의 골짜기 | 0-99 | 43 |
| 1 | 평화주의자 (DMZ) | 100-199 | 42 |
| 5 | 미드가드시 | 500-599 | 19 |
| 15 | 서바이벌 존 | 1500-1599 | 91 |
| 18 | 쥬라기 공원 | 1800-1899 | 103 |
| 25 | 마법의 성 | 2500-2699 | 329 |
| 28 | 황제의 성 | 2800-2899 | 139 |
| 29 | 미드가드 북부 중심가 | 2900-2999 | 105 |
| 30 | 미드가드 중심가 | 3000-3099 | 325 |
| 54 | 뉴 탈로스 | 5400-5699 | 401 |
| 65 | 난장이 왕국 | 6500-6599 | 118 |
| 81 | 마벨 숲 | 8100-8199 | 275 |
| 91 | 성당 지하 | 9100-9199 | 107 |
| 120 | 로마 | 12000-12099 | 284 |
| 150 | 웰마왕의 성 | 15000-15099 | 135 |
| 186 | 초보자 | 18600-18699 | 56 |
| 237 | 엘프의숲 | 23700-23799 | 129 |
| 239 | 고대동굴 | 23900-23999 | 194 |
| 241 | 광산 | 24100-24199 | 218 |
| 242 | 해변가 | 24200-24299 | 192 |
| 247 | 엘리멘탈 | 24700-24799 | 146 |

reset 명령이 가장 많은 zone은 뉴 탈로스(401개), 마법의 성(329개), 미드가드 중심가(325개)이다. 약 30개 zone은 reset 명령 0개로 비어있거나 미완성 상태이다.

---

## 8. Quest 목록

| # | 이름 | 유형 | 대상 | 보상 EXP | 최소 레벨 |
|---|------|------|------|----------|-----------|
| 1 | 칼슈타인을 찾아라 | kill(3) | mob 20190 | 100,000 | 20 |
| 2 | 잠자리를 찾아라 | find_room(2) | room 27 | 10,000 | 0 |
| 3 | 제우스를 죽여라 | kill(3) | mob 19999 | 100,000 | 0 |
| 4 | 치료카드 가져와라 | collect(0) | obj 36 | 10,000 | 0 |
| 5 | 치료카드 갖다 줘라 | deliver(5) | obj 36 | 0 | 0 |
| 6 | 후크선장을 죽여라 | deliver(5) | obj 24201 | 100,000 | 10 |
| 7 | 에인션트 드래곤을 잡아라 | kill(3) | mob 23902 | 0 | 10 |
| 8 | 시간의전사를 죽여라 | kill(3) | mob 22355 | 0 | 500 |
| 9 | 드래곤 블레이드를 갖다주어라 | deliver(5) | obj 20190 | 0 | 10 |
| 10 | (미완성) | deliver(5) | - | 0 | 5 |
| 3000 | 열매찾기 | collect(0) | obj 3082 | 100,000 | 0 |
| 18000 | 갯벌을 찾아가시오 | kill(3) | mob 18004 | 30,000 | 2 |
| 18601 | 코끼리 석상이 있는 곳을 찾아가시오 | find_room(1) | room 18631 | 1,000 | 2 |
| 18700 | 비천검을 찾아라 | collect(0) | obj 18625 | 30,000 | 3 |
| 18701 | 코끼리 석상을 찾으시오 | find_room(1) | room 18631 | 1,000 | 2 |
| 20300 | 사랑의 마을에서 지령장을 얻어라 | kill(3) | mob 1702 | 100,000 | 10 |

quest type: 0=collect item, 1=find room, 2=find room(alt), 3=kill mob, 5=deliver item

---

## 9. Shop 통계

- 총 103개 shop
- 판매 아이템 총 542개 (shop당 평균 5.3개)
- 최대 아이템 보유 shop: 95개 아이템

---

## 10. MUD Color Code 체계

Simoon은 2종류의 color code를 혼용한다:

### 단문자 코드 (`&x` 형식, CircleMUD 표준)

| 코드 | 의미 | 사용 횟수 |
|------|------|-----------|
| `&w` | white (기본) | 5,699 |
| `&W` | bright white | 1,692 |
| `&B` | bright blue | 1,345 |
| `&R` | bright red | 1,291 |
| `&g` | green | 1,070 |
| `&Y` | bright yellow | 878 |
| `&C` | bright cyan | 667 |
| `&b` | blue | 491 |
| `&M` | bright magenta | 482 |
| `&G` | bright green | 460 |
| `&c` | cyan | 417 |
| `&r` | red | 392 |
| `&y` | yellow | 184 |
| `&m` | magenta | 169 |

### 숫자 코드 (`&cNN` 형식, Simoon 확장)

| 코드 | 사용 횟수 |
|------|-----------|
| `&c14` | 276 |
| `&c07` | 149 |
| `&c08` | 84 |
| `&c11` | 81 |
| `&c12` | 48 |
| `&c09` | 34 |
| `&c10` | 31 |

GenOS 마이그레이션 시 이 color code들을 적절한 HTML/ANSI 매핑으로 변환하는 후처리가 필요하다.

---

## 11. Validation 이슈

### Dangling Exit (2건)

- Room 4021: exit direction 5(down) → 존재하지 않는 room 4115
- Room 4052: exit direction 1(east) → 존재하지 않는 room 4100

Zone 41(Moria Level 3)의 room 데이터가 누락된 것으로 보인다.

### Orphan Shop Keeper (4건)

- Shop 19010, 19011, 22250, 6516: keeper mob 187이 존재하지 않음
- Shop 800, 801: keeper mob 1010이 존재하지 않음

이 shop들은 keeper mob이 다른 zone에서 삭제되었거나, mob vnum이 잘못 설정된 것으로 보인다.

---

## 12. Simoon 고유 확장 (Standard CircleMUD 대비)

1. **커스텀 Sector Type**: 10, 13 (31개 room)
2. **커스텀 Room Flag**: bit 17-29 (수백 개 room에 영향)
3. **커스텀 Item Type**: 24-46 (55개 item)
4. **Monster 능력치**: Str/Dex/Int/Wis/Con/Cha + Att1/Att2/Att3
5. **Color Code 확장**: `&cNN` 형식의 숫자 기반 색상 코드
6. **왕국 시스템**: zone 이름에 "왕국"이 들어간 zone이 다수 (플레이어 그룹 소유 영역)
7. **BareHandAttack 확장**: 표준 type 0-14 외에 type 15, 18도 사용

---

## 13. 마이그레이션 시 주의사항

### 인코딩
- 모든 파일은 EUC-KR로 읽어야 한다
- 일부 파일은 CRLF 줄바꿈 (124개 wld 중 22개)
- `errors="replace"` 옵션으로 깨진 문자 대응

### 플래그 혼합 형식
- 대부분의 zone은 plain integer flag를 사용하지만, 영문 stock zone(62, 72, 99번 등)은 asciiflag 문자를 사용
- 파서가 integer 파싱 실패 시 asciiflag로 자동 폴백

### 미완성 콘텐츠
- 약 30개 zone이 reset 명령 0개 (미완성 또는 빈 zone)
- Quest #10은 미완성 상태 (이름 "0", 설명 부실)
- Zone 238의 이름에 "버그있음" 표기

### Color Code 후처리
- 약 18,000회 이상의 color code 사용
- GenOS 출력 포맷에 맞는 변환 테이블 필요

---

## 14. Phase 2: 확장 데이터 마이그레이션

### 14-1. Socials (감정표현)

tbaMUD과 동일한 `lib/misc/socials` 형식. 총 104개.
EUC-KR 인코딩이지만 socials 데이터 자체는 대부분 영문 (CircleMUD stock 데이터).

### 14-2. Help (도움말)

`lib/text/help/` 디렉토리에 20+개의 `.hlp` 파일, `index` 파일 참조.

| 항목 | 수치 |
|------|------|
| .hlp 파일 수 | 20+ |
| 도움말 항목 총 수 | 2,220 |
| 한글 도움말 비율 | ~85% |

tbaMUD(721개)보다 3배 이상 많은 도움말을 보유. 한국어 게임 시스템, 직업, 종족, 기능 설명이 상세하게 작성되어 있다.

### 14-3. Commands (명령어)

`src/interpreter.c`의 `cmd_info[]` 배열에서 추출. **546개** 커맨드 (tbaMUD의 275개 대비 2배).

**tbaMUD과의 차이점**:
- Simoon cmd_info[]는 **5필드** (min_match 없음), tbaMUD는 6필드
- 커스텀 커맨드 다수: 왕국 시스템, 제조 시스템, 한글 커맨드 등

### 14-4. Skills (스킬/스펠)

`src/spell_parser.c`의 `spello()` + `src/class.c`의 `spell_level()` 결합. **79개** 스킬 (tbaMUD의 54개 대비 +25).

**tbaMUD과의 차이점**:
- Simoon `spello()`는 **8 인자** (name, wearoff_msg 없음), tbaMUD는 10 인자
- 한글 스펠 이름은 `han_spells[]` 배열에 별도 정의 → `skill.extensions["korean_name"]`에 저장
- 7개 클래스(기본 4 + DarkMage/Berserker/Summoner)에 대한 `spell_level()` 매핑

### 14-5. Races (종족)

Simoon은 5종족 시스템을 사용한다 (tbaMUD에는 종족 없음):

| id | 이름 | 약어 | 스탯 보정 | 허용 클래스 |
|----|------|------|-----------|------------|
| 0 | 인간 (Human) | Hu | 없음 | 전체 7클래스 |
| 1 | 드워프 (Dwarf) | Dw | str+1, con+1, dex-1 | Warrior, Cleric, Berserker 등 |
| 2 | 엘프 (Elf) | El | int+1, dex+1, con-1 | Magic User, Thief, Summoner 등 |
| 3 | 호빗 (Hobbit) | Ho | dex+2, str-1, con-1 | Thief, Magic User 등 |
| 4 | 하프엘프 (Half-Elf) | HE | int+1, cha+1, str-1 | 대부분 클래스 |

### 14-6. Classes (직업 확장)

Phase 1에서 기본 4클래스였던 것을 Phase 2에서 7클래스로 확장:

| id | 이름 | 약어 | HP 범위 | 비고 |
|----|------|------|---------|------|
| 0 | Magic User | Mu | 3-8 | 기본 |
| 1 | Cleric | Cl | 5-10 | 기본 |
| 2 | Thief | Th | 6-11 | 기본 |
| 3 | Warrior | Wa | 10-15 | 기본 |
| 4 | DarkMage (흑마법사) | DM | 4-9 | Simoon 확장 |
| 5 | Berserker (광전사) | Be | 12-18 | Simoon 확장 |
| 6 | Summoner (소환사) | Su | 3-7 | Simoon 확장 |

### 14-7. Phase 2 출력 파일 변화

Phase 2 추가로 SQL 출력이 확대됨:

| 파일 | Phase 1 | Phase 2 적용 후 |
|------|---------|-----------------|
| schema.sql | 9 테이블 | 14 테이블 (+5) |
| seed_data.sql | ~23K 줄 | ~26K 줄 (+3K) |

추가된 SQL 테이블: `socials`, `help_entries`, `commands`, `skills`, `races`

---

## 15. Phase 3: 시스템 테이블 마이그레이션

### 15-1. Game Config (게임 설정)

`src/config.c`에서 CircleMUD config_parser를 재사용 (encoding="euc-kr"). **36개** 설정 추출.

카테고리별 분포:
- game: 22개 (tunnel_size, level_can_shout 등)
- rent: 7개 (free_rent, auto_save 등)
- room: 6개 (mortal_start_room 등)
- idle: 3개 (idle_void, idle_rent_time 등)
- pk/economy/corpse/port: 각 1-2개

### 15-2. Experience Table + Level Titles

Simoon은 `src/class.c`의 `titles[1][LVL_BULSA+1]` 배열에서 **칭호와 경험치를 동시에 추출**한다. tbaMUD과 달리 단일 테이블(class_id=0)을 전 클래스가 공유.

- **Level Titles**: 628개 (314레벨 × male/female)
- **Experience Table**: 314개 (레벨 0~313)

최대 레벨이 313(LVL_BULSA)으로, tbaMUD(레벨 34)보다 10배 이상 깊은 레벨 시스템.

### 15-3. Attribute Modifiers (능력치 보정)

`src/constants.c`에서 CircleMUD config_parser 재사용 (encoding="euc-kr"). **168개** 항목.

6개 테이블:
- str_app (31항목): tohit, todam, carry_w, wield_w
- dex_app_skill (26항목): p_pocket, p_locks, p_traps, p_sneak, p_hide
- dex_app (26항목): reaction, missile_attack, defensive
- con_app (26항목): hitp, shock
- int_app (26항목): learn
- wis_app (26항목): bonus

### 15-4. Practice Params (연습 파라미터)

`src/class.c`의 `prac_params[4][NUM_CLASSES]` 배열에서 추출. **7개** 클래스.

추가로 `train_params[6][NUM_CLASSES]`에서 스탯 훈련 상한을 추출하여 PracticeParams.extensions에 머지:
- STR_CAP, INT_CAP, WIS_CAP, DEX_CAP, CON_CAP, CHA_CAP

### 15-5. 미지원 항목

- **THAC0 Table**: Simoon에서 주석처리되어 있음 (사용 안 함)
- **Saving Throws**: Simoon에서 주석처리되어 있음

### 15-6. Phase 3 출력 파일 변화

| 파일 | Phase 2 | Phase 3 적용 후 |
|------|---------|-----------------|
| schema.sql | 14 테이블 | 21 테이블 (+7) |
| seed_data.sql | ~26K 줄 | ~43K 줄 (+17K) |
| Lua 스크립트 | 2개 | 5개 (+config, exp_tables, stat_tables) |
