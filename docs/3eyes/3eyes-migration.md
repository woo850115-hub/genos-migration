# 3eyes (검제3의눈) Migration Report

## 1. Overview

3eyes(검제3의눈)는 Mordor/CircleMUD 계열의 한국형 커스텀 MUD이다. 일반 CircleMUD의 텍스트 파일 포맷과 완전히 다른 **바이너리 C 구조체** 형식을 사용하는 것이 가장 큰 특징이다. 32-bit Linux(x86)에서 컴파일/운영되었으며, 모든 데이터가 C `write(fd, &struct, sizeof(struct))` 형태로 직접 디스크에 기록된다.

- **기반**: Mordor (CircleMUD variant)
- **인코딩**: EUC-KR
- **데이터 형식**: 바이너리 C 구조체 (32-bit Linux, little-endian)
- **포트**: 7123
- **특수 시스템**: 가문(16개), 결혼, 킬러모드, 경매, 무술랭킹, 포커/카지노

### Migration 결과

| 항목 | 수량 |
|------|------|
| Rooms | 7,439 |
| Monsters | 1,394 |
| Items | 1,362 |
| Zones | 103 |
| Help | 116 |
| Skills/Spells | 63 |
| Classes | 8 |
| Races | 8 |
| Talk Files | 41 |
| Ddesc Files | 39 |
| THAC0 Table | 160 |
| Exp Table | 203 |
| Attr Modifiers | 160 |

### 출력 파일

| 파일 | 크기 | 줄 수 |
|------|------|-------|
| uir.yaml | ~8 MB | ~423K |
| seed_data.sql | 5.7 MB | 28,820 |
| schema.sql | 8 KB | 224 |
| combat.lua | 1.6 KB | 56 |
| classes.lua | 2.1 KB | 103 |
| exp_tables.lua | 4.3 KB | 218 |
| stat_tables.lua | 4.9 KB | 180 |

---

## 2. 바이너리 형식 vs 텍스트 형식

3eyes가 다른 CircleMUD 변형과 근본적으로 다른 점은 **텍스트 기반 데이터 파일이 아닌 바이너리 C 구조체**를 직접 사용한다는 것이다.

| 비교 항목 | CircleMUD/tbaMUD/Simoon | 3eyes |
|-----------|------------------------|-------|
| 데이터 형식 | 텍스트 (`#vnum`, `~` 구분자) | 바이너리 C struct |
| 레코드 구분 | `#vnum` 마커로 시작 | 고정 크기 레코드 (offset 계산) |
| 문자열 | tilde-terminated (`~`) | null-terminated C string |
| 플래그 | asciiflag 또는 정수 | 바이트 배열 + F_ISSET 매크로 |
| 방 파일 | 1파일에 여러 방 | 방 하나가 개별 파일 |
| 포인터 필드 | 없음 | 있음 (디스크에서 무시) |

이 때문에 기존 CircleMUD 텍스트 파서를 재활용할 수 없고, 완전히 별도의 바이너리 파서가 필요하다.

---

## 3. 한글 콘텐츠 비율

| 데이터 | 한글 | 전체 | 비율 |
|--------|------|------|------|
| Rooms | 7,396 | 7,426 (named) | 99.6% |
| Monsters | 1,358 | 1,394 | 97.4% |
| Items | 1,320 | 1,362 | 96.9% |

Simoon(91%)이나 tbaMUD(0%)과 비교하면, 3eyes는 거의 모든 콘텐츠가 한글로 작성되어 있다. 영문 stock zone이 거의 없는 순수 한국어 MUD이다.

---

## 4. 파일 시스템 구조

```
3eyes/
├── rooms/                      ← 방 데이터 (바이너리, 개별 파일)
│   ├── r00/
│   │   ├── r00000              ← 방 #0
│   │   ├── r00001              ← 방 #1
│   │   └── ...
│   ├── r01/
│   └── ...  (14개 zone 디렉토리)
├── objmon/                     ← 오브젝트/몬스터 데이터
│   ├── o00 ~ o28               ← 오브젝트 (100개×352바이트/파일)
│   ├── m00 ~ m28               ← 몬스터 (100개×1184바이트/파일)
│   ├── talk/                   ← 몬스터 대화 텍스트
│   │   ├── 길라잡이-25
│   │   └── ...  (41개 파일)
│   └── ddesc/                  ← 몬스터 상세설명 텍스트
│       ├── 검은_알_10
│       └── ...  (39개 파일)
├── help/                       ← 도움말 텍스트
│   ├── help.1 ~ help.152       ← 116개 파일
│   ├── char                    ← 캐릭터 관련 도움말
│   ├── exp                     ← 경험치 테이블
│   └── dmhelp                  ← DM 전용 도움말
├── src/                        ← C 소스 코드
│   ├── mstruct.h               ← 구조체 정의
│   ├── mtype.h                 ← 상수/플래그 정의
│   └── files1.c                ← read_rom/write_rom I/O
└── player/                     ← 플레이어 데이터 (마이그레이션 대상 아님)
```

