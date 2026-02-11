# 99hunter (더 헌터, SMAUG MUD) 데이터 전수조사

> 최종 업데이트: 2026-02-12 | 심층 분석 + 런타임 메커닉 분석 완료

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

---

## 14. 런타임 메커닉

> 소스: `src/fight.c` (102KB) 심층 분석

### 14.1 타이밍 — violence_update

SMAUG 표준 `violence_update()` 루프 (fight.c:203). PULSE_VIOLENCE 주기마다 호출.

**매 전투 라운드 처리 순서**:

| 순서 | 처리 | 설명 |
|------|------|------|
| 1 | 경험치 감쇠 | `duration % 24 == 0` → `xp = (xp * 9) / 10` |
| 2 | 타이머 처리 | TIMER_DO_FUN 콜백, TIMER_ASUPRESSED, TIMER_NUISANCE |
| 3 | 지속 효과 | affect.duration-- → 0이면 msg_off 출력 + 제거 |
| 4 | pullcheck | 이동 출구 자동 당김 검사 |
| 5 | 전투 실행 | `multi_hit(ch, victim, TYPE_UNDEFINED)` |
| 6 | 트리거 | `rprog_rfight_trigger`, `mprog_hitprcnt_trigger` |

경험치 감쇠: 전투 24라운드마다 10% 감소 → 장기전 패널티.

### 14.2 multi_hit — 다타 공격

**multi_hit()** (fight.c:699):

```
1. PK 타이머 — 양쪽에 TIMER_RECENTFIGHT=11 라운드
2. 1타 필수 — one_hit() (backstab/circle이면 여기서 종료)
3. Berserk — AFF_BERSERK이면 추가 1타 (NPC 100%, PC gsn_berserk*5/2 %)
4. 이도류 — dual_wield 스킬/2 확률로 추가 1타, dual_bonus = 스킬/10
5. NPC numattacks — 0보다 크면 numattacks회 추가 공격
6. 2nd attack — NPC: level/2,  PC: (gsn_second_attack + dual_bonus) / 1.5
7. 3rd attack — NPC: level/3,  PC: gsn_third_attack + dual_bonus/2
8. 4th attack — NPC: level/4,  PC: (gsn_fourth_attack + dual_bonus*2) / 3
9. 5th attack — NPC: level/5,  PC: (gsn_fifth_attack + dual_bonus*2) / 4
10. NPC 추가 — level/4 확률로 1타 더
11. 이동력 소모 — 비행/부유 아니면 지형 기반 이동력 소모
```

이동력 < 10이면 dual_bonus = -20 (피로 패널티).

### 14.3 one_hit — 단일 공격

**one_hit()** (fight.c:927):

```
1. 무기 결정: dual_wield면 번갈아 사용 (dual_flip 토글)
2. 무기 숙련도 보너스: weapon_prof_bonus_check()
   - 무기 타입별 gsn 매핑 (장검/단검/도끼/창/둔기/미사일 등)
   - 보너스 = (learned - 50) / 10

3. NPC 특수 공격 (ch->attacks에 설정):
   - ATCK_BITE/CLAWS/TAIL/STING/PUNCH/KICK
   - 무기 있으면 25%, 없으면 50% 확률로 발동

4. THAC0 계산:
   - NPC: ch->mobthac0 (에리어 파일에서 설정)
   - PC: interpolate(level, class.thac0_00, class.thac0_32) - hitroll
   - victim_ac = GET_AC(victim) / 10  (최소 -19)
   - 보이지 않는 무기: victim_ac += 1
   - 못 보는 대상: victim_ac -= 4

5. 지능 학습 보정:
   - intdiff = ch.int - victim.int
   - victim_ac += (intdiff * timeskilled) / 10

6. d20 판정:
   - diceroll = number_bits(5)  (0-19 범위)
   - 0 = 자동 빗나감
   - 19 = 자동 명중
   - 그 외: diceroll < thac0 - victim_ac → 빗나감
```

