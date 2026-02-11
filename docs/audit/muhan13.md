# Muhan13 (무한던전, Mordor 2.0) 데이터 전수조사

> 최종 업데이트: 2026-02-12 | 심층 분석 + 런타임 차이점 분석 완료

## 1. 아키텍처

Mordor 2.0 기반 한국어 MUD. 3eyes와 동일 엔진이나 **struct 필드 순서가 다름**.
EUC-KR 인코딩, 바이너리 C struct 포맷, 포트 4000.

| 항목 | 3eyes | muhan13 차이 |
|------|-------|-------------|
| sizeof(creature) | 1184 | 1184 (동일, 필드 순서 다름) |
| sizeof(object) | 352 | 352 (동일, name 분할 다름) |
| sizeof(room) | 480 | 480 (동일, 필드 순서 다름) |
| sizeof(exit_) | 44 | 44 (동일) |
| creature 시작 필드 | fd (short) | **name[80]** |
| object name | name[70]+etc[10] | **name[80]** 통합 |
| room 시작 필드 | name[80] | **rom_num** (short) |
| creature2 struct | 없음 | **별도 파일** (title/bank/extended flags) |

## 2. 데이터 파일 구조

### objmon/ — 바이너리 데이터

| 파일 패턴 | 수량 | 데이터 | struct 크기 |
|-----------|------|--------|------------|
| m{nn} | 13 | 몬스터 (1,049 슬롯) | 1184B |
| o{nn} | 12 | 아이템 (907 슬롯) | 352B |
| talk/ | 55 | 몬스터 대화 | 텍스트 |
| ddesc/ | 14 | 사망 설명 | 텍스트 |
| rndtalk/ | 3 | 랜덤 대화 | 텍스트 |
| (readable items) | 11 | 읽기 아이템 (긴급_명령서 등) | 텍스트 |

### rooms/ — 방 데이터

| 디렉토리 | 방 수 |
|----------|-------|
| r00 | 789 |
| r01 | 847 |
| r02 | 342 |
| r03 | 500 |
| r04 | 141 |
| r05 | 133 |
| r06 | 335 |
| r07 | 3 |
| r08 | 127 |
| r09 | 1 |
| **합계** | **3,218** |

### help/ — 도움말

| 유형 | 수량 |
|------|------|
| help.N (명령어 도움말) | 150 |
| spell.N (주문 도움말) | 53 |
| 기타 (dmhelp, policy 등) | ~25 |
| **합계** | **~228** |

### src/ — 소스 코드 (67 파일, ~1.13MB)

| 카테고리 | 파일 수 |
|----------|--------|
| 명령어 핸들러 (command1-12.c) | 12 |
| 마법 (magic1-8.c) | 8 |
| DM 명령 (dm1-6.c) | 6 |
| 코어 (main, io, player, creature, room, object, update, misc) | 8 |
| 파일 I/O (files1-3.c) | 3 |
| 시스템 (bank, board, alias, action, post, special1, compress) | 7 |
| 헤더 (mtype.h, mstruct.h, mstruct2.h, mextern.h 등) | 7 |

---

## 3. Struct 상세

### 3.1 creature (1184B) — 필드 순서 (3eyes와 다름!)

```
offset 0:   name[80]          ← 3eyes는 fd(short)부터 시작
offset 80:  description[80]
offset 160: talk[80]
offset 240: password[15]      ← 3eyes는 etc[15]
offset 255: key[3][20]
...
offset ~330: fd (short)
offset ~332: level, type, class, race, numwander
offset ~340: alignment, stats (str/dex/con/int/piety)
offset ~360: hp/mp, armor, thaco
offset ~376: experience, gold, dice
offset ~400: proficiency[5], realm[4]
offset ~436: spells[16], flags[8], quests[16], questnum
offset ~470: carry[10], rom_num
... pointers, daily[10], lasttime[45]
```

**핵심 차이**: name-first (muhan13) vs fd-first (3eyes). 3eyes 파서 직접 재사용 불가.

### 3.2 creature2 (muhan13 전용)

```c
typedef struct creature2 {
    char title[80];        // 플레이어 칭호
    long bank;             // 은행 골드
    otag *inventory_box;   // 은행 인벤토리
    int  alias_num;        // 별명 수
    char flags[16];        // 확장 플래그 (128비트)
    int  empty[1024-27];   // 패딩 (총 4096B)
} creature2;
```

### 3.3 object (352B) — 거의 동일

3eyes: `name[70]+etc[10]` → muhan13: `name[80]` 통합. 나머지 동일.

### 3.4 room (480B) — 필드 순서 다름

- muhan13: `rom_num` → `name` → `short_desc` → `long_desc`
- 3eyes: `name` → `rom_num` → `long_desc` → `short_desc`
- lolevel/hilevel 위치도 다름

---

## 4. 상수 및 정의

### 4.1 클래스 (13개, 0-12)