### 파일 크기 검증

| 구조체 | sizeof | 파일 예시 | 파일 크기 | 100으로 나눈 값 |
|--------|--------|-----------|-----------|-----------------|
| object | 352 | o00 | 35,200 | 352 ✓ |
| creature | 1,184 | m00 | 118,400 | 1,184 ✓ |
| room | 480 | (가변) | 가변 | — |
| exit_ | 44 | (room 내부) | — | — |

일부 파일은 100개 미만의 레코드를 포함하여 크기가 작다 (정상 동작).

---

## 5. Room 상세 통계

### 5-1. 기본 통계

| 항목 | 수치 |
|------|------|
| 총 방 수 | 7,439 |
| 이름 있는 방 | 7,426 (99.8%) |
| 설명 있는 방 | 5,405 (72.7%) |
| 출구 있는 방 | 7,052 (94.8%) |
| 총 출구 수 | 16,514 (방당 평균 2.22개) |
| 랜덤 몬스터 설정 방 | 566 |
| 특수 기능 방 | 473 |
| 함정 방 | 183 |

### 5-2. 출구 수 분포

| 출구 수 | 방 수 |
|---------|-------|
| 0 | 387 |
| 1 | 1,426 |
| 2 | 4,106 |
| 3 | 1,107 |
| 4 | 336 |
| 5 | 55 |
| 6+ | 22 |

대부분의 방이 2개의 출구를 가진 직선 통로 구조이다.

### 5-3. Top 10 Zone별 방 수

| Zone | 방 수 | 대표 방 이름 |
|------|-------|-------------|
| 87 | 666 | 화룡의 꿈 |
| 6 | 380 | 마케스터 시내 6 |
| 5 | 349 | 5 번 |
| 34 | 282 | 중형 드래곤 동굴 34 |
| 35 | 268 | 3530 |
| 88 | 264 | 야영장 |
| 12 | 259 | 바다 |
| 33 | 251 | 메카닉스 동네 |
| 36 | 241 | 얼음왕국 |
| 10 | 238 | 바다속 |

### 5-4. Room Flag 분포

| Flag | 이름 | 수량 |
|------|------|------|
| 12 | no_teleport | 5,776 |
| 33 | no_login | 5,443 |
| 28 | no_leave | 4,948 |
| 42 | killer | 4,830 |
| 8 | dark_always | 1,398 |
| 11 | no_kill | 622 |
| 0 | shop | 275 |
| 17 | no_magic | 206 |
| 43 | no_map | 186 |
| 47 | shrine | 157 |

대부분의 방에 `no_teleport`(78%), `no_login`(73%), `no_leave`(67%), `killer`(65%) 플래그가 설정되어 있다. 이는 3eyes가 PvP 전투(킬러모드)를 핵심 시스템으로 가지고 있음을 반영한다.

### 5-5. 특수 방 기능

| Special 값 | 수량 | 의미 |
|------------|------|------|
| 4 (게시판) | 208 | 게시판 설치 방 |
| 101-116 | 178 | 가문(Family) 전용 방 |
| 1 (지도/두루마리) | 29 | 지도/스크롤 방 |
| 2 (조합 자물쇠) | 18 | 콤비네이션 락 방 |
| 120-121 | 13 | 복권 관련 방 |
| 200 | 27 | 이벤트 방 |

가문(Family) 시스템이 16개 가문을 지원하며, 각 가문 전용 방(SP_FAM1~SP_FAM16)이 178개 존재한다.

---

## 6. Item 상세 통계

### 6-1. 아이템 타입 분포

