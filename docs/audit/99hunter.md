# 99hunter (더 헌터, SMAUG MUD) 데이터 전수조사

> 최종 업데이트: 2026-02-11 | 심층 분석 완료

## 1. 아키텍처

SMAUG 1.4 기반 한국어 MUD (Merc 2.1 → DikuMUD 계열). 기존 분석 게임들과
**완전히 다른 엔진**: 텍스트 기반 에리어 파일, 모든 엔티티가 단일 파일에 포함.
EUC-KR 인코딩, 포트 7000. 개발팀: "Never Ending Loop Team" (1999-2000).

| 항목 | CircleMUD계 | Mordor계 | SMAUG (99hunter) |
|------|-------------|----------|-----------------|
| 포맷 | 텍스트 WLD/MOB/OBJ/ZON | 바이너리 C struct | **텍스트 에리어 파일** |
| 파일 구조 | 타입별 분리 | 타입별 분리 | **단일 파일에 전체** |
| 문자열 종료 | ~ (tilde) | length-prefix | ~ (tilde) |
| Bitvector | 128-bit | 8B flags | **확장 128-bit** (4×32) |
| 색상 코드 | ANSI \033[ | 없음 | **&W &g 등** |
| 스킬 정의 | C 소스 spello() | C 소스 | **외부 skills.dat** |
| 클래스 정의 | C 소스 class.c | C 소스 | **외부 .class 파일** |
| OLC | OasisOLC | 없음 | **내장 build.c** |

## 2. 에리어 파일 포맷

### 2.1 섹션 구조

```
#AREA   <area-name>~
#VERSION 1
#AUTHOR <author>~
#RANGES <low_soft> <hi_soft> <low_hard> <hi_hard> $
#RESETMSG <message>~          (선택)
#FLAGS <area-flags>
#ECONOMY <gold> <total>
#CLIMATE <temp> <precip> <wind>
#MOBILES ... #0
#OBJECTS ... #0
#ROOMS ... #0
#RESETS ... S
#SHOPS ... 0
#REPAIRS ... 0
#SPECIALS ... S
#$
```

### 2.2 MOB 포맷 (S타입/C타입)

**S타입 (단순)**: 3줄 스탯
```
#<vnum>
<keywords>~
<short-desc>~
<long-desc>~
<description>~
<act-flags> <affected-flags> <alignment> S
<level> <hitroll> <armor> <hitdice>d<hitsize>+<hitbonus> <damdice>d<damsize>+<dambonus>
<gold> <exp>
<position> <position> <sex>
```

**C타입 (복잡)**: 8줄 스탯 (7종 스탯, 5종 saving throw, 종족/클래스 등)
```
... S → C
... (기본 3줄)
<str> <int> <wis> <dex> <con> <cha> <lck>
<sav1> <sav2> <sav3> <sav4> <sav5>
<race> <class> <height> <weight> <speaks> <speaking> <numattacks>
<hitroll> <damroll> <xflags> <resist> <immune> <suscept> <attacks> <defenses>
```

### 2.3 OBJ 포맷

```
#<vnum>
<keywords>~
<short-desc>~
<long-desc>~
<action-desc>~
<item-type> <extra-flags> <wear-flags>
<value0> <value1> <value2> <value3>
<weight> <cost> <cost-per-day>
{E <keyword>~ <description>~}   (선택: extra desc)
{A <apply-type> <apply-value>}  (선택: applies)
```

### 2.4 ROOM 포맷

```
#<vnum>
<name>~
<description>~
<area-obsolete> <room-flags> <sector-type> [teledelay televnum]
D<direction>     (0-10, 10=somewhere)
  <exit-desc>~
  <exit-keywords>~
  <lock-flags> <key-vnum> <to-room-vnum>
E
  <keywords>~
  <description>~
S                (방 종료)
```

**Direction 10**: "somewhere" — 포탈/특수 출구 (문~, 입구~ 등 키워드)

---

## 3. 에리어 파일 목록 (53개 활성)

| 에리어 | 크기 | 예상 엔티티 |
|--------|------|------------|
| 왕국건물들 | 27KB | ~1,005 |
| 불.정령계 | 105KB | ~505 |
| 바람.정령계 | 33KB | ~516 |
| 물.정령계 | 55KB | ~429 |
| 불거인성 | 97KB | ~327 |
| 초보자존 | 160KB | ~290 |
| 블루드래곤존 | 46KB | ~211 |
| 블랙드래곤존 | 49KB | ~206 |
| 대평원 | 8KB | ~204 |
| 수원지 | 21KB | ~204 |
| 아크리릭 | 46KB | ~192 |
| 블랙웜존 | 49KB | ~180 |
| 레드웜존 | 46KB | ~171 |
| 에트린 | 36KB | ~154 |
| 고블린야산 | 33KB | ~134 |
| 오크소굴 | 35KB | ~128 |
| 얼음산맥중부 | 30KB | ~119 |
| 화이트웜존 | 30KB | ~119 |
| 오우거엘프숲 | 28KB | ~112 |
| 트레이닝존 | 30KB | ~110 |
| 기타 33개 | 다양 | ~1,500+ |
| **합계** | | **~7,348** |

별도: 작업/ 디렉토리에 WIP/백업 14개 파일 (로드 안됨)

---

## 4. 클래스 (30개)

### 4.1 기본 클래스 (6)

모험가, 마법사, 성직자, 전사, 도둑, 매지션

### 4.2 고급 마법 (4)

룬캐스터, 인챈터, 위저드, 네크로맨서

### 4.3 고급 성직 (6)

프리스트, 샤먼, 비숍, 드루이드, 포프, 프로핏

### 4.4 고급 전투 (7)

페이지, 워리어, 나이트, 파이터, 아처, 패러딘, 워로드

### 4.5 고급 도적 (7)

시프, 킬러, 바드, 로그, 어쌔신, 미스틱, 어벤저

### 4.6 클래스 파일 포맷

```
Name        <한국어이름>~
Class       <class-id>
Attrprime   <주속성>     (1=Str, 2=Dex, 3=Int, 4=Wis)
Weapon      <무기-vnum>
Guild       <길드방-vnum>
Skilladept  <최대스킬%>
Thac0       <레벨1 thac0>
Thac32      <레벨32 thac0>
Hpmin/Hpmax <HP증가범위>
Mana        <마나타입>   (0=없음, 1=있음)
Expbase     <기본경험치>
Skill '<스킬명>' <습득레벨> <습득%>
...
End
```

---

## 5. 종족 (8 플레이어 + 91 NPC)

| ID | 이름 | Str | Dex | Int | Con | Exp% | 특징 |
|----|------|-----|-----|-----|-----|------|------|
| 0 | 인간 | 0 | 0 | 0 | 0 | 100 | 기본 |
| 1 | 엘프 | -2 | +2 | +2 | -1 | 94 | 마나+10 |
| 2 | 드워프 | +2 | 0 | 0 | +3 | 96 | HP+6 |
| 3 | 하플링 | -2 | +1 | 0 | +1 | 105 | 마나+10 |
| 4 | 하프엘프 | -1 | +1 | +1 | -1 | 98 | HP+3, 마나+3 |
| 5 | 하프오우거 | +5 | -3 | -2 | +4 | 92 | HP+5 |
| 6 | 바다엘프 | -2 | +2 | +2 | -1 | 96 | 마나+10 |
| 7 | 드래곤뉴트 | +3 | -3 | +2 | +2 | 95 | HP+2 |

NPC 종족 91개: const.c의 `_npc_race[]` 배열 (전부 한국어)

---

## 6. 시스템 데이터 (시스템/ 디렉토리)

| 파일 | 크기 | 설명 |
|------|------|------|
| skills.dat | 79KB | **54 스킬/스펠** (#SKILL 포맷) |
| 명령어.dat | 50KB | **488 명령어** (#COMMAND 포맷) |
| socials.dat | 38KB | 7 한국어 소셜 |
| sysdata.dat | 1KB | 시스템 설정 |
| economy.txt | 268KB | 경제 데이터 |
| tongues.dat | 6KB | 언어 시스템 |
| herbs.dat | 2KB | 약초 데이터 |
| commands.eng | 47KB | 영문 명령어 테이블 |

### 6.1 시스템 설정 (sysdata.dat)

```
MudName      더 헌터
MAX_LEVEL    777
Damplrvsplr  33      (PvP 데미지 33%)
Dammobvsplr  100     (MvP 데미지 100%)
StunRegular  15
DodgeMod     2
ParryMod     2
TumbleMod    3
```

### 6.2 스킬 포맷 (#SKILL)

```
#SKILL
Name         <스킬명>~
Type         Spell|Skill|Weapon|Tongue|Herb
Target       <대상타입>
Mana         <마나비용>
Code         <C함수명>
Dammsg       <데미지메시지>~
Wearoff      <종료메시지>~
Affect       '<지속시간>' <위치> '<수정치>' <비트벡터>
End
```

### 6.3 명령어 포맷 (#COMMAND)

```
#COMMAND
Name        <명령어명>~
Code        <C함수명>
Position    <최소포지션>
Level       <최소레벨>
Log         <로그타입>
End
```

---

## 7. 도움말 (도움말 파일)

- 593KB, 16,001줄
- ~326 도움말 항목
- SMAUG 표준 `#HELPS` 포맷
- 한국어+영어 혼합

---

## 8. 클랜/신/의회

### 8.1 클랜 (1개)

- 영원한제국 (dragonet)
- 포맷: #CLAN / Name / Leader / Members / Board / Recall 등

### 8.2 신 (2개)

- 필마리온, Test
- 포맷: #DEITY / Alignment / Worshippers / Favour 시스템

### 8.3 의회 (2개)

- 운영진, 펠리아스
- 포맷: #COUNCIL / Head / Members / Board / Powers

---

## 9. 플레이어 파일

```
#사용자
Version     3
Name        <이름>~
Sex/Race/Class/Level/Homeroom
HpManaMove  <hp> <maxhp> <mana> <maxmana> <move> <maxmove>
Gold/Balance/Exp
AttrPerm    <str> <dex> <wis> <int> <con> <cha> <lck>
Password    <평문비밀번호>~    ← NOCRYPT 정의!
```

**주의**: 비밀번호 평문 저장 (NOCRYPT).

---

## 10. 소스 코드 (src/)

| 파일 | 크기 | 설명 |
|------|------|------|
| mud.h | 172KB | 메인 헤더 (모든 struct) |
| db.c | 174KB | DB 로더 (에리어 파서) |
| build.c | 220KB | OLC 빌더 |
| act_wiz.c | 281KB | 불멸자 명령 |
| magic.c | 176KB | 스펠 구현 |
| skills.c | 151KB | 스킬 시스템 |
| tables.c | 114KB | 조회 테이블 |
| fight.c | 102KB | 전투 시스템 |
| kstbl.h | 18KB | 한국어 인코딩 테이블 (KS 완성형 2350자) |
| const.c | 16KB | 상수 (NPC종족 91개) |

### 10.1 주요 상수 (mud.h)

```c
MAX_LEVEL    777
MAX_CLASS    30
MAX_RACE     8 (player) / 91 (NPC)
MAX_SKILL    400
MAX_CLAN     50
MAX_DEITY    50
MAX_REXITS   20    // 방당 최대 출구
MAX_LAYERS   8     // 의복 레이어
MAX_WEAR     22    // 착용 위치
```

### 10.2 레벨 계층

```
LEVEL_HERO      762  (MAX_LEVEL - 15)
LEVEL_IMMORTAL  763
LEVEL_SUPREME   777  (MAX_LEVEL)
```

---

## 11. 색상 코드

SMAUG `&` 접두사 코드:
- `&W` = 흰색, `&w` = 회색, `&z` = 진회색
- `&g` = 녹색, `&Y` = 노랑, `&R` = 빨강 등
- GenOS `{코드}` 포맷으로 변환 필요

---

## 12. 데이터 규모 요약

| 엔티티 | 수량 |
|--------|------|
| 활성 에리어 | 53 |
| 총 VNUM 엔트리 | ~7,348 |
| 추정 방 | ~2,500-3,000 |
| 추정 몬스터 | ~1,500-2,000 |
| 추정 아이템 | ~1,500-2,000 |
| 클래스 (플레이어) | 30 |
| 종족 (플레이어) | 8 |
| NPC 종족 | 91 |
| 스킬/스펠 | 54 |
| 명령어 | 488 |
| 도움말 | ~326 |
| 소셜 | 7 |
| 클랜 | 1 |
| 신 | 2 |
| 의회 | 2 |

---

## 13. 마이그레이션 고려사항

### 13.1 완전히 새로운 어댑터 필요

SMAUG 에리어 파일 포맷은 기존 4개 어댑터(CircleMUD/Simoon/3eyes/LPMud)와
호환되지 않음. 새로운 SmaugAdapter 필요:

1. **에리어 파일 파서**: #AREA → #MOBILES → #OBJECTS → #ROOMS → #RESETS → #SHOPS
2. **MOB S/C 타입**: 단순(3줄)/복잡(8줄) 두 가지 포맷
3. **Direction 10**: "somewhere" 11번째 방향 (포탈/특수 출구)
4. **확장 bitvector**: SMAUG 128-bit (4×32)
5. **외부 데이터 파일**: skills.dat, 명령어.dat, socials.dat → 별도 파서

### 13.2 인코딩

EUC-KR → UTF-8 변환 필요. kstbl.h에 KS 완성형 2,350자 매핑 테이블 존재.

### 13.3 색상 코드

SMAUG `&` 코드 → GenOS `{코드}` 포맷 변환 규칙 추가 필요.

### 13.4 클래스/종족

외부 파일(.class/.종족)에서 정의 — C 소스 파싱 대신 파일 파싱.

### 13.5 비밀번호

평문 저장 (NOCRYPT). 마이그레이션 시 bcrypt/argon2 해싱 필수.

### 13.6 존목록 (boot list)

에리어 로드 순서가 `존목록` 파일로 정의됨. 48개 항목 + `$` 종료.
