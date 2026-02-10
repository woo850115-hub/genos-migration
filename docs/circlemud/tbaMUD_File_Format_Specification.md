# tbaMUD 데이터 파일 형식 사양서

**Version**: 1.0
**대상**: tbaMUD (CircleMUD 3.x 파생, 128-bit bitvector 확장)
**소스**: `/home/genos/workspace/tbamud/`
**참조**: `src/structs.h`, `src/constants.c`, `src/db.c`

---

## 목차

1. [개요](#1-개요)
2. [공통 규칙](#2-공통-규칙)
3. [World 파일 (.wld)](#3-world-파일-wld)
4. [Object 파일 (.obj)](#4-object-파일-obj)
5. [Mobile 파일 (.mob)](#5-mobile-파일-mob)
6. [Zone 파일 (.zon)](#6-zone-파일-zon)
7. [Trigger 파일 (.trg)](#7-trigger-파일-trg)
8. [Shop 파일 (.shp)](#8-shop-파일-shp)
9. [Quest 파일 (.qst)](#9-quest-파일-qst)
10. [Bitvector 인코딩](#10-bitvector-인코딩)
11. [Socials 파일](#11-socials-파일) (Phase 2)
12. [Help 파일 (.hlp)](#12-help-파일-hlp) (Phase 2)
13. [Commands — cmd_info[]](#13-commands--cmd_info) (Phase 2)
14. [Skills — spello()](#14-skills--spello) (Phase 2)

---

## 1. 개요

### 데이터 규모 (tbaMUD stock world)

| 타입 | 파일 수 | 엔티티 수 |
|------|---------|-----------|
| Room (.wld) | 189 | 12,700 |
| Object (.obj) | 189 | 4,765 |
| Mobile (.mob) | 189 | 3,705 |
| Zone (.zon) | 189 | 189 |
| Trigger (.trg) | 189 | 1,461 |
| Shop (.shp) | 189 | 334 |
| Quest (.qst) | 8 | 1 |
| Socials | 1 | 104 |
| Help (.hlp) | 1 | 721 |
| Commands (src) | - | 275 |
| Skills (src) | - | 54 |

### 파일 위치

월드 데이터 파일은 `lib/world/<type>/` 디렉토리 아래에, Phase 2 데이터는 `lib/misc/`, `lib/text/help/`, `src/` 아래에 있습니다.

```
lib/
├── world/
│   ├── wld/    # Room 정의
│   ├── obj/    # Object/Item 정의
│   ├── mob/    # Mobile/NPC 정의
│   ├── zon/    # Zone 설정 + 리셋 커맨드
│   ├── trg/    # DG Script 트리거
│   ├── shp/    # Shop 정의
│   └── qst/    # Quest 정의
├── misc/
│   └── socials # 소셜 커맨드 정의 (Phase 2)
└── text/
    └── help/   # 도움말 파일 (Phase 2)
        ├── index
        └── *.hlp

src/
├── interpreter.c  # cmd_info[] 배열 (Phase 2)
├── spell_parser.c # spello() 호출 (Phase 2)
├── spells.h       # SPELL_*/SKILL_* #define (Phase 2)
└── class.c        # spell_level() 호출 (Phase 2)
```

---

## 2. 공통 규칙

### 2.1 VNUM (Virtual Number)

모든 엔티티는 고유한 정수 ID(VNUM)로 식별됩니다. 각 파일은 `#<vnum>` 으로 시작하는 블록들의 연속이며, `$~` 또는 `$` 로 파일이 종료됩니다.

```
#0
(... 엔티티 데이터 ...)
#1
(... 엔티티 데이터 ...)
$~
```

### 2.2 Tilde (~) 구분자

문자열은 `~` 문자로 종료됩니다. 한 줄 문자열과 여러 줄 문자열 모두 동일한 규칙을 따릅니다.

```
한줄 문자열~
여러 줄
문자열은 이렇게
~
```

### 2.3 Asciiflag 인코딩

tbaMUD는 bitvector를 ASCII 문자로 인코딩합니다:
- 소문자 `a`-`z` → 비트 0-25
- 대문자 `A`-`Z` → 비트 26-51
- 숫자 문자열 → 그대로 정수 변환
- `0` → 비트 없음

예시:
- `a` → 비트 0 (1)
- `d` → 비트 3 (8)
- `ae` → 비트 0 + 비트 4 (17)
- `abcj` → 비트 0,1,2,9

### 2.4 128-bit Bitvector (tbaMUD 확장)

원래 CircleMUD는 단일 정수 bitvector를 사용했지만, tbaMUD는 이를 4개의 32-bit dword로 확장하여 128비트를 지원합니다. 파일에서는 4개의 asciiflag 필드로 나타납니다.

```
# 기존 CircleMUD (3-4 필드)
<type> <extra_flags> <wear_flags>

# tbaMUD 128-bit (13 필드)
<type> <ef0> <ef1> <ef2> <ef3> <wf0> <wf1> <wf2> <wf3> <af0> <af1> <af2> <af3>
```

**중요**: 현재 대부분의 데이터는 첫 번째 dword(0-31 비트)만 사용하며, 나머지 3개는 `0`입니다.

---

## 3. World 파일 (.wld)

### 형식

```
#<vnum>
<room_name>~
<room_description (여러 줄)>
~
<zone_num> <room_flags> <sector_type> [<unlinked> <previous> <map_x> [<map_y>]]
[D<direction>
 <exit_description>~
 <exit_keyword>~
 <door_flags> <key_vnum> <destination_room>
]...
[E
 <extra_keywords>~
 <extra_description>~
]...
S
[T <trigger_vnum>]...
```

### 핵심 주의사항

**T (trigger) 라인은 반드시 S 마커 이후에 위치합니다.** 이것은 `db.c`의 `parse_room()` 함수에서 확인할 수 있으며, S를 읽은 후 T 라인을 탐색합니다:

```c
case 'S':  /* end of room */
  letter = fread_letter(fl);
  ungetc(letter, fl);
  while (letter=='T') {
    dg_read_trigger(fl, &world[room_nr], WLD_TRIGGER);
    letter = fread_letter(fl);
    ungetc(letter, fl);
  }
```

### Room Flags 라인 (6-7 필드)

```
<zone_num> <flags> <sector> <unlinked> <previous> <map_x> [<map_y>]
```

| 필드 | 설명 | 예시 |
|------|------|------|
| zone_num | 존 번호 (레거시, 실제로는 .zon에서 범위로 결정) | `0` |
| flags | Room 플래그 (asciiflag) | `8` → INDOORS, `24` → INDOORS+PEACEFUL |
| sector | 지형 타입 (0-9) | `0` = INSIDE |
| unlinked | 미링크 여부 | `0` |
| previous | 이전 방 | `0` |
| map_x | 월드맵 X 좌표 | `1` |
| map_y | 월드맵 Y 좌표 (선택) | - |

### 방향 (Direction)

```
D<dir>
<look_description>~
<keyword>~
<door_flags> <key_vnum> <destination_room>
```

| dir | 방향 |
|-----|------|
| 0 | North |
| 1 | East |
| 2 | South |
| 3 | West |
| 4 | Up |
| 5 | Down |
| 6 | Northwest |
| 7 | Northeast |
| 8 | Southeast |
| 9 | Southwest |

Door flags (비트마스크):
- `1` (EX_ISDOOR) - 문이 있음
- `2` (EX_CLOSED) - 닫혀 있음
- `4` (EX_LOCKED) - 잠겨 있음
- `8` (EX_PICKPROOF) - 따개질 불가
- `16` (EX_HIDDEN) - 숨겨진 출구

### Sector Types

| 값 | 이름 | 설명 |
|----|------|------|
| 0 | INSIDE | 실내 |
| 1 | CITY | 도시 |
| 2 | FIELD | 평야 |
| 3 | FOREST | 숲 |
| 4 | HILLS | 언덕 |
| 5 | MOUNTAIN | 산 |
| 6 | WATER_SWIM | 수영 가능 물 |
| 7 | WATER_NOSWIM | 보트 필요 물 |
| 8 | FLYING | 비행 |
| 9 | UNDERWATER | 수중 |

### Room Flags

| 비트 | 이름 | 설명 |
|------|------|------|
| 0 | DARK | 빛이 필요함 |
| 1 | DEATH | 즉사 트랩 |
| 2 | NOMOB | NPC 진입 불가 |
| 3 | INDOORS | 실내 (날씨 없음) |
| 4 | PEACEFUL | 전투 불가 |
| 5 | SOUNDPROOF | 외침/잡담 차단 |
| 6 | NOTRACK | 추적 불가 |
| 7 | NOMAGIC | 마법 불가 |
| 8 | TUNNEL | 1인만 입장 |
| 9 | PRIVATE | 텔레포트 불가 |
| 10 | GODROOM | 신급 전용 |
| 11 | HOUSE | (R) 하우스 |
| 12 | HOUSE_CRASH | (R) 하우스 저장 필요 |
| 13 | ATRIUM | (R) 하우스 출입구 |
| 14 | OLC | (R) 수정 가능/비압축 |
| 15 | BFS_MARK | (R) BFS 검색 마크 |
| 16 | WORLDMAP | 월드맵 스타일 |

### 실제 예시

```
#20
Advanced Trigedit Example~
   Begin by @RSTAT GATEGUARD@n and then tstat each trigger listed...
~
0 24 0 0 0 0
D0
   The tutorial hallway continues.
~
gateway~
2 46 21
D2
~
~
0 0 18
S
```

여기서 `24` = 비트3(INDOORS) + 비트4(PEACEFUL), door `D0`(north)에 `gateway` 키워드가 있고 door_flags=2(CLOSED), key=46, dest=21.

---

## 4. Object 파일 (.obj)

### 형식

```
#<vnum>
<keywords>~
<short_description>~
<long_description>~
<action_description>~
<type> <ef0> <ef1> <ef2> <ef3> <wf0> <wf1> <wf2> <wf3> <af0> <af1> <af2> <af3>
<value0> <value1> <value2> <value3>
<weight> <cost> <rent> [<timer>] [<min_level>]
[E
 <extra_keywords>~
 <extra_description>~
]...
[A
 <apply_location> <modifier>
]...
[T <trigger_vnum>]...
```

### 핵심 주의사항

**128-bit 형식의 필드 위치**: 13필드 라인에서 wear_flags는 **인덱스 5**(6번째 필드)에 위치합니다.

```
type ef0 ef1 ef2 ef3 wf0 wf1 wf2 wf3 af0 af1 af2 af3
[0]  [1] [2] [3] [4] [5] [6] [7] [8] [9] [10][11][12]
```

- `[0]`: item_type (정수)
- `[1]-[4]`: extra_flags (128-bit, 4 dwords)
- `[5]-[8]`: wear_flags (128-bit, 4 dwords)
- `[9]-[12]`: affect_bitvector (128-bit, 4 dwords)

### Item Types

| 값 | 이름 | Values 해석 |
|----|------|-------------|
| 1 | LIGHT | v0=unused, v1=unused, v2=hours(-1=무한), v3=unused |
| 2 | SCROLL | v0=level, v1-v3=spell numbers |
| 3 | WAND | v0=level, v1=max_charges, v2=cur_charges, v3=spell |
| 4 | STAFF | v0=level, v1=max_charges, v2=cur_charges, v3=spell |
| 5 | WEAPON | v0=unused, v1=dice_num, v2=dice_size, v3=attack_type |
| 6 | FURNITURE | v0=max_people, v1=unused, v2=unused, v3=unused |
| 8 | TREASURE | 특별한 values 없음 |
| 9 | ARMOR | v0=AC_apply, v1-v3=unused |
| 10 | POTION | v0=level, v1-v3=spell numbers |
| 15 | CONTAINER | v0=capacity, v1=flags, v2=key_vnum, v3=unused |
| 17 | DRINKCON | v0=capacity, v1=current, v2=liquid_type, v3=poisoned |
| 18 | KEY | 특별한 values 없음 |
| 19 | FOOD | v0=hours_fill, v1=unused, v2=unused, v3=poisoned |
| 20 | MONEY | v0=gold_amount |
| 23 | FOUNTAIN | v0=capacity, v1=current, v2=liquid_type, v3=poisoned |

### Item Wear Flags (wf0 필드)

| 비트 | 이름 | 장착 위치 |
|------|------|-----------|
| 0 | TAKE | 주울 수 있음 |
| 1 | FINGER | 손가락 |
| 2 | NECK | 목 |
| 3 | BODY | 몸통 |
| 4 | HEAD | 머리 |
| 5 | LEGS | 다리 |
| 6 | FEET | 발 |
| 7 | HANDS | 손 |
| 8 | ARMS | 팔 |
| 9 | SHIELD | 방패 |
| 10 | ABOUT | 어깨/망토 |
| 11 | WAIST | 허리 |
| 12 | WRIST | 손목 |
| 13 | WIELD | 무기(주무기) |
| 14 | HOLD | 보조손 |

### Item Extra Flags (ef0 필드)

| 비트 | 이름 | 설명 |
|------|------|------|
| 0 | GLOW | 빛남 |
| 1 | HUM | 윙윙거림 |
| 2 | NORENT | 렌트 불가 |
| 3 | NODONATE | 기부 불가 |
| 4 | NOINVIS | 투명화 불가 |
| 5 | INVISIBLE | 투명 |
| 6 | MAGIC | 마법 아이템 |
| 7 | NODROP | 드롭 불가 (저주) |
| 8 | BLESS | 축복됨 |
| 9 | ANTI_GOOD | 선 사용 불가 |
| 10 | ANTI_EVIL | 악 사용 불가 |
| 11 | ANTI_NEUTRAL | 중립 사용 불가 |
| 12 | ANTI_MAGIC_USER | 마법사 사용 불가 |
| 13 | ANTI_CLERIC | 성직자 사용 불가 |
| 14 | ANTI_THIEF | 도적 사용 불가 |
| 15 | ANTI_WARRIOR | 전사 사용 불가 |
| 16 | NOSELL | 판매 불가 |
| 17 | QUEST | 퀘스트 아이템 |

### Apply Types (A 블록)

| 값 | 이름 | 설명 |
|----|------|------|
| 0 | NONE | 효과 없음 |
| 1 | STR | 힘 |
| 2 | DEX | 민첩 |
| 3 | INT | 지능 |
| 4 | WIS | 지혜 |
| 5 | CON | 체력 |
| 6 | CHA | 매력 |
| 12 | MANA | 최대 마나 |
| 13 | HIT | 최대 HP |
| 14 | MOVE | 최대 이동력 |
| 17 | AC | 방어도 |
| 18 | HITROLL | 명중 보너스 |
| 19 | DAMROLL | 피해 보너스 |
| 20-24 | SAVING_* | 내성 굴림 보너스 |

### 실제 예시

```
#1
wings~
a pair of wings~
A pair of wings is sitting here.~
~
9 0 0 0 0 ae 0 0 0 0 0 0 0
6 0 0 0
1 1 0 0 0
```

- type=9 (ARMOR), extra_flags=0, wear_flags=`ae`(비트0=TAKE + 비트4=HEAD)
- values=[6,0,0,0] → AC_apply=6
- weight=1, cost=1, rent=0

---

## 5. Mobile 파일 (.mob)

### 형식 (Enhanced 'E' 포맷)

```
#<vnum>
<keywords>~
<short_description>~
<long_description (in-room)>
~
<detailed_description>
~
<action_flags> <affect_flags> <alignment> [unused...] E
<level> <hitroll> <ac> <hp_dice> <damage_dice>
<gold> <experience>
<load_position> <default_position> <sex>
[BareHandAttack: <type>]
E
[T <trigger_vnum>]...
```

### 핵심 주의사항

- **마지막 E 마커**: flags 라인의 마지막 필드 `E`는 Enhanced 포맷임을 표시
- **E 종료 마커**: 데이터 끝에 별도의 `E` 라인이 있음
- **T 라인**: E 종료 마커 이후에 위치 (wld와 유사)
- **Dice 표기**: `NdS+B` (N개의 S면 주사위 + B 보너스)

### Flags 라인 (tbaMUD 128-bit)

```
<af0> <af1> <af2> <af3> <aff0> <aff1> <aff2> <aff3> <alignment> E
```

실제로는 간략화하여:
```
<action_flags> <affect_flags> <alignment> [padding...] E
```

### MOB Action Flags

| 비트 | 이름 | 설명 |
|------|------|------|
| 0 | SPEC | 특수 프로시저 있음 |
| 1 | SENTINEL | 이동하지 않음 |
| 2 | SCAVENGER | 바닥의 물건을 주움 |
| 3 | ISNPC | (R) NPC 자동 설정 |
| 4 | AWARE | 백스탭 면역 |
| 5 | AGGRESSIVE | 모든 PC 공격 |
| 6 | STAY_ZONE | 존 밖으로 나가지 않음 |
| 7 | WIMPY | 체력 낮으면 도주 |
| 8 | AGGR_EVIL | 악한 PC만 공격 |
| 9 | AGGR_GOOD | 선한 PC만 공격 |
| 10 | AGGR_NEUTRAL | 중립 PC만 공격 |
| 11 | MEMORY | 공격자를 기억 |
| 12 | HELPER | 다른 NPC를 도움 |
| 13 | NOCHARM | 매혹 면역 |
| 14 | NOSUMMON | 소환 면역 |
| 15 | NOSLEEP | 수면 면역 |
| 16 | NOBASH | 밀침 면역 |
| 17 | NOBLIND | 실명 면역 |
| 18 | NOKILL | 공격 불가 |

### Position 값

| 값 | 이름 | 설명 |
|----|------|------|
| 0 | DEAD | 죽음 |
| 1 | MORTALLY_WOUNDED | 치명상 |
| 2 | INCAPACITATED | 전투불능 |
| 3 | STUNNED | 기절 |
| 4 | SLEEPING | 수면 |
| 5 | RESTING | 휴식 |
| 6 | SITTING | 앉음 |
| 7 | FIGHTING | 전투 |
| 8 | STANDING | 서있음 |

### 맨손 공격 타입

| 값 | 이름 |
|----|------|
| 0 | hit |
| 1 | sting |
| 2 | whip |
| 3 | slash |
| 4 | bite |
| 5 | bludgeon |
| 6 | crush |
| 7 | pound |
| 8 | claw |
| 9 | maul |
| 10 | thrash |
| 11 | pierce |
| 12 | blast |
| 13 | punch |
| 14 | stab |

### 실제 예시

```
#1
Puff dragon fractal~
Puff~
Puff the Fractal Dragon is here, contemplating a higher reality.
~
   Is that some type of differential curve...
~
516106 0 0 0 2128 0 0 0 1000 E
34 9 -10 6d6+340 5d5+5
340 115600
8 8 2
BareHandAttack: 12
E
T 95
```

- action_flags=516106, alignment=1000, Enhanced 포맷
- 레벨 34, hitroll 9, AC -10, HP=6d6+340, 데미지=5d5+5
- gold=340, exp=115600
- 서있음/서있음/여성, 맨손=blast(12)
- 트리거 95 부착

---

## 6. Zone 파일 (.zon)

### 형식

```
#<zone_vnum>
<builder_names>~
<zone_name>~
<bot> <top> <lifespan> <reset_mode> <zone_flags> <unused> <unused> <unused> <min_level> <max_level>
{reset commands}
S
```

### Zone 파라미터

| 필드 | 설명 |
|------|------|
| bot | 존 시작 VNUM |
| top | 존 종료 VNUM |
| lifespan | 리셋 주기 (분) |
| reset_mode | 0=안함, 1=빈방일때, 2=항상 |
| zone_flags | 존 플래그 (asciiflag) |
| min_level | 최소 레벨 (-1=없음) |
| max_level | 최대 레벨 (-1=없음) |

### Zone Flags

| 비트 | 이름 | 설명 |
|------|------|------|
| 0 | CLOSED | 입장 불가 |
| 1 | NOIMMORT | 불멸자 입장 불가 |
| 2 | QUEST | 퀘스트 존 |
| 3 | GRID | areas 목록에 표시 |
| 4 | NOBUILD | 빌딩 불가 |
| 5 | NOASTRAL | 텔레포트 불가 |
| 6 | WORLDMAP | 월드맵 기본 사용 |

### Reset 커맨드

```
<cmd> <if_flag> <arg1> <arg2> <arg3> [<arg4>] [TAB comment]
```

| 커맨드 | 형식 | 설명 |
|--------|------|------|
| M | `M <if> <mob_vnum> <max_exist> <room_vnum>` | 몹 로드 |
| O | `O <if> <obj_vnum> <max_exist> <room_vnum>` | 오브젝트를 방에 배치 |
| G | `G <if> <obj_vnum> <max_exist> <unused>` | 마지막 M의 몹에게 지급 |
| E | `E <if> <obj_vnum> <max_exist> <equip_pos>` | 마지막 M의 몹에 장착 |
| P | `P <if> <obj_vnum> <max_exist> <container_vnum>` | 컨테이너에 넣기 |
| D | `D <if> <room_vnum> <exit_dir> <door_state>` | 문 상태 설정 |
| R | `R <if> <room_vnum> <obj_vnum> <unused>` | 방에서 오브젝트 제거 |
| T | `T <if> <trigger_type> <trigger_vnum> <room/mob/obj>` | 트리거 부착 |
| V | `V <if> <trigger_type> <context> <room> <name> <value>` | 변수 설정 |

if_flag: `0`=항상, `1`=이전 커맨드 성공시

### 실제 예시

```
#0
Rumble~
The Builder Academy Zone~
0 99 30 2 d 0 0 0 -1 -1
M 0 34 1 8 	(Chuck Norris)
O 0 1228 99 88 	(a advertising bulletin board)
M 0 1 1 1 	(Puff)
E 1 99 100 16 	(the Scythe of Death)
S
```

---

## 7. Trigger 파일 (.trg)

### 형식

```
#<vnum>
<trigger_name>~
<attach_type> <trigger_type_flags> <numeric_arg>
<arg_list>~
<script_body>
~
```

### Attach Types

| 값 | 타입 |
|----|------|
| 0 | MOB |
| 1 | OBJ |
| 2 | WLD (Room) |

### Trigger Type Flags (attach_type별로 다름)

**MOB Triggers** (attach_type=0):
| 비트 | 문자 | 이름 | 설명 |
|------|------|------|------|
| 0 | a | GLOBAL | 전역 |
| 1 | b | RANDOM | 랜덤 발동 |
| 2 | c | COMMAND | 커맨드 입력 |
| 3 | d | SPEECH | 대화 |
| 4 | e | ACT | 행동 |
| 5 | f | DEATH | 사망시 |
| 6 | g | GREET | 인사 (방향 포함) |
| 7 | h | GREET_ALL | 전체 인사 |
| 8 | i | ENTRY | 입장 |
| 9 | j | RECEIVE | 아이템 수령 |
| 10 | k | FIGHT | 전투중 |
| 11 | l | HITPRCNT | HP% 이하시 |
| 12 | m | BRIBE | 돈 수령 |
| 13 | n | LOAD | 로드시 |
| 14 | o | MEMORY | 기억된 PC 만남 |
| 15 | p | CAST | 주문 대상 |
| 16 | q | LEAVE | 떠남 |
| 17 | r | DOOR | 문 조작 |
| 18 | s | TIME | 특정 시간 |

### DG Script 언어 (기본 문법)

```
* 주석
if <condition>
  <commands>
elseif <condition>
  <commands>
else
  <commands>
end

wait <N> sec

%변수.속성%         # 변수 참조
%actor.name%       # 행위자 이름
%actor.is_pc%      # PC 여부
%self.vnum%        # 자신의 VNUM
%load% obj <vnum>  # 오브젝트 로드
%load% mob <vnum>  # 몹 로드
%purge% <target>   # 대상 제거
%send% <target> <msg>    # 개인 메시지
%echoaround% <target> <msg>  # 주변 메시지
nop %actor.gold(N)%  # 골드 지급
```

---

## 8. Shop 파일 (.shp)

### 핵심 주의사항

**Shop의 VNUM은 `#<vnum>~` 형태**로, 다른 타입과 달리 `~`가 포함됩니다.

### 형식

```
CircleMUD v3.0 Shop File~
#<vnum>~
<sell_item_vnum>
...
-1
<profit_buy>       (float, 예: 1.20)
<profit_sell>      (float, 예: 0.90)
<accept_type>      (아이템 타입 번호)
...
-1
<no_such_item1>~   (7개의 메시지 문자열)
<no_such_item2>~
<do_not_buy>~
<missing_cash1>~
<missing_cash2>~
<message_buy>~
<message_sell>~
<temper>           (0=normal)
<bitvector>        (0=normal)
<keeper_mob_vnum>
<with_who>         (0=all)
<shop_room_vnum>
...
-1
<open1>            (영업 시작1, 0-28)
<close1>           (영업 종료1)
<open2>            (영업 시작2)
<close2>           (영업 종료2)
```

---

## 9. Quest 파일 (.qst)

### 형식

```
#<vnum>
<quest_name>~
<keywords>~
<description>
~
<completion_message>
~
<quit_message>
~
<flags> <type> <target_vnum> <mob_vnum> <value0> <value1> <value2> <value3>
<reward_gold> <reward_exp> <reward_obj> <next_quest> <prev_quest> <min_level> <max_level>
S
```

### 실제 예시

```
#100
Kill the Mice!~
mice~
   I really need some help killing these mice...
~
   Well done!  You have completed your quest!
~
You have abandoned the quest.
~
3 179 0 194 -1 -1 -1
0 0 1 34 60 -1 3
10 0 65535
S
```

---

## 10. Bitvector 인코딩

### asciiflag_conv() 알고리즘

```python
def asciiflag_to_int(flag_str: str) -> int:
    if not flag_str or flag_str == "0":
        return 0
    try:
        return int(flag_str)  # 숫자면 그대로
    except ValueError:
        pass
    result = 0
    for ch in flag_str:
        if ch.islower():      # a-z → bit 0-25
            result |= 1 << (ord(ch) - ord('a'))
        elif ch.isupper():    # A-Z → bit 26-51
            result |= 1 << (26 + ord(ch) - ord('A'))
    return result
```

### 변환 예시

| 입력 | 비트 | 정수 | 의미 (Room flags 기준) |
|------|------|------|----------------------|
| `0` | 없음 | 0 | 플래그 없음 |
| `8` | - | 8 | 숫자 그대로 (TUNNEL) |
| `a` | 0 | 1 | DARK |
| `d` | 3 | 8 | INDOORS |
| `ae` | 0,4 | 17 | DARK + PEACEFUL |
| `abcj` | 0,1,2,9 | 519 | DARK+DEATH+NOMOB+PRIVATE |

---

## 11. Socials 파일

**위치**: `lib/misc/socials`

소셜(감정표현) 커맨드 정의. tbaMUD과 Simoon에서 형식이 동일합니다.

### 형식

```
<command> <min_victim_position> <flags>
<no_arg_to_char>
<no_arg_to_room>
<found_to_char>
<found_to_room>
<found_to_victim>
<not_found>
<self_to_char>
<self_to_room>

```

- 각 메시지 줄에서 `#`은 빈 메시지 (해당 상황에 메시지 없음)
- 8개 메시지 전에 `#`이 나오면 해당 소셜은 그 시점에서 종료 (short form)
- 소셜 사이에 빈 줄 구분
- `$` = 파일 종료

### 실제 예시

```
accuse 8 0
You look accusingly at $N.
$n looks accusingly at $N.
You accuse $N.
$n accuses $N.
$n accuses you.
Accuse who?
You accuse yourself.
$n accuses $n self.

ack 0 0
You gasp in exasperation!
$n gasps in exasperation!
#
```

`ack`는 `#`으로 종료되므로 "대상 없음" 메시지만 있는 short form입니다.

### 변수 치환

| 변수 | 의미 |
|------|------|
| `$n` | 행위자 이름 |
| `$N` | 대상 이름 |
| `$e/$E` | 행위자/대상의 he/she |
| `$m/$M` | 행위자/대상의 him/her |
| `$s/$S` | 행위자/대상의 his/her |

---

## 12. Help 파일 (.hlp)

**위치**: `lib/text/help/` (index 파일 참조)

### 파일 구조

`index` 파일이 로드할 `.hlp` 파일 목록을 나열합니다:

```
background.hlp
building.hlp
...
$
```

### 각 .hlp 파일 내 항목 형식

```
<keyword1> [keyword2] ...

<help text body>
...

#<level>
```

- 첫 줄: 공백 구분 키워드 (대소문자 무관)
- 빈 줄 이후: 도움말 본문 (여러 줄)
- `#<level>`: 종료 + 최소 열람 레벨 (예: `#0` = 모든 레벨, `#34` = 레벨 34+)

### 실제 예시

```
MAGIC MISSILE

Usage: cast 'magic missile' <victim>
Minimum Level: Mage 1

Causes a bolt of magical energy to be
hurled at the victim.

#0
```

### 핵심 주의사항

- tbaMUD는 `help.hlp` 1개에 721개 항목
- Simoon은 20+개의 `.hlp` 파일에 2,220개 항목 (EUC-KR)
- 파서는 `index` 파일을 읽어 로드할 파일 목록 결정

---

## 13. Commands — cmd_info[]

**위치**: `src/interpreter.c`

C 소스 코드의 `cmd_info[]` 배열에서 커맨드 목록을 추출합니다.

### tbaMUD 형식 (6필드)

```c
cpp_extern const struct command_info cmd_info[] = {
  { "RESERVED", "RESERVED", 0, 0, 0, 0 },  /* 0번 예약 */
  { "north"   , "n"       , POS_STANDING, do_move     , 0, SCMD_NORTH },
  { "look"    , "l"       , POS_RESTING , do_look     , 0, 0 },
  ...
};
```

| 필드 | 설명 | 예시 |
|------|------|------|
| name | 커맨드 이름 | `"look"` |
| min_match | 최소 약어 | `"l"` |
| position | 최소 포지션 (POS_*) | `POS_RESTING` |
| handler | C 핸들러 함수 | `do_look` |
| min_level | 최소 레벨 (LVL_*) | `0` |
| subcmd | 서브커맨드 (SCMD_*) | `0` |

### Simoon 형식 (5필드, min_match 없음)

```c
{ "north"  , POS_STANDING, do_move    , 0, SCMD_NORTH },
{ "look"   , POS_RESTING , do_look    , 0, 0 },
```

### 핵심 차이점

- tbaMUD: 6필드 (min_match 포함) → `has_min_match=True`
- Simoon: 5필드 (min_match 없음) → `has_min_match=False`
- POS_STANDING=8, POS_FIGHTING=7, POS_RESTING=5 등 상수는 파서 내부에서 숫자로 변환

### 데이터 규모

| MUD | 커맨드 수 |
|-----|-----------|
| tbaMUD | 275 |
| Simoon | 546 |

---

## 14. Skills — spello()

**위치**: `src/spell_parser.c`, `src/spells.h`, `src/class.c`

스킬/스펠 메타데이터는 3개 소스 파일에서 결합 추출합니다.

### (1) 스펠 ID 정의 — spells.h

```c
#define SPELL_MAGIC_MISSILE    32
#define SPELL_FIREBALL         26
#define SKILL_BACKSTAB         131
#define SKILL_BASH             132
```

- `SPELL_*`: 스펠 (마법 시전)
- `SKILL_*`: 스킬 (물리/비마법)

### (2) 스펠 메타데이터 — spell_parser.c: spello()

**tbaMUD (10 인자)**:

```c
spello(SPELL_MAGIC_MISSILE, "magic missile", 25, 10, 3,
       POS_FIGHTING, TAR_CHAR_ROOM | TAR_FIGHT_VICT,
       TRUE, MAG_DAMAGE, "You feel a cloak of blindness dissolve.");
```

| 인자 | 설명 |
|------|------|
| spell_id | SPELL_*/SKILL_* 상수 |
| name | 스펠 이름 문자열 |
| max_mana | 최대 마나 소모 |
| min_mana | 최소 마나 소모 |
| mana_change | 레벨당 마나 감소 |
| min_position | 최소 시전 포지션 |
| targets | 타겟 플래그 비트마스크 |
| violent | 적대 여부 |
| routines | 루틴 플래그 |
| wearoff_msg | 효과 해제 메시지 |

**Simoon (8 인자, name/wearoff 없음)**:

```c
spello(SPELL_MAGIC_MISSILE, 25, 10, 3,
       POS_FIGHTING, TAR_CHAR_ROOM | TAR_FIGHT_VICT,
       TRUE, MAG_DAMAGE);
```

Simoon에서 한글 스펠 이름은 별도의 `han_spells[]` 배열에 정의:

```c
const char *han_spells[] = {
    "!RESERVED!",          /* 0 */
    "방어",                /* 1 - SPELL_ARMOR */
    "텔레포트",            /* 2 - SPELL_TELEPORT */
    ...
};
```

### (3) 클래스별 레벨 — class.c: spell_level()

```c
spell_level(SPELL_MAGIC_MISSILE, CLASS_MAGIC_USER, 1);
spell_level(SPELL_MAGIC_MISSILE, CLASS_CLERIC, 10);
```

→ `skill.class_levels = {0: 1, 1: 10}` (0=Magic User, 1=Cleric)

### 핵심 차이 요약

| 항목 | tbaMUD | Simoon |
|------|--------|--------|
| spello() 인자 수 | 10 (이름+해제메시지 포함) | 8 (이름/해제메시지 없음) |
| 스펠 이름 소스 | spello() 인자 | han_spells[] 배열 |
| 스킬 수 | 54 | 79 |
| 클래스 수 | 4 | 7 |