| Type | 이름 | 수량 | 비율 |
|------|------|------|------|
| 5 | armor | 357 | 26.2% |
| 6 | potion | 179 | 13.1% |
| 13 | misc | 173 | 12.7% |
| 11 | key | 121 | 8.9% |
| 7 | scroll | 115 | 8.4% |
| 10 | money | 94 | 6.9% |
| 8 | wand | 78 | 5.7% |
| 12 | lightsource | 67 | 4.9% |
| 9 | container | 54 | 4.0% |
| 0 | (weapon/untyped) | 60 | 4.4% |
| 14 | container2 | 26 | 1.9% |
| 15 | hp_up | 20 | 1.5% |

3eyes의 object type=0은 무기(weapon)에 해당한다. tbaMUD에서는 type 5가 weapon이지만, 3eyes(Mordor 계열)에서는 type이 0이면 기본 무기를 의미한다.

### 6-2. 착용 위치 분포

| Wearflag | 위치 | 수량 |
|----------|------|------|
| 17 | held | 347 |
| 20 | wield | 243 |
| 1 | body | 59 |
| 4 | neck | 55 |
| 9 | finger | 52 |
| 7 | head | 50 |
| 18 | shield | 47 |
| 8 | feet | 41 |
| 6 | hands | 39 |
| 19 | face | 33 |

`held`(손에 든 장비)가 가장 많고, 그 다음이 `wield`(무기 장비)이다.

### 6-3. Top 10 아이템 플래그

| Flag | 이름 | 수량 |
|------|------|------|
| 15 | no_fix (수리 불가) | 278 |
| 14 | enchanted (인챈트) | 268 |
| 46 | event (이벤트) | 109 |
| 0 | permanent | 91 |
| 17 | no_take (줍기 불가) | 74 |
| 23 | worn (착용 중) | 52 |
| 47 | named (이름 변경됨) | 46 |
| 18 | scenery (배경) | 32 |
| 31 | class_selective | 30 |
| 28 | obj_dice_damage | 30 |

---

## 7. Monster 상세 통계

### 7-1. 레벨 분포

| 레벨대 | 수량 |
|--------|------|
| 0-19 | 267 |
| 20-39 | 178 |
| 40-59 | 138 |
| 60-79 | 114 |
| 80-99 | 109 |
| 100-119 | 189 |
| 120-127 | 399 |

- 최소 레벨: 0, 최대 레벨: 127 (unsigned char 범위)
- 레벨 120-127에 대규모 집중 (전체의 28.6%) — 엔드게임 몬스터 밀집
- Simoon의 최대 레벨 1000과 달리, 3eyes는 1바이트(unsigned char)로 레벨 상한 127

### 7-2. 성향(Alignment) 분포

| 성향 | 수량 | 비율 |
|------|------|------|
| 중립 (-200 ~ 200) | 1,140 | 81.8% |
| 악 (< -200) | 185 | 13.3% |
| 선 (> 200) | 69 | 4.9% |

대부분의 몬스터가 중립 성향이다.

### 7-3. 직업(Class) 분포

| Class | 이름 | 수량 |
|-------|------|------|
| 0 | (없음) | 1,044 |
| 5 | Mage | 168 |
| 3 | Cleric | 75 |
| 4 | Fighter | 57 |
| 6 | Paladin | 23 |
| 1 | Assassin | 10 |
| 7 | Ranger | 8 |
| 8 | Thief | 6 |
| 2 | Barbarian | 3 |

74.9%의 몬스터에 직업이 설정되지 않았다. 직업이 설정된 몬스터는 주로 Mage(168), Cleric(75), Fighter(57)이다.

### 7-4. 종족(Race) 분포

| Race | 이름 | 수량 |
|------|------|------|
| 0 | (없음) | 1,039 |
| 5 | Human | 200 |
| 6 | Orc | 60 |
| 2 | Elf | 28 |
| 1 | Dwarf | 22 |
| 3 | Half-Elf | 19 |
| 4 | Hobbit | 16 |
| 8 | Gnome | 7 |
| 7 | Half-Giant | 3 |

74.5%의 몬스터에 종족이 미설정. Human(200)이 가장 많다.

### 7-5. 스펠 사용 통계

1,394마리 중 801마리(57.5%)가 스펠을 보유한다.

| Spell | 이름 | 사용 수 |
|-------|------|---------|
| 18 | mend_wounds (상처회복) | 484 |
| 6 | fireball (화염구) | 426 |
| 0 | vigor (활력) | 406 |
| 13 | lightning (번개) | 371 |
| 25 | shock (감전) | 266 |
| 4 | bless (축복) | 254 |
| 5 | protection (보호) | 254 |
| 14 | ice_blast (얼음폭풍) | 246 |
| 8 | restore (회복) | 244 |
| 1 | hurt (상처) | 243 |

