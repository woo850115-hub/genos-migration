# GenOS 마이그레이션 통합 갭 분석 v4

> 7개 게임 심층 분석 기반 데이터 모델 비교
> 최종 업데이트: 2026-02-11

---

## 1. 7개 게임 데이터 모델 비교표

### 1.1 엔티티별 고유 속성

#### Room (방)

| 속성 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 기본 (이름/설명/VNUM) | O | O | O | O | O | O | O |
| 출구 (6방향+커스텀) | O | O | O (exit 44B) | O (mapping) | O (exit 44B) | O (exit ~40B) | O (D0-D10) |
| 플래그 (비트맵) | 128-bit (4dword) | int/asciiflag | 64-bit (8B) | stat_* 개별 | 64-bit (8B) | 65종 비트맵 | 128-bit (4×32) |
| 섹터 타입 | O | O | — | — | — | — | O (0-21) |
| 레벨 제한 | — | — | lolevel/hilevel | — | lolevel/hilevel | lolevel/hilevel | — |
| 랜덤 스폰 | reset_commands | reset_commands | random[10] | RandomMonster/Rate | random[10] | random[10] | #RESETS |
| 트리거 | DG Script (T lines) | — | — | — | — | — | mprog (내장) |
| 문(Door) | exit door_flags | exit door_flags | exit flags | mapping Doors | exit flags | exit flags | D lock_flags |
| 트랩 | — | — | trap/trapexit | — | trap/trapexit | trap/trapexit | — |
| 특수 속성 | extra_descriptions | extra_descriptions | special/track | no_sky/sea/fast_heal | special/track | special/track | E (extra desc) |
| Direction 10 | — | — | — | — | — | — | **somewhere** |

#### Item (아이템)

| 속성 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 기본 (이름/설명/키워드) | O | O | O (70+80+60B) | O (setName/ID) | O (name[80]) | O | O (4줄 텍스트) |
| 타입 | item_type (17종) | item_type | type (1B) | inherit계열 (8종) | type (1B) | type (1B) | item_type |
| 무게/가격 | weight/cost/rent | weight/cost/rent | weight/value | Mass/Value | weight/value | weight/value | weight/cost/rent |
| 플래그 | 128-bit bitvector | int/asciiflag | 64-bit flags | setPrevent* 등 | 64-bit flags | 58종 비트맵 | 128-bit (4×32) |
| 착용 위치 | wear_flags (128-bit) | wear_flags | wearflag (1B) | setType (22슬롯) | wearflag (1B, 20슬롯) | wearflag (40슬롯) | wear_flags |
| AC | values[0] | values[0] | armor (1B) | ArmorClass | armor (1B) | armor (1B) | values[0] |
| 데미지 | values[1-2] | values[1-2] | ndice/sdice/pdice | MinDamage/DamageRange | ndice/sdice/pdice | ndice/sdice/pdice | values[1-2] |
| 마법 강화 | — | — | magicpower/realm | upgrade/sp_upgrade | magicpower/realm | obj01-20 인챈트 | A (apply) |
| 내구도 | — | — | shotsmax/shotscur | MaxLifeCircle | shotsmax/shotscur | shotsmax/shotscur | — |
| 스탯 보정 | affects[] | affects[] | adjustment (1B) | setStatUp (6종) | adjustment (1B) | adjustment (1B) | A (apply_type) |
| 메시지 | — | — | use_output | HitMessage/EquipMessage | use_output | use_output | — |
| 소유자 정보 | — | — | — | — | — | **owner+인챈트 140B** | — |
| 레이어 | — | — | — | — | — | — | MAX_LAYERS=8 |

#### Monster (몬스터)