### 14.4 데미지 계산

```
맨손: number_range(barenumdie, baresizedie * barenumdie)
무기: number_range(value[1], value[2])

+ DAMROLL
+ prof_bonus / 4

전투 스타일 보정 (양쪽 모두 적용):
  berserk:    x1.2
  aggressive: x1.1
  defensive:  x0.85
  evasive:    x0.8

enhanced_damage 스킬: + dam * learned / EH_BONUS

수면 상태: x2
backstab:   x3
circle:     x3

최소: dam = 1 (0 이하 시)
```

### 14.5 RIS 시스템 (저항/면역/취약)

**무기 등급 (Plus) 판정**:

```
plusris = obj_hitroll(weapon)
victim의 immune/resistant/susceptible과 비교:
  - immune >= plusris  → modifier -= 10
  - resistant >= plusris → modifier -= 3
  - susceptible <= plusris → modifier += 3
  - modifier ≤ 0 → 면역 (dam = -1)
  - dam = (dam * modifier) / 10
```

**데미지 타입별 RIS** (damage() 함수, fight.c:1644):

| 카테고리 | 타입 |
|----------|------|
| 원소 | fire, cold, acid, electricity, energy |
| 기타 | drain, poison |
| 물리 | blunt (pound/crush/stone/pea) |
| | pierce (stab/pierce/bite/bolt/dart/arrow) |
| | slash (slice/slash/axe/claw) |
| 마법 | magic (스펠), nonmagic (무기, plus=0일 때) |

ris_damage(): immune → -10, resistant → -3, susceptible → +3, modifier/10.

### 14.6 damage() — 데미지 적용

**damage() 함수** (fight.c:1644):

```
1. RIS 타입 체크 (14.5 참조)
2. ROOM_SAFE → dam = 0
3. NPC 행동 설정:
   - hunting: 공격자를 추적 대상으로 등록
   - hating: 공격자를 적대 대상으로 등록
4. 최대 데미지 제한:
   - backstab: level * 2000
   - 일반:     level * 1000

5. 전투 개시: set_fighting() 양쪽
6. 은신/투명 해제 → dam += dam/2 보너스
7. sanctuary → dam /= 2
8. protect → dam -= dam/4

9. AC 차감 (물리 공격만):
   - PC: dam -= (100 - GET_AC)
   - NPC lv>150: dam -= (100 - GET_AC) * 2
   - NPC lv>25:  dam -= (100 - GET_AC)
   - 최소 1

10. 독무기: dam += dam/2 (save 실패 시 + 독 지속효과)
11. 방어 체크: disarm / trip / parry / dodge / tumble
12. 제어판 보정: sysdata.dam_X_vs_Y (퍼센트)
    - plr vs mob, plr vs plr(33%), mob vs plr(100%), mob vs mob
13. 장비 손상: dam > 100 → 랜덤 부위, 25% 확률 damage_obj

victim.hit -= dam
```

### 14.7 사망 처리

```
victim.position == POS_DEAD:
1. group_gain(ch, victim) — 그룹 경험치 배분
2. 플레이어 사망: 로그 기록, 채널 알림, 클랜 기록
   - 사망 패널티: 주석 처리됨! (1/2 way back 비활성)
3. NPC 사망: add_kill (킬 카운트)
4. check_killer → legal_loot → raw_kill
5. 자동 루팅:
   - PLR_AUTOGOLD → "금화 시체" → split
   - PLR_AUTOLOOT → "모두 시체"
   - PLR_AUTOSAC  → "시체" 제물

포지션별 메시지:
  POS_MORTAL:  "심각한 부상, 치료하지 않으면 곧 죽을 것"
  POS_INCAP:   "부상을 입었고, 치료하지 않으면 천천히 죽을 것"
  POS_STUNNED: "기절하였으나, 곧 회복할 것"
  POS_DEAD:    "당신은 $N을 죽였습니다!"
```