### 7-6. Monster Flag 분포

| Flag | 이름 | 수량 |
|------|------|------|
| 12 | male | 1,148 |
| 0 | permanent | 1,028 |
| 6 | aggressive | 537 |
| 5 | no_prefix | 455 |
| 17 | casts_magic | 417 |
| 9 | follows_attacker | 302 |
| 10 | flees | 196 |
| 21 | detect_invisible | 153 |
| 25 | no_random_gold | 121 |
| 7 | guards_treasure | 121 |

82.4%의 몬스터가 male 플래그를 가진다. permanent(73.7%), aggressive(38.5%) 순.

### 7-7. Talk/Ddesc

| 항목 | 수량 |
|------|------|
| Talk 파일 (대화) | 41 |
| Talk 키워드-응답 쌍 | 386 |
| Ddesc 파일 (상세설명) | 39 |
| 대화 가진 몬스터 (매칭됨) | 32 |
| 상세설명 가진 몬스터 (매칭됨) | 37 |

Talk 파일은 `{이름}-{레벨}` 형식(예: `길라잡이-25`), ddesc 파일은 `{이름}_{레벨}` 형식(예: `검은_알_10`)으로 파일명에 몬스터 이름과 레벨이 인코딩되어 있다.

### 7-8. 골드/경험치 범위

| 항목 | 최소 | 최대 |
|------|------|------|
| Gold | 0 | 3,000,000 |
| Experience | 0 | 666,666 |

---

## 8. Character Classes (직업)

3eyes는 8개의 플레이어 직업을 제공한다:

| ID | 이름 | 약어 | HP 범위 | MP 범위 |
|----|------|------|---------|---------|
| 1 | Assassin (암살자) | As | 8-12 | 2-6 |
| 2 | Barbarian (야만전사) | Ba | 12-18 | 0-0 |
| 3 | Cleric (성직자) | Cl | 6-10 | 4-8 |
| 4 | Fighter (검사) | Fi | 10-15 | 0-0 |
| 5 | Mage (마법사) | Ma | 4-8 | 6-12 |
| 6 | Paladin (성기사) | Pa | 8-14 | 2-6 |
| 7 | Ranger (순찰자) | Ra | 9-14 | 1-4 |
| 8 | Thief (도적) | Th | 7-11 | 1-3 |

Barbarian과 Fighter는 MP(마나)가 0으로 순수 물리 직업이다. Mage가 가장 높은 MP 성장을 가진다.

---

## 9. Races (종족)

8개의 플레이어 종족:

| ID | 이름 | 약어 | 스탯 보정 |
|----|------|------|-----------|
| 1 | Dwarf (드워프) | Dw | STR+2, CON+1, INT-1 |
| 2 | Elf (엘프) | El | DEX+2, INT+1, CON-1 |
| 3 | Half-Elf (하프엘프) | He | DEX+1, INT+1 |
| 4 | Hobbit (호빗) | Ho | DEX+2, STR-1 |
| 5 | Human (인간) | Hu | (보정 없음) |
| 6 | Orc (오크) | Or | STR+2, CON+1, INT-2 |
| 7 | Half-Giant (하프자이언트) | Hg | STR+3, CON+2, INT-2, DEX-1 |
| 8 | Gnome (노움) | Gn | INT+2, DEX+1, STR-1 |

Simoon(5종족)보다 많은 8종족 체계. Orc, Half-Giant, Gnome이 추가되어 있다.

---

## 10. Spell System (주문 체계)

3eyes는 63개의 주문을 지원한다. 4개의 마법 영역(Realm)으로 분류된다:

| 영역 | 이름 | 주요 스펠 |
|------|------|-----------|
| 1 | Earth (땅) | vigor, bless, mend_wounds, know_alignment |
| 2 | Wind (바람) | hurt, lightning, shock, dust_gust |
| 3 | Fire (불) | fireball, burn, burst, hellfire |
| 4 | Water (물) | ice_blast, water_bolt, steam, flood_fill |

고레벨 스펠에는 한국 애니메이션/판타지 영향이 보인다:
- `dragon_slave` (드래곤 슬레이브) — 슬레이어즈 시리즈
- `giga_slave` (기가 슬레이브) — 슬레이어즈 시리즈
- `plasma` (플라즈마)
- `megiddo` (메기도) — 성경/RPG 레퍼런스
- `hellfire` (헬파이어)
- `aqua_ray` (아쿠아레이)