| ID | 상수 | 한국어 | 유형 |
|----|------|--------|------|
| 0 | ZONEMAKER | 관리 | 관리자 |
| 1 | ASSASSIN | 자객 | 플레이어 |
| 2 | BARBARIAN | 야만인 | 플레이어 |
| 3 | CLERIC | 성직자 | 플레이어 |
| 4 | FIGHTER | 검사 | 플레이어 |
| 5 | MAGE | 마법사 | 플레이어 |
| 6 | PALADIN | 성기사 | 플레이어 |
| 7 | RANGER | 궁수 | 플레이어 |
| 8 | THIEF | 도적 | 플레이어 |
| 9 | INVINCIBLE | 달인 | 전직 |
| 10 | CARETAKER | 관리 | 관리자 |
| 11 | SUB_DM | 부관 | 관리자 |
| 12 | DM | 운영자 | 관리자 |

### 4.2 종족 (8종, 1-8)

드워프, 엘프, 하프엘프, 호빗, 인간, 오크반족, 반거인, 노메스족

### 4.3 스펠 (56개, MAXSPELL)

4개 마법 영역 (EARTH/WIND/FIRE/WATER), 5단계 × 4영역 = 20 공격 스펠 포함.
치유 8개, 버프 8개, 감지 4개, 디버프 6개, 유틸리티 10개.

### 4.4 착용 위치 (20 슬롯, MAXWEAR=20)

BODY, ARMS, LEGS, NECK(2), HANDS, HEAD, FEET, FINGER(8), HELD, SHIELD, FACE, WIELD

---

## 5. 명령어 시스템 (global.c cmdlist[])

| 카테고리 | 수량 |
|----------|------|
| 이동 별명 | 45 |
| 플레이어 명령 | 243 |
| DM 명령 | 103 |
| 소셜 (action) | 40 |
| 고유 명령 번호 | 155 |
| **총 엔트리** | **350** |

### 5.1 muhan13 고유 명령어

- **은행**: 입금/찾기/예금잔고/받아 (cmdno=63)
- **결혼**: 결혼/이혼/상대자 (cmdno=150)
- **문중**: 문중가입/문중원/문중 등 7개 (cmdno=148)
- **게시판**: 글/글삭제/게시판 (cmdno=92-94)
- **제련**: 제련/무기만들기 (cmdno=85)
- **전투 스킬**: 발차기/독바르기/업그레이드/집중의힘/정확의힘/흡수의힘/명상/마법차단
- **기타**: 선전포고/투표/비교/개명/계정삭제/칭호/스탯구매/초대/메모

---

## 6. 고유 시스템 (3eyes 대비)

### 6.1 은행 시스템 (bank.c, 14KB)
- 입금/인출/잔액 확인/아이템 보관
- 방 플래그: RBANK(39)

### 6.2 결혼 시스템
- 결혼식/이혼/배우자 메시지
- 방 플래그: RONMAR(40), RMARRI(41)
- 전용 디렉토리: player/marriage/

### 6.3 게시판 시스템 (board.c, 13KB)
- 18개 게시판 디렉토리 (info, user, family1-15, 일반)
- 게시판 인덱스 256B per 글

### 6.4 별명 시스템 (alias.c)
- 50개 별명/플레이어, 64명령 버퍼

### 6.5 제련/무기 제작
- forge() + newforge()
- 방 플래그: RFORGE(35)

### 6.6 전직/클래스 변경
- change_class() 함수

### 6.7 전쟁 시스템
- call_war() — 왕국 간 전쟁 선포
- 왕국 플래그: MKNDM1-4, PKNDM1-2

### 6.8 달돌(Moonstone) 시스템
- moon_set() / dm_moonstone() / update_moonstone()

---

## 7. 데이터 규모 요약

| 엔티티 | 수량 |
|--------|------|
| 방 | 3,218 |
| 몬스터 (슬롯) | 1,049 |
| 아이템 (슬롯) | 907 |
| 존 | 10 (활성) |
| 대화 파일 | 55 |
| 사망 설명 | 14 |
| 도움말 | ~228 |
| 스펠 | 56 |
| 공격 스펠 | 20 |
| 명령어 (엔트리) | 350 |
| 클래스 | 8 (플레이어) + 5 관리자 |
| 종족 | 8 |
| 클랜 슬롯 | 16 |
| 게시판 | 18 |
| 최대 레벨 | 128 |

---

## 8. 3eyes와의 비교

| 항목 | 3eyes | muhan13 |
|------|-------|---------|
| struct 크기 | 동일 | 동일 (필드 순서 다름) |
| creature2 | 없음 | **별도 struct** |
| 클래스 | 8+관리자 | 동일 |
| 종족 | 8 | 동일 |
| 스펠 | 63 | 56 |
| 명령어 | 405 | 350 |
| 은행 | 없음 | **있음** |
| 결혼 | 없음 | **있음** |
| 게시판 | board_index 바이너리 | **객체 기반 board.c** |
| 제련 | 없음 | **있음** |
| 전쟁 | 없음 | **있음** |
| 방 수 | 7,439 | 3,218 |
| 몬스터 | 1,394 | 1,049 |
| 아이템 | 1,362 | 907 |