### 14.8 NPC 행동 AI

| 행동 | 트리거 | 설명 |
|------|--------|------|
| hunting | 피격 시 | 공격자 추적 (비 SENTINEL + 비 PACIFIST) |
| hating | 피격 시 | 공격자 적대 |
| fearing | HP < 50% | ACT_WIMPY NPC → 50% flee |
| DFND_DISARM | level/3% | 무기 해제 (레벨 9+) |
| DFND_TRIP | level/2% | 넘어뜨리기 (레벨 5+) |
| ATCK_* | 25-50% | 특수 공격 (물기/할퀴기/꼬리/침/주먹/발차기) |

NPC 방어 스킬 (violence_update에서 발동):

| 플래그 | 행동 |
|--------|------|
| DFND_CURELIGHT~CURECRITICAL | 자가 치유 |
| DFND_HEAL | 대치유 |
| DFND_SANCTUARY | 생츄어리 시전 |

### 14.9 PvP 시스템

```
sysdata.dam_plr_vs_plr = 33     → PvP 데미지 33%
TIMER_RECENTFIGHT = 11 라운드    → PK 타이머
PLR_NICE → 공격 불가
ROOM_SAFE → dam = 0 (전쟁 중 제외)
is_in_war() → SAFE 방에서도 전투 허용
```

### 14.10 전투 스타일

```c
#define STYLE_EVASIVE     0    /* POS_EVASIVE    — dam x0.8 */
#define STYLE_DEFENSIVE   1    /* POS_DEFENSIVE  — dam x0.85 */
#define STYLE_AGGRESSIVE  2    /* POS_AGGRESSIVE — dam x1.1 */
#define STYLE_BERSERK     3    /* POS_BERSERK    — dam x1.2 */
```

공격자와 방어자 모두 적용 → 최대 x1.44 (berserk vs berserk).

### 14.11 뱀파이어 시스템

```
피해 >= max_hit/10  → 혈갈 -1-(level/20)
HP <= max_hit/8 + 혈갈>5  → 혈갈 소모로 HP 회복
  회복량: URANGE(4, max_hit/30, 15)
```

### 14.12 기타 메커닉

| 메커닉 | 설명 |
|--------|------|
| 무기 숙련도 학습 | 명중/빗나감 시 learn_from_success/failure |
| 무기 스펠 | 명중 시 APPLY_WEAPONSPELL 발동 |
| magic shield 반격 | fireshield/iceshield/shockshield |
| 장비 손상 | dam>100 → 랜덤 부위 25% 파손 (dam -5), 장비 없으면 dam +5 |
| 링크 데드 | 접속 끊긴 PC → NORECALL 아니면 recall 시도 |
| wimpy | PC: hit≤wimpy → auto flee, NPC: ACT_WIMPY + HP<50% |

### 14.13 DB 설계 포인트

| 런타임 요소 | DB/엔진 적용 |
|-------------|-------------|
| violence_update | Python asyncio 전투 루프 |
| multi_hit 다타 | NPC numattacks + 스킬별 공격 횟수 |
| THAC0 보간 | class.thac0_00/thac0_32 → 레벨별 보간 |
| RIS 시스템 | mobs.extensions에 immune/resistant/susceptible 비트벡터 |
| fighting style | 인메모리 상태, 스타일별 배율 상수 |
| hunting/hating/fearing | 인메모리 NPC AI 상태 |
| sysdata 제어판 | game_configs 테이블 (dam_plr_vs_mob 등) |
| 경험치 감쇠 | 전투 duration 카운터 (24라운드 주기 10% 감소) |
| 장비 손상 | 내구도 시스템 (items.extensions) |
| 무기 숙련도 | players.skills JSONB (learned 0-100) |
| PK 타이머 | 인메모리 타이머 (11 라운드) |
| 뱀파이어 혈갈 | players.conditions JSONB |
