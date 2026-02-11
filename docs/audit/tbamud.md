# tbaMUD (CircleMUD) 데이터 전수조사

> 최종 업데이트: 2026-02-11 | 심층 분석 완료

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