---

## 11. 3eyes 고유 시스템

표준 CircleMUD/Mordor에 없는 3eyes만의 확장 시스템:

### 11-1. 가문 (Family) 시스템
- 최대 16개 가문 (`MAXFAMILY 16`)
- 가문 전용 방 (`RFAMIL`, `RONFML` 플래그)
- 가문 보스 (`PFMBOS`), 가문 채팅 (`PNOFAMTALK`)
- 가문 전용 아이템 (`OFAMIL` 플래그)
- Special 101~116: 가문별 전용 공간

### 11-2. 결혼 시스템
- 결혼 상태 플래그 (`PMARRI`, `PRDMAR`)
- 결혼 전용 방 (`RMARRI`, `RONMAR`)
- 결혼 전용 아이템 (`OMARRI`)
- Daily use 변수로 결혼 관련 기능 제한 (`DL_MARRI`)

### 11-3. 킬러모드
- 킬러 플래그 (`RKILLR` room flag)
- 전체 방의 65%가 킬러 모드 허용
- 별도 킬러 디렉토리 (`killer/`)

### 11-4. 경제 시스템
- 은행 방 (`RBANK`)
- 경매 시스템 (PNOAUC 플래그로 알림 토글)
- 카지노/포커 방 (`RCAZINO`, `RPOKER`)

### 11-5. 아이템 특수 기능
- 업그레이드 스펠 (`SUPGRADE`)
- 폭탄 아이템 (`OBOMB`)
- 그림자 아이템 (`OSHADO`, `OSHAD2` — 사용 시 그림자 획득)
- 관리자 전용 아이템 (`OINVIN`, `OCARET`, `OCARE2`, `OCARE3`)
- 3eyes 전용 아이템 (`O3EYES` — 업그레이드 가능)

---

## 12. Validation 이슈

### 12-1. 빈 방 (13건)
VNUM 0, 4, 5, 6, 7, 8, 9, 10 등 13개 방에 이름이 없다. 시스템 예약 슬롯으로 추정.

### 12-2. Dead-End 방 (381건)
이름이 있지만 출구가 없는 방이 381개. 일부는 의도적 (감옥, 함정, 텔레포트 목적지), 일부는 미완성 zone.

### 12-3. Dangling Exit (1건)
출구가 존재하지 않는 방을 가리키는 경우가 1건 확인됨. 전체 16,514개 출구 중 1건이므로 데이터 무결성은 양호.

### 12-4. 미분류 아이템 (60건)
`item_type=0`인 아이템이 60개. 3eyes에서 type 0은 무기(weapon)에 해당하므로 이는 정상 데이터이나, UIR에서는 명시적 무기 타입 매핑이 필요할 수 있다.

### 12-5. Talk/Ddesc 미매칭
- 41개 talk 파일 중 32개만 몬스터와 매칭 (78%)
- 39개 ddesc 파일 중 37개만 매칭 (95%)
- 미매칭 원인: 파일명의 이름/레벨이 실제 몬스터 데이터와 불일치 (이름에 공백 vs 밑줄 차이 등)

---

## 13. 마이그레이션 시 주의사항

### 바이너리 파싱
- 모든 오프셋은 32-bit Linux의 자연 정렬(natural alignment) 기준
- 패딩 바이트를 정확히 고려해야 함 (예: `creature`의 offset 7, 15, 26-27, 359, 437)
- 포인터 필드(4바이트)는 디스크에서 무의미한 값 — 무시해야 함

### 인코딩
- 모든 텍스트 필드는 EUC-KR로 디코딩
- C 문자열이므로 null-terminator로 끝남
- `errors="replace"` 옵션으로 깨진 문자 대응
- 파일명도 EUC-KR (talk/ddesc 디렉토리의 한글 파일명)

### 파일 크기 가변성
- object/creature 파일이 정확히 100개 레코드를 포함하지 않을 수 있음
- `record_count = min(file_size // struct_size, 100)`으로 안전 처리
- 파일 크기가 구조체 크기의 배수가 아닌 경우도 존재 (m03: 117,216 ≠ 1,184×100)