---

## 9. 마이그레이션 고려사항

### 9.1 3eyes 파서 재사용 불가

creature/object/room struct 필드 순서가 다르므로 별도 파서 필요:
1. creature: name-first (3eyes: fd-first)
2. object: name[80] 통합 (3eyes: name[70]+etc[10])
3. room: rom_num-first (3eyes: name-first)
4. creature2 별도 파싱 필요

### 9.2 추가 파서 필요

- creature2 struct (title, bank, extended flags)
- 은행 데이터 (player/bank/)
- 게시판 데이터 (18개 디렉토리)
- rndtalk 파일 (3eyes에 없는 포맷)
- 클랜 데이터 (family_*)

---

## 10. 런타임 메커닉 — 3eyes 대비 차이점

> 소스: `src/command5.c`, `src/creature.c`, `src/global.c`, `src/bank.c` 분석

### 10.1 3eyes와 동일한 부분

- **THAC0 공식**: `mrand(1,30) >= thaco - armor/10` (d30 기반 동일)
- **기본 전투 흐름**: attack_crt() 구조 동일
- **사망 경험치 패널티**: 레벨 20 이하 1/20, 이상 1/15 또는 100,000 고정
- **다단 공격**: PUPDMG 플래그 시 count++ (최대 3회)
- **무기 숙련도**: proficiency[5] (SHARP/THRUST/BLUNT/POLE/MISSILE)
- **마법 영역**: realm[4] (EARTH/WIND/FIRE/WATER)
- **방어도**: thaco - armor/8 보정, bonus[] 배열

### 10.2 creature2 — 확장 구조체 (3eyes에 없음)

```c
typedef struct creature2 {
    char title[80];        // 칭호 (who 표시)
    long bank;             // 은행 잔액
    otag *inventory_box;   // 은행 아이템 보관
    int  alias_num;        // 별명 수
    char flags[16];        // 확장 플래그 (128비트)
    int  empty[1024-27];   // 패딩 (총 4096B)
} creature2;
```

플레이어당 2개 파일 관리: creature(1184B) + creature2(4096B).

### 10.3 은행 시스템 (bank.c)

3eyes에 없는 muhan13 전용 시스템:

| 기능 | 명령어 | 설명 |
|------|--------|------|
| 입금 | 입금 | 골드 예치 |
| 출금 | 찾기 | 골드 인출 |
| 잔액 | 예금잔고 | 잔액 확인 |
| 아이템 보관 | 은행 | 아이템 저장소 |

저장: `PLAYERPATH/bank/플레이어명` 파일.
방 플래그: RBANK(39) — 은행 이용 가능 방.

### 10.4 가문(클랜) 시스템 — 전쟁 기능 추가

```
16개 가문 슬롯: family_str[16], fmboss_str[16]
AT_WAR 전역 변수 — 가문 간 전쟁 상태
check_war() — 전쟁 판정 함수
가문장 사망 시 → 전쟁 종료

플래그: PFAMIL(가문 소속), PFMBOS(가문장)
명령어: 문중가입/문중원/문중/선전포고 등 7개
```

### 10.5 결혼/이혼 시스템

```
방 플래그: RONMAR(40) 결혼식장, RMARRI(41) 결혼 관련
명령어: 결혼/이혼/상대자
저장: player/marriage/ 디렉토리
```

### 10.6 제련/달돌 시스템

```
제련: 특정 방(RFORGE=35)에서 달돌+무기 → 능력치 향상
달돌: moon_set() / dm_moonstone() / update_moonstone()
명령어: 제련/무기만들기
```

### 10.7 게시판 시스템 (board.c, 13KB)

3eyes는 board_index 바이너리, muhan13은 **파일 기반 객체 게시판**:

```
18개 게시판 디렉토리: info, user, family1-15, 일반
게시판 인덱스: 256B per 글
명령어: 글/글삭제/게시판
```

### 10.8 칭호 시스템

```
creature2->title[80]에 저장
명령어: 칭호/칭호변경
who 명령 시 이름 옆에 표시
```

### 10.9 사망 처리 차이

```
3eyes와 동일:
  - 경험치 패널티: level_exp 차이의 3/4
  - 영혼방 이동

muhan13 추가:
  - 전쟁 중 비생존 방에서 사망: 착용 장비 드롭
  - 부활: 방 1008 (회복의 방)
```

### 10.10 DB 설계 포인트 (3eyes 대비 추가)

| 런타임 요소 | DB/엔진 적용 |
|-------------|-------------|
| creature2 | players 테이블 확장 (title, bank 컬럼 추가) |
| 은행 시스템 | bank_items 테이블 또는 players.bank JSONB |
| 가문 전쟁 | clans 테이블 + 전쟁 상태 (인메모리) |
| 결혼 | players.spouse 컬럼 |
| 제련/달돌 | crafting_recipes 테이블 또는 런타임 전용 |
| 게시판 | boards + board_posts 테이블 |
| 칭호 | players.title 컬럼 |