| 속성 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 기본 (이름/설명) | O | O | O (80+80B) | O | O (name[80]) | O (72+78B) | O (4줄 텍스트) |
| 레벨 | O | O | level (1B) | randomStat() | level (1B) | level (long) | level |
| 스탯 | — | — | 5종 (str~pty) | 6종 (힘~투지) | 5종 (str~pty) | **18종** (5+13무술) | **7종** (str~lck) |
| HP/MP | hp_dice 주사위 | hp_dice | hpmax/mpmax | setupBody() | hpmax/mpmax | hpmax/mpmax (long) | hitdice+damdice |
| AC/THAC0 | armor_class/— | armor_class/— | armor/thaco | AC/WeaponClass | armor/thaco | armor/thaco | armor/hitroll |
| 공격력 | damage_dice/damroll | damage_dice/damroll | ndice/sdice/pdice | — (기술 기반) | ndice/sdice/pdice | ndice/sdice/pdice | damdice/damroll |
| 골드/경험치 | gold/experience | gold/experience | gold/experience | Gold/Exp/Fame | gold/experience | gold/experience | gold/exp |
| 행동 플래그 | action_flags (128-bit) | action_flags | flags (64-bit) | setAggresive 등 | flags (64-bit) | **72종** (640-bit) | act_flags (128-bit) |
| 스킬/스펠 | — | — | spells[16] (128-bit) | setSkillData | spells[16] | spells[16] | — (skills.dat) |
| 대화 | — | — | talk 파일 | setChat/ChatChance | talk/rndtalk | talk | — |
| 무기 숙련도 | — | — | proficiency[5] | — | proficiency[5] | **proficiency[50]** | — |
| 마법 영역 | — | — | realm[4] | — | realm[4] | **realm[40]** | — |
| 무공 | — | — | — | — | — | **art[256]** | — |
| 문파/클랜 | — | — | — | setMunpa | — | — | — |
| S/C 타입 | — | — | — | — | — | — | **S(3줄)/C(8줄)** |
| saving_throw | — | — | — | — | — | — | 5종 |
| 종족 | — | — | race (1B) | — | race (1B) | race (1B) | race (91+8) |

#### Skill (스킬/기술)