### Room 파일 구조
- Room 파일은 가변 길이 — 고정 480바이트 + 가변 섹션
- 가변 섹션 순서: exits → monsters(+inventory) → objects(+contents) → short_desc → long_desc → obj_desc
- 몬스터와 오브젝트는 재귀적으로 인벤토리/내용물을 포함할 수 있음
- 현재 파서는 room의 몬스터/오브젝트는 skip하고 방 데이터만 추출 (objmon에서 별도 파싱)

### Color Code
방 설명에 `#녹{텍스트}`, `#빨{텍스트}` 형태의 한국어 색상 코드가 사용된다:
```
#녹{검제3의 }#빨{검눈}으로 오신것을 환영합니다.
```
GenOS 변환 시 이 색상 코드의 후처리 매핑이 필요하다.

---

## 14. Phase 3: 시스템 테이블 마이그레이션

3eyes의 시스템 데이터는 `src/global.c`의 C 배열 이니셜라이저에서 파싱한다. tbaMUD/Simoon의 `config.c`/`class.c`/`constants.c` 구조와 다르지만, 동일한 UIR 구조로 변환된다.

### 14-1. THAC0 Table

`thaco_list[][20]` 배열에서 추출. **160개** 항목 (8클래스 × 20레벨).

```c
short thaco_list[][20] = {
    { 20, 20, 19, 19, 18, ... },  // Assassin (class 1)
    { 20, 19, 18, 17, 16, ... },  // Barbarian (class 2)
    ...
};
```

클래스 1(Assassin)~8(Thief)까지 각각 레벨 1~20의 THAC0 값. tbaMUD(34레벨)보다 레벨 범위가 좁지만 클래스 수가 2배(8개 vs 4개).

### 14-2. Experience Table

`level_exp[]` 배열에서 추출. **203개** 항목 (레벨 0~202, class_id=0 공유).

```c
long level_exp[] = { 0, 100, 300, 700, 1500, ... };
```

전 클래스가 동일 경험치 테이블을 공유한다 (tbaMUD와 달리 클래스별 분리 없음). 최대 레벨 127에 비해 테이블은 202까지 정의되어 있어 여유분이 존재.

### 14-3. Bonus Table (능력치 보정)

`bonus[]` 배열에서 추출. **160개** 항목 → `AttributeModifier(stat_name="bonus")`.

```c
short bonus[] = { -5, -5, -4, -4, -3, ..., 3, 4, 5 };
```

tbaMUD의 6종 세분화된 능력치 보정(str_app, dex_app 등)과 달리, 3eyes는 단일 `bonus[]` 배열로 모든 능력치 보정을 처리한다.

### 14-4. Class Stats

`class_stats[13]` 배열에서 추출. 8개 클래스의 초기 스탯 및 레벨업 주사위.

```c
struct class_stats_struct class_stats[] = {
    { hpstart, mpstart, hp, mp, ndice, sdice, pdice },
    ...
};
```

추출된 데이터는 `CharacterClass.extensions`에 머지:
- `hpstart`/`mpstart`: 시작 HP/MP
- `hp`/`mp`: 레벨업 HP/MP 기본 증가
- `ndice`/`sdice`/`pdice`: 레벨업 주사위 (NdS+P)

### 14-5. Level Cycle

`level_cycle[][10]` 배열에서 추출. `uir.extensions["level_cycle"]`에 저장.

3eyes 고유의 레벨업 스탯 사이클 시스템으로, 각 레벨업 시 어떤 능력치가 상승하는지 정의한다. STR/INT/DEX/CON/PTY(경건) 5개 능력치의 순환 패턴.

### 14-6. 미지원 항목

- **Game Config**: 3eyes에는 `config.c`가 없음 (설정이 하드코딩)
- **Saving Throws**: global.c에 세이빙 스로우 테이블 없음
- **Level Titles**: 3eyes 칭호는 커스텀 시스템 (C 배열에 없음)
- **Practice Params**: global.c에 연습 파라미터 없음

### 14-7. Phase 3 출력 파일 변화

| 파일 | Phase 2 | Phase 3 적용 후 |
|------|---------|-----------------|
| schema.sql | 14 테이블 | 21 테이블 (+7) |
| seed_data.sql | ~28K 줄 | ~29K 줄 (+523 Phase 3 행) |
| Lua 스크립트 | 2개 | 4개 (+exp_tables, stat_tables) |

3eyes는 config.c가 없어 config.lua가 생성되지 않는다 (tbaMUD/Simoon과의 차이).
