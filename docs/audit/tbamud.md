# tbaMUD (CircleMUD) 데이터 전수조사

> 최종 업데이트: 2026-02-12 | 런타임 메커닉 분석 포함

## 1. 데이터 파일 구조

### lib/world/ — 189개 존 (확장자별)

| 확장자 | 수량 | 용도 | 현재 파싱 |
|--------|------|------|-----------|
| .wld | 189 | 방 (12,700) | **YES** |
| .mob | 189 | 몬스터 (3,705) | **YES** |
| .obj | 189 | 아이템 (4,765) | **YES** |
| .zon | 189 | 존 리셋 (189존, 17,545 cmds) | **YES** |
| .shp | 189 | 상점 (334) | **YES** |
| .trg | 189 | DG Script 트리거 (1,461) | **YES** |
| .qst | 8 | 퀘스트 | **YES** |
| .mini | 8 | 인덱스 파일 (로드 순서 정의) | **NO** |

### lib/misc/ — 시스템 파일

| 파일 | 크기 | 용도 | 현재 파싱 |
|------|------|------|-----------|
| messages | 29KB | **전투 메시지** (스킬별 hit/miss/kill/god 4종) | **NO** |
| socials | 18KB | 소셜 커맨드 (104개) | **YES** |
| socials.new | 210KB | 확장 소셜 (미사용?) | NO |
| xnames | 0.1KB | 금지 이름 목록 | NO |

### lib/text/ — 텍스트 파일

| 파일 | 크기 | 줄 수 | 용도 | 현재 파싱 |
|------|------|-------|------|-----------|
| greetings | 281B | 8 | 로그인 인트로 (ASCII 아트) | **NO** |
| motd | 197B | 5 | 오늘의 메시지 | **NO** |
| imotd | 390B | 12 | 관리자 메시지 | **NO** |
| news | 4.5KB | 113 | 뉴스/패치노트 | **NO** |
| info | 2.1KB | 49 | 게임 정보 | **NO** |
| credits | 1.3KB | 32 | 크레딧 | **NO** |
| background | 202B | 9 | 배경 스토리 | **NO** |
| policies | 218B | 9 | 정책 | **NO** |
| handbook | 291B | 10 | 관리자 핸드북 | NO |
| wizlist | 512B | - | 관리자 목록 | NO |
| immlist | 332B | - | 불멸자 목록 | NO |
| help/ | 6 files | - | 도움말 | **YES** (별도 .hlp) |

### lib/house/ — 플레이어 하우스

- 1개 파일 (60B) — 하우스 시스템은 원본에서도 미니멀

---

## 2. 소스 코드 기반 데이터 (src/)

### 현재 파싱 중

| 소스 파일 | 추출 데이터 | 파서 |
|-----------|-------------|------|
| spell_parser.c | spello() 54개 스킬 정의 | skill_parser.py |
| interpreter.c | ACMD() 275개 명령 정의 | cmd_parser.py |
| config.c | 게임 설정값 | config_parser.py |
| class.c | 경험치/THAC0/세이빙/타이틀 테이블 | config_parser.py |
| constants.c | 상수 정의 | config_parser.py |

### 누락 — 중요