| 속성 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 수량 | 54 (spello) | 79 (spello) | 63 (spllist) | 367 (LPC) | 56 (MAXSPELL) | 126+ | 54 (skills.dat) |
| 정의 방식 | C함수 spello() | C함수 spello() | C배열 spllist[] | LPC #define | C 소스 | C 소스 | **외부 skills.dat** |
| 마나 비용 | max/min/change | max/min/change | ospell.mp | startSkill() 내부 | 불명 | 불명 | Mana 필드 |
| 타겟 | TAR_* (11종) | TAR_* (11종) | — | 기술별 고유 | — | — | Target 필드 |
| 루틴 | MAG_* (12종) | MAG_* (12종) | 함수 포인터 | skillMain/endSkill | 함수 포인터 | 함수 포인터 | Code (C함수명) |
| 데미지 | spell별 고유 | spell별 고유 | ndice*D(sdice)+pdice | 공식 (스탯*계수) | dice 기반 | dice+스탯보정 | Dammsg 필드 |
| 마법 영역 | — | — | EARTH~WATER (4) | ATTR (#define) | EARTH~WATER (4) | **8계파** | — |
| 숙련도 | — | — | — | 0-100 | — | — | Skill 레벨별 % |
| 습득 레벨 | — | — | spllv | — | — | — | **클래스별 .class** |

---

## 2. 게임별 커버리지 평가

### 2.1 기존 4개 게임 (파서 구현 완료)

| 게임 | 초기 평가 | 심층 분석 후 | 전투메시지+텍스트 추가 시 |
|------|----------|-------------|-------------------------|
| tbaMUD | ~90% | **~92%** | **~97%** |
| Simoon | ~88% | **~90%** | **~96%** |
| 3eyes | ~82% | **~85%** | **~95%** |
| 10woongi | ~65% | **~55%** (하향) | **~92%** |

### 2.2 신규 3개 게임 (파서 미구현)

| 게임 | 엔진 | 파서 존재 | 데이터 분석 커버리지 | 재사용 가능 파서 |
|------|------|----------|-------------------|----------------|
| muhan13 | Mordor 2.0 | 없음 | **~95%** (struct 해석 완료) | 3eyes 참고 (필드 순서 다름) |
| murim | Mordor 2.0 확장 | 없음 | **~90%** (rooms/ 누락) | 없음 (struct 완전 다름) |
| 99hunter | SMAUG 1.4 | 없음 | **~95%** (에리어 포맷 해석 완료) | 없음 (새 엔진) |

### 2.3 10woongi 하향 사유

- 기존 평가: 기술 시스템 "부분 파싱" → 30%로 산정
- 실제: 51개 이름만 추출, 367개 구현 파일 완전 미파싱 → **15%**
- 아이템: LIB_OBJECT 366개 전체 누락, 속성 다수 미파싱 → **50%**
- NPC 특수유형/문파 시스템 **0%** 추가 확인
- 가중 평균으로 ~55%가 정확

### 2.4 3eyes 상향 사유

- creature.speak[] 필드가 **존재하지 않음** 확인 → 파서 정확
- proficiency[5]/realm[4]/spells[16] 기본 추출은 되어 있음
- 명령어 405개, 스펠 63개의 **데이터가 global.c에 존재** 확인 → 추출만 하면 됨

### 2.5 신규 게임 분석 참고사항

- **muhan13**: 3eyes와 struct 크기 동일(1184/352/480)이나 **필드 순서 완전 다름** → 별도 파서 필요
- **murim**: creature 3,380B (+185%), object 492B (+40%) — 무공/내공 시스템 대폭 확장
- **99hunter**: SMAUG 에리어 파일 포맷은 기존 어댑터와 **호환 불가** → SmaugAdapter 신규 필요
- **murim rooms/**: 현재 스냅샷에 없음. 맵 파일 기반으로 수천 개 방 존재 추정

---

## 3. 범용 스키마를 위한 공통 패턴

### 3.1 공통 엔티티 (7게임 모두 존재)

| 엔티티 | 공통 필드 | extensions로 처리 |
|--------|----------|-------------------|
| Room | vnum, name, description, exits | flags, sector, triggers, special, level_range, traps |
| Item | vnum, name, description, type, weight, cost | wear, damage, magic, durability, enchant, layers |
| Monster | vnum, name, description, level, hp, gold, exp | stats, skills, behavior, combat, martial_arts |
| Zone | number, name, reset_commands | lifespan, flags, climate, economy |
| Skill | id, name | mana, target, damage, routines, realm, mastery |
| Command | name, min_level | function, category, position, log_type |
| HelpEntry | keyword, body | category, level |

### 3.2 공통 시스템

| 시스템 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|--------|--------|--------|-------|----------|---------|-------|----------|
| 전투 | messages 파일 | messages (EUC-KR) | 소스 하드코딩 | 기술별 messageRoutine | 소스 하드코딩 | 소스+무공 | skills.dat Dammsg |
| 상점 | .shp (334개) | .shp (103개) | 없음 | merchant/dealer | 없음 | 없음 | #SHOPS 섹션 |
| 퀘스트 | .qst (8개) | .qst (16개) | quests[16] 비트 | player.Quest | quests[16] 비트 | quests[16] 비트 | — |
| 소셜 | socials (104개) | socials (104개) | 없음 | 없음 | action (40개) | 100+ | socials.dat (7개) |
| 클랜/문파 | 없음 | clan 파일 | family[16] | 문파 7개 | family[16] | 문중 16개 | clan 1개 |
| 은행 | — | — | — | banker | **bank.c** | **bank.c** | — |
| 결혼 | — | — | — | marry.c | **결혼 시스템** | **결혼 시스템** | — |
| 게시판 | — | — | board_index | — | **board.c (18개)** | board.c | — |
| 제련 | — | — | — | — | **forge()** | — | — |
| 신(Deity) | — | — | — | — | — | — | **deity 2개** |
| 의회(Council) | — | — | — | — | — | — | **council 2개** |

### 3.3 게임별 고유 시스템

| 게임 | 고유 시스템 |
|------|------------|
| tbaMUD | DG Script 트리거 (1,461개), 128-bit bitvector, .mini 인덱스 |
| Simoon | EUC-KR 한국어 조사 변수 ($j/$g/$d/$C/$v/$D), 5종족/7직업 |
| 3eyes | 바이너리 C struct 포맷, 4개 마법 영역, 5개 무기 숙련도, 환생 시스템 |
| 10woongi | LPC inheritance, SHA-256 VNUM, 6종 스탯, 22개 방어구 슬롯, 문파 경제 |
| muhan13 | creature2 별도 struct, 은행/결혼/제련/전쟁/달돌 시스템, 128비트 확장 플래그 |
| murim | **3,380B creature** (무공/내공), art[256] 무공 배열, 18종 스탯, 8계파 마법, 분신법술, 환생 |
| 99hunter | SMAUG 에리어 파일, Direction 10 (somewhere), 외부 skills.dat/명령어.dat, 신/의회, 8-layer 의복 |

---

## 4. 엔진 계보별 분류

### 4.1 Diku/Merc 계열 (텍스트 기반)

| 게임 | 엔진 | 특이사항 |
|------|------|---------|
| tbaMUD | CircleMUD 3.1 | 원본 표준, DG Script |
| Simoon | CircleMUD 3.0 | 한국어 커스텀 |
| 99hunter | SMAUG 1.4 (Merc 2.1) | 단일 에리어 파일, OLC 내장 |

### 4.2 Mordor 계열 (바이너리 struct)

| 게임 | 엔진 | struct 크기 | 특이사항 |
|------|------|------------|---------|
| 3eyes | Mordor 2.0 | 1184/352/480 | 원본 Mordor |
| muhan13 | Mordor 2.0 | 1184/352/480 (필드 순서 다름) | creature2 추가, 은행/결혼/제련 |
| murim | Mordor 2.0 확장 | **3380/492/~444** | 무공/내공 대폭 확장 |

### 4.3 LP-MUD 계열 (LPC 소스)

| 게임 | 엔진 | 특이사항 |
|------|------|---------|
| 10woongi | FluffOS (LP-MUD) | 개별 .c 파일, setXxx() 패턴 |

---

## 5. 누락 항목 우선순위

### Tier 1: 기존 게임 실행 필수

| # | 게임 | 누락 항목 | 영향 | 데이터 존재 확인 |
|---|------|-----------|------|-----------------|
| 1 | 10woongi | LIB_OBJECT 아이템 (366개) | 비장비 오브젝트 전부 | YES — inherit LIB_OBJECT |
| 2 | 10woongi | 몬스터 전투 속성 (17개 set함수) | 전투 밸런스 | YES — monster.c 982줄 |
| 3 | 10woongi | 아이템 속성 확장 (15개 set함수) | 장비 시스템 | YES — item/weapon/armor.c |
| 4 | 10woongi | NPC 특수유형 (상인/은행/힐러) | 상점/경제 | YES — 구조/ 4파일 |

### Tier 2: 기존 게임 품질 필수

| # | 게임 | 누락 항목 | 영향 | 데이터 존재 확인 |
|---|------|-----------|------|-----------------|
| 5 | ALL | 전투 메시지 파서 | 전투 피드백 텍스트 | YES — messages 파일 |
| 6 | ALL | 텍스트 파일 추출 | 로그인/MOTD/뉴스 | YES — lib/text/ |
| 7 | 10woongi | 기술 구현 데이터 (367파일) | 기술 수치 | YES — lib/기술/ |
| 8 | 10woongi | 문파 데이터 (7개) | 문파 시스템 | YES — 관리자/문파/ |
| 9 | 3eyes | 스펠 데이터 (ospell[26]) | 63개 스펠 효과 | YES — global.c |
| 10 | 3eyes | 명령어 목록 (cmdlist[405]) | 명령어 시스템 | YES — global.c |

### Tier 3: 신규 게임 어댑터

| # | 게임 | 필요 작업 | 난이도 | 비고 |
|---|------|-----------|--------|------|
| 11 | muhan13 | Mordor2Adapter (struct 재배치) | 중 | 3eyes ThreeEyesAdapter 참고 |
| 12 | murim | MurimAdapter (3,380B creature) | 상 | 완전 새 struct 레이아웃 |
| 13 | 99hunter | SmaugAdapter (에리어 파일 파서) | 상 | 새 엔진 계열 |
| 14 | murim | rooms/ 데이터 수집 | — | 현재 스냅샷 누락 |

### Tier 4: 완성도

| # | 게임 | 누락 항목 | 영향 |
|---|------|-----------|------|
| 15 | 10woongi | 문서 → 도움말 (29파일) | 인게임 문서 |
| 16 | 10woongi | 관리자 시스템 | 게시판/순위/날씨 |
| 17 | 3eyes | 게시판 글 (6,692개) | 커뮤니티 |
| 18 | 3eyes | magicpower/magicrealm UIR | 아이템 마법 |
| 19 | tbaMUD | .mini 인덱스 (8개) | 로드 순서 |
| 20 | Simoon | clan 데이터 | 클랜 시스템 |
| 21 | muhan13 | creature2 파서 | 확장 플레이어 데이터 |
| 22 | murim | mukong/ 무공 커리큘럼 파서 | 종족별 무공 트리 |
| 23 | 99hunter | 신/의회/클랜 데이터 | 조직 시스템 |

---

## 6. 예상 커버리지 (구현 후)

### 6.1 기존 게임

| 게임 | 현재 | Tier 1 후 | Tier 2 후 | Tier 4 후 |
|------|------|----------|----------|----------|
| tbaMUD | ~92% | ~92% | **~97%** | ~98% |
| Simoon | ~90% | ~90% | **~96%** | ~97% |
| 3eyes | ~85% | ~85% | **~95%** | ~97% |
| 10woongi | ~55% | ~70% | **~92%** | ~95% |

### 6.2 신규 게임

| 게임 | 데이터 분석 | Tier 3 후 (파서 구현) | Tier 4 후 |
|------|-----------|---------------------|----------|
| muhan13 | ~95% | **~90%** (struct 파싱) | ~95% |
| murim | ~90% | **~80%** (rooms/ 누락) | ~90% |
| 99hunter | ~95% | **~90%** (에리어 파싱) | ~95% |

---

## 7. 어댑터 구현 로드맵

### 7.1 현재 (4개 어댑터)

```
CircleMudAdapter  → tbaMUD
SimoonAdapter     → Simoon
ThreeEyesAdapter  → 3eyes
LPMudAdapter      → 10woongi
```

### 7.2 목표 (7개 어댑터)

```
CircleMudAdapter  → tbaMUD
SimoonAdapter     → Simoon
ThreeEyesAdapter  → 3eyes
LPMudAdapter      → 10woongi
Muhan13Adapter    → muhan13   (ThreeEyesAdapter 참고, struct offset 재배치)
MurimAdapter      → murim     (완전 새 struct 레이아웃, 3,380B creature)
SmaugAdapter      → 99hunter  (완전 새 엔진, 에리어 파일 포맷)
```

### 7.3 난이도 평가

| 어댑터 | 재사용 가능 부분 | 신규 작업 | 예상 난이도 |
|--------|----------------|----------|------------|
| Muhan13Adapter | 3eyes 파일 탐색/존 분류 | struct offset 재매핑, creature2 파서 | **중** |
| MurimAdapter | 3eyes 기본 구조 | 3,380B creature, 492B object, mukong 파서 | **상** |
| SmaugAdapter | 없음 (새 엔진) | 에리어 파서, skills.dat/명령어.dat 파서, &색상 변환 | **상** |