| 소스 파일 | 추출 가능 데이터 | 중요도 |
|-----------|-----------------|--------|
| fight.c / lib/misc/messages | **전투 메시지** — 스킬당 4 메시지셋 × 3 대상 | 높음 |
| lib/text/* | 로그인 화면, MOTD, 뉴스 등 | 중간 |

---

## 3. 전투 메시지 (lib/misc/messages)

> 소스: 864줄, 55개 M 블록 심층 분석

### 3.1 포맷

```
M                           ← 블록 시작
{skill_num}                 ← 스킬/무기 번호
{die_to_char}               ← 사망 시 시전자에게
{die_to_victim}             ← 사망 시 대상에게
{die_to_room}               ← 사망 시 방 전체에게
{miss_to_char}              ← 미스 시 시전자
{miss_to_victim}            ← 미스 시 대상
{miss_to_room}              ← 미스 시 방
{hit_to_char}               ← 적중 시 시전자
{hit_to_victim}             ← 적중 시 대상
{hit_to_room}               ← 적중 시 방
{god_to_char}               ← 신급 시 시전자
{god_to_victim}             ← 신급 시 대상
{god_to_room}               ← 신급 시 방
```

### 3.2 변수

| 변수 | 의미 |
|------|------|
| $n/$N | 시전자/대상 이름 |
| $s/$S | 시전자/대상 소유격 (his/her) |
| $m/$M | 시전자/대상 목적격 (him/her) |
| $e/$E | 시전자/대상 주격대명사 (he/she) |
| # | 빈 메시지 (미표시) |
| * | 주석 |

### 3.3 55개 블록 분류

| 분류 | 수량 | 예시 |
|------|------|------|
| 스펠 | 14 | burning hands, shocking grasp, color spray |
| 스킬 | 4 | backstab, bash, whirlwind, sting |
| 무기 | 32 | hit/sting/whip/slash/bite/bludgeon/crush/pound/claw/maul/thrash/pierce/blast/punch/stab/suffering 등 |
| 상태 | 2 | poison, wrath of god |
| 미사용 | 5 | TYPE_UNDEFINED, reserved |

---

## 4. 스펠/스킬 시스템 (spell_parser.c)

### 4.1 spello() 10인자

```c
spello(spl, name, max_mana, min_mana, mana_change,
       minpos, targets, violent, routines, wearoff)
```

### 4.2 MAG_* 루틴 플래그 (12종)

| 플래그 | 의미 |
|--------|------|
| MAG_DAMAGE | 직접 데미지 |
| MAG_AFFECTS | 효과 부여 (버프/디버프) |
| MAG_UNAFFECTS | 효과 제거 |
| MAG_POINTS | HP/MP 회복 |
| MAG_ALTER_OBJS | 아이템 변경 |
| MAG_GROUPS | 그룹 대상 |
| MAG_MASSES | 대량 대상 |
| MAG_AREAS | 범위 대상 |
| MAG_SUMMONS | 소환 |
| MAG_CREATIONS | 생성 |
| MAG_MANUAL | 수동 처리 |
| MAG_ROOMS | 방 효과 |

### 4.3 TAR_* 타겟 플래그 (11종)

| 플래그 | 의미 |
|--------|------|
| TAR_IGNORE | 타겟 없음 |
| TAR_CHAR_ROOM | 같은 방 캐릭터 |
| TAR_CHAR_WORLD | 월드 내 캐릭터 |
| TAR_FIGHT_SELF | 전투중 자신 |
| TAR_FIGHT_VICT | 전투중 상대 |
| TAR_SELF_ONLY | 자신만 |
| TAR_NOT_SELF | 자신 제외 |
| TAR_OBJ_INV | 인벤토리 아이템 |
| TAR_OBJ_ROOM | 방 아이템 |
| TAR_OBJ_WORLD | 월드 아이템 |
| TAR_OBJ_EQUIP | 장비 아이템 |

### 4.4 Saving Throw (5종)

PARA / ROD / PETRI / BREATH / SPELL

---

## 5. House 시스템 (house.h/house.c)

| 속성 | 값 |
|------|-----|
| MAX_HOUSES | 100 |
| MAX_GUESTS | 10 per house |
| 구조 | vnum/atrium/exit_num/built_on/mode/owner/guests[10] |

---

## 6. .mini 파일

`.mini` 파일은 **인덱스 파일**로서 로드 순서를 정의함 (시각적 미니맵 아님).
각 존 디렉토리(wld, obj, mob, zon, shp, qst)에서 어떤 파일을 어떤 순서로 로드할지 나열.

---

## 7. DG Script 변수

- `trig_var_data` 구조: name/value/context
- 런타임 동적 생성 — 데이터 파일에는 없음
- 스크립트 본문에서 `%self.gold%`, `%actor.skill(slash)%` 등으로 참조

---

## 8. 파일 포맷별 필드 커버리지

### WLD (방) — 100% 파싱

| 필드 | 파싱 |
|------|------|
| vnum, name, description, zone_number | YES |
| room_flags (128-bit bitvector, 4 dword) | YES |
| sector_type | YES |
| exits (6방향, door_flags/key_vnum/destination) | YES |
| extra_descriptions | YES |
| trigger attachments (T lines after S) | YES |

### MOB (몬스터) — 100% 파싱

| 필드 | 파싱 |
|------|------|
| vnum, keywords, descriptions (short/long/detailed) | YES |
| action_flags, affect_flags (128-bit) | YES |
| alignment, mob_type, level, hitroll, armor_class | YES |
| hp_dice, damage_dice, damroll | YES |
| gold, experience, position, sex, weight, height | YES |
| E (enhanced mob) section | YES |
| trigger attachments | YES |

### OBJ (아이템) — 100% 파싱

| 필드 | 파싱 |
|------|------|
| vnum, keywords, descriptions | YES |
| item_type, extra_flags, wear_flags (128-bit) | YES |
| values[0-3], weight, cost, rent | YES |
| affects, extra_descriptions | YES |
| trigger attachments | YES |

### ZON/SHP/TRG/QST — 모두 100% 파싱

---

## 9. 커버리지 요약

### 현재 (재평가: ~92%)

| 카테고리 | 파싱 비율 | 비고 |
|----------|-----------|------|
| 방 | **100%** | 전 필드 파싱 |
| 몬스터 | **100%** | 전 필드 파싱 |
| 아이템 | **100%** | 전 필드 파싱 |
| 존 리셋 | **100%** | 전 커맨드 파싱 |
| 상점 | **100%** | |
| 트리거 | **100%** | |
| 퀘스트 | **100%** | |
| 소셜 | **100%** | |
| 도움말 | **100%** | .hlp 파싱 |
| 명령어 | **100%** | interpreter.c에서 추출 |
| 스킬 | **100%** | spello()에서 추출 |
| 게임 설정 | **100%** | config/class/constants 파싱 |
| **전투 메시지** | **0%** | 55M블록×12줄, messages 파일 미파싱 |
| **텍스트 파일** | **0%** | greetings/motd/news 등 8개 |
| **미니맵(.mini)** | **0%** | 인덱스 파일 (선택적) |

### 95% 달성 필요 작업

1. **전투 메시지 파서** — lib/misc/messages 파싱 (55블록×12줄 메시지)
2. **텍스트 파일 추출** — greetings, motd, news, info, background, credits, policies (8개)
3. (선택) .mini 인덱스 파일 — 로드 순서 참조용

---

## 10. 런타임 메커닉 (소스 코드 분석)

> 소스: fight.c(990줄), limits.c(531줄), act.movement.c(993줄), act.comm.c(544줄),
> shop.c(1673줄), objsave.c(1373줄), dg_scripts.c(3156줄), interpreter.c(1800줄), db.c

### 10.1 타이밍 시스템 (structs.h + comm.c)

```
OPT_USEC        = 100000      (100ms/tick = 10 ticks/sec)
PASSES_PER_SEC  = 10
PULSE_VIOLENCE  = 2초         (전투 라운드)
PULSE_MOBILE    = 10초        (몹 행동)
PULSE_ZONE      = 10초        (존 리셋 큐)
PULSE_AUTOSAVE  = 60초        (자동 저장)
PULSE_DG_SCRIPT = 13초        (DG 스크립트)
PULSE_IDLEPWD   = 15초
PULSE_SANITY    = 30초
PULSE_USAGE     = 5분
PULSE_TIMESAVE  = 30분
point_update    = 75초 (1 게임시간 = 75 실제초)
```

### 10.2 전투 시스템 (fight.c)

#### 전투 라운드 플로우 (perform_violence → 매 2초)

```
for each ch in combat_list:
  1. FIGHTING(ch) 유효성 확인 (없거나 다른 방이면 stop)
  2. NPC wait 카운터 차감 (GET_MOB_WAIT -= PULSE_VIOLENCE)
  3. 자세 확인 (POS_FIGHTING 미만이면 skip)
  4. 그룹 자동 지원 (PRF_AUTOASSIST)
  5. hit(ch, FIGHTING(ch))
  6. MOB_SPEC 특수 함수 호출
```

#### 명중 판정 (hit → compute_thaco)

```c
THAC0 = thaco(class, level)
      - str_app[STR].tohit
      - hitroll
      - (INT - 13) / 1.5
      - (WIS - 13) / 1.5

victim_AC = GET_AC(victim) + dex_app[DEX].defensive × 10
victim_AC = MAX(-100, victim_AC) / 10

diceroll = rand(1, 20)
  20 또는 잠든 대상 → 자동 명중
  1 → 자동 실패
  그 외 → (THAC0 - diceroll) <= victim_AC 이면 명중
```

#### 데미지 계산 (hit)

```c
dam = str_app[STR].todam + damroll
if (무기 장비):
    dam += dice(weapon_val1, weapon_val2)
else if (NPC):
    dam += dice(damnodice, damsizedice)
else:
    dam += rand(0, 2)  // 플레이어 맨손 최대 2

// 자세 보정 (앉아있으면 증가)
if (victim_pos < POS_FIGHTING):
    dam *= 1 + (POS_FIGHTING - pos) / 3
    // sitting=1.33x, resting=1.66x, sleeping=2x

// 백스탭
if (backstab): dam *= backstab_mult(level)

// 최소 1, 최대 100
dam = MAX(1, MIN(dam, 100))
```

#### 데미지 적용 (damage)

```
1. Sanctuary → dam /= 2
2. GET_HIT(victim) -= dam
3. 공격자 전투 경험치 += victim_level × dam
4. update_pos (HP 기반 상태 결정):
   HP > 0     → 변화 없음
   HP 0..-2   → STUNNED
   HP -3..-5  → INCAP (매 틱 1 데미지)
   HP -6..-10 → MORTALLYW (매 틱 2 데미지)
   HP <= -11  → DEAD
5. wimpy: HP < wimp_level이면 자동 도주
6. DEAD → 경험치 분배 → die()
```

#### 사망 처리 (die → raw_kill → make_corpse)

```
die():
  경험치 페널티 = -(현재 EXP / 2)
  KILLER/THIEF 플래그 제거

raw_kill():
  전투 중지 → 모든 affect 제거 → death_mtrigger
  → death_cry (인접 방까지 전달) → autoquest 체크
  → make_corpse() → extract_char()

make_corpse():
  시체 오브젝트 생성 (ITEM_CONTAINER)
  인벤토리 전부 → 시체로 이동
  장비 전부 → unequip → 시체로 이동
  골드 → money 오브젝트로 변환 → 시체
  NPC 시체 타이머: CONFIG_MAX_NPC_CORPSE_TIME
  PC 시체 타이머:  CONFIG_MAX_PC_CORPSE_TIME
```

#### 경험치 분배

```
솔로:
  exp = MIN(MAX_EXP_GAIN, victim_exp / 3)
  레벨차 보정: + MAX(0, exp × MIN(8, victim_lv - ch_lv) / 8)
  해피아워: + exp × HAPPY_EXP / 100

그룹:
  tot_gain = victim_exp / 3
  base = tot_gain / 같은 방 멤버 수
  각 멤버에게 MIN(MAX_EXP_GAIN, base) 분배
```

#### 데미지 메시지 분기 (9단계)

| 데미지 | 표현 |
|--------|------|
| 0 | misses |
| 1-2 | tickles |
| 3-4 | barely |
| 5-6 | #W |
| 7-10 | hard |
| 11-14 | very hard |
| 15-19 | extremely hard |
| 20-23 | massacres |
| 24+ | OBLITERATES |

### 10.3 이동 시스템 (act.movement.c)

#### 이동력 소모 공식

```c
need_movement = (movement_loss[sector_src] + movement_loss[sector_dst]) / 2
```

movement_loss 배열 (constants.c):
| 섹터 | 비용 |
|------|------|
| INSIDE | 1 |
| CITY | 1 |
| FIELD | 2 |
| FOREST | 3 |
| HILLS | 4 |
| MOUNTAIN | 6 |
| WATER_SWIM | 4 |
| WATER_NOSWIM | 6 (보트 필요) |
| FLYING | 1 (비행 필요) |
| UNDERWATER | 5 (스쿠버 필요) |

#### 이동 조건 체크 순서

```
1. special proc 체크
2. leave_mtrigger / leave_wtrigger / leave_otrigger
3. CHARM 효과 (주인이 같은 방이면 이동 불가)
4. 물/비행/수중 조건 (보트/비행/스쿠버)
5. 하우스 권한
6. 존 레벨/플래그 제한
7. 터널 인원 제한
8. 이동력 부족 체크
9. → 이동 실행 → 도착 → entry/greet 트리거
10. DEATH TRAP 방 → 즉사
```

#### 문 시스템

```
5가지 명령: open / close / unlock / lock / pick
양방향 동기화: 문 상태 변경 시 반대편 방도 동시 변경
pick: rand(1,101) vs (SKILL_PICK_LOCK + dex_app_skill.p_locks)
PICKPROOF 플래그 → 따개 불가
```

### 10.4 리젠/업데이트 시스템 (limits.c)

#### HP/Mana/Move 리젠 (point_update, 매 75초)

```
HP 리젠:
  NPC: level
  PC: graf(age, 8,12,20,32,16,10,4)
  자세: sleeping ×1.5, resting ×1.25, sitting ×1.125
  마법직: ÷2
  배고픔/목마름=0: ÷4
  독: ÷4

Mana 리젠:
  NPC: level
  PC: graf(age, 4,8,12,16,12,10,8)
  자세: sleeping ×2, resting ×1.5, sitting ×1.25
  마법직: ×2
  배고픔/목마름=0: ÷4
  독: ÷4

Move 리젠:
  NPC: level
  PC: graf(age, 16,20,24,20,16,12,10)
  자세: sleeping ×1.5, resting ×1.25, sitting ×1.125
  배고픔/목마름=0: ÷4
  독: ÷4

graf(age, p0,p1,p2,p3,p4,p5,p6):
  <15세: p0, 15-29: p1→p2 선형, 30-44: p2→p3, 45-59: p3→p4, 60-79: p4→p5, 80+: p6
```

#### 허기/갈증 시스템

```
매 point_update (75초):
  HUNGER -1, THIRST -1, DRUNK -1
  범위: 0~24 (-1 = 면역)
  HUNGER=0 또는 THIRST=0 → 리젠 ÷4
```

#### 독 데미지

```
매 point_update: AFF_POISON → damage(self, 2, SPELL_POISON)
```

#### 상태별 자동 데미지

```
POS_INCAP: damage(self, 1, TYPE_SUFFERING) — 매 틱
POS_MORTALLYW: damage(self, 2, TYPE_SUFFERING) — 매 틱
```

#### 시체 부패

```
매 point_update: 시체 타이머 -1
타이머 0 → 내용물 방에 드롭 → 시체 제거 ("maggots" 메시지)
```

### 10.5 유휴/저장 (limits.c + objsave.c)

```
idle_void: CONFIG_IDLE_VOID 이상 → void 방으로 이동
idle_rent: CONFIG_IDLE_RENT_TIME 이상 → 자동 로그아웃 + 저장
autosave: PULSE_AUTOSAVE (60초) → Crash_crashsave()
rent 시스템: offer_rent() → 일일 비용 계산 → reception()
```

### 10.6 통신 시스템 (act.comm.c)

| 채널 | 범위 | 제한 |
|------|------|------|
| say | 같은 방 | SOUNDPROOF 방 차단 |
| gsay | 그룹 멤버 | 그룹 필요 |
| tell | 전역 (아무 방) | NOTELL, 수면 시 수신 가능 |
| whisper | 같은 방, 특정 대상 | |
| shout | 존 전체 | 이동력 소모 |
| holler | 전역 | 마나 소모 |
| gossip | 전역 | NOGOSSIP 옵트아웃 |
| auction | 전역 | |
| grats | 전역 | |

모든 채널: add_history() → 채널별 히스토리 저장

### 10.7 존 리셋 (db.c reset_zone)

```
zone_update (매 PULSE_ZONE = 10초):
  zone.age++ (매 분)
  age >= lifespan → 리셋 큐에 추가
  age = ZO_DEAD (비활성화)

리셋 조건:
  reset_mode == 2 → 항상 리셋
  reset_mode == 1 → 플레이어 없을 때만 (is_empty)

리셋 명령:
  M: 몹 로드 (max_existing 체크)
  O: 오브젝트 로드 (방에)
  G: 오브젝트 → 마지막 로드된 몹 인벤토리
  E: 오브젝트 → 마지막 로드된 몹 장비
  P: 오브젝트 → 다른 오브젝트 안에
  D: 문 상태 설정
  T: 트리거 부착
  V: 변수 설정
```

### 10.8 DG Script 엔진 (dg_scripts.c)

```
실행 주기: PULSE_DG_SCRIPT = 13초 (타이머 기반)
최대 재귀: MAX_SCRIPT_DEPTH
while 루프: 30회 반복 후 자동 wait 1, 100회 → 강제 중단

명령어:
  제어: if/elseif/else/end, while/done/break, switch/case/default
  변수: set/unset/eval/extract/global/context/remote/rdelete
  동작: wait, halt, return, attach/detach
  특수: dg_cast, dg_affect, makeuid, dg_letter, nop
  일반: 등록된 모든 MUD 명령 실행 가능 (command_interpreter)

변수 시스템:
  로컬: 트리거별 (실행 후 해제)
  글로벌: 스크립트 전체
  context: 상태 번호 기반 네임스페이스
  remote: 다른 엔티티의 변수 접근
```

### 10.9 캐릭터 생성 (interpreter.c nanny())

```
상태 머신:
  CON_GET_NAME → CON_NAME_CNFRM → CON_PASSWORD → CON_NEWPASSWD
  → CON_CNFPASSWD → CON_QSEX → CON_QCLASS → CON_RMOTD → CON_MENU

생성 플로우:
  이름 입력 → 비밀번호 설정(2회) → 성별(M/F) → 클래스 선택
  → roll_real_abils() → MOTD 표시 → 메뉴

비밀번호: CRYPT() (DES/MD5 해시)
```

### 10.10 레벨업 (limits.c gain_exp)

```
exp >= level_exp(class, level+1) → 자동 레벨업
  advance_level(ch) 호출
  다중 레벨업 가능 (while 루프)
  LVL_IMMORT 도달 시 autowiz 실행
  제한: LVL_IMMORT - CONFIG_NO_MORT_TO_IMMORT

경험치 캡:
  획득: MIN(CONFIG_MAX_EXP_GAIN, exp)
  손실: MAX(-CONFIG_MAX_EXP_LOSS, loss)
  해피아워: +HAPPY_EXP% 보정
```

### 10.11 PK 시스템

```
CONFIG_PK_OFF    → PvP 완전 차단
CONFIG_PK_LIMITED → KILLER 플래그 부여 후 허용
CONFIG_PK_ON     → 무제한
ROOM_PEACEFUL    → 해당 방에서 전투 불가
```

### 10.12 DB 설계 영향 데이터 포인트

| 항목 | DB 테이블 영향 | 비고 |
|------|---------------|------|
| 전투 라운드 2초 | game_configs | PULSE_VIOLENCE |
| THAC0 공식 | 코드/Lua | class+level+str+hitroll+int+wis |
| 데미지 캡 100 | game_configs | MAX_DAM_PER_HIT |
| 사망 EXP -50% | game_configs | death_exp_penalty |
| 시체 타이머 | game_configs | npc_corpse_time, pc_corpse_time |
| 리젠 graf 공식 | stat_tables | 7포인트 나이별 보간 |
| movement_loss[10] | stat_tables | 섹터별 이동 비용 |
| 존 리셋 모드 0/1/2 | zones 테이블 | reset_mode 컬럼 |
| DG Script 변수 | runtime only | DB 저장 불필요 |
| 채널 히스토리 | runtime only | 세션 내 메모리 |
| 허기/갈증 0-24 | players 테이블 | conditions JSONB |
