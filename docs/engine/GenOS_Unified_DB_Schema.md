# GenOS Unified DB Schema v1.0

> 7개 게임(tbaMUD, Simoon, 3eyes, 10woongi, muhan13, murim, 99hunter)의
> 런타임 데이터를 단일 PostgreSQL 스키마로 통합하는 범용 데이터베이스 설계.

---

## 1. 개요 및 설계 원칙

### 1.1 목적

GenOS 엔진은 7종의 이질적인 MUD 게임을 하나의 프레임워크 위에서 구동한다. 각 게임은 고유한 스탯 체계(5~18종), 장비 슬롯(16~40개), 플래그 비트필드, 직업/종족 구조를 가진다. 이 스키마는 **공통 구조를 정규 컬럼으로, 게임 고유 확장을 JSONB로** 수용하여 단일 DDL로 모든 게임을 지원한다.

### 1.2 설계 원칙

| # | 원칙 | 설명 |
|---|------|------|
| 1 | **Proto/Instance 분리** | 템플릿(불변, 빌더가 정의)과 런타임 상태(가변, 플레이어 데이터)를 명시적으로 구분한다. `mob_protos`/`item_protos`는 프로토타입, `players`는 인스턴스. |
| 2 | **정규 컬럼 + JSONB 하이브리드** | 7게임 공통 필드(vnum, name, level, hp 등)는 정규 컬럼으로 정의하여 타입 안전성과 인덱싱을 보장한다. 게임별 고유 데이터는 `ext JSONB`에 저장한다. |
| 3 | **비트필드 -> TEXT[] 태그 배열** | 숫자 비트필드 대신 사람이 읽을 수 있는 문자열 태그 배열(`TEXT[]`)을 사용하고, GIN 인덱스로 검색 성능을 확보한다. |
| 4 | **스탯은 JSONB** | 게임마다 스탯 종류가 5종(tbaMUD)에서 18종(murim)까지 다르므로, 고정 컬럼 대신 `stats JSONB`로 동적 수용한다. |
| 5 | **그래프 모델 exits** | 방 출구를 `rooms` 테이블의 JSONB 컬럼이 아닌 `room_exits` 별도 테이블로 분리하여 경로 탐색 쿼리와 참조 무결성을 지원한다. |
| 6 | **장비 슬롯 동적** | 착용 슬롯을 비트필드가 아닌 `TEXT[] wear_slots`로 정의하여 16슬롯(tbaMUD)부터 40슬롯(murim)까지 수용한다. |

---

## 2. 스키마 개요 (20+2 테이블)

### 2.1 테이블 분류

```
Proto (16, 불변 - 빌더/마이그레이션 데이터)
  rooms             방 프로토타입
  room_exits        방 출구 (그래프 간선)
  mob_protos        몬스터 프로토타입
  item_protos       아이템 프로토타입
  zones             존/에리어
  skills            스킬/스펠
  classes           직업
  races             종족
  shops             상점
  quests            퀘스트
  socials           소셜 명령어
  help_entries      도움말
  combat_messages   전투 메시지
  text_files        시스템 텍스트
  game_tables       수치 테이블 (EXP, THAC0, 세이브 등 통합)
  game_configs      게임 설정

Instance (3, 런타임 가변 데이터)
  players           플레이어 캐릭터
  organizations     클랜/길드/조직
  lua_scripts       Lua 스크립트 저장소

선택적 (2, 게시판 시스템)
  boards            게시판 정의
  board_posts       게시판 글
```

### 2.2 테이블 관계도

```
zones ──1:N──> rooms ──1:N──> room_exits
                 |
                 +── shops.room_vnum
                 +── players.room_vnum
                 +── organizations.room_vnum
                 +── boards.room_vnum

mob_protos ──── shops.keeper_vnum
item_protos ─── (values.key_vnum 등 JSONB 내부 참조)

classes ──── players.class_id, mob_protos.class_id
races   ──── players.race_id, mob_protos.race_id

skills  ──── combat_messages.skill_id

boards ──1:N──> board_posts
```

---

## 3. 테이블별 상세 DDL

### 3.1 rooms

방(Room) 프로토타입. 게임 월드의 기본 공간 단위.

```sql
CREATE TABLE rooms (
    vnum        INTEGER PRIMARY KEY,
    zone_vnum   INTEGER NOT NULL DEFAULT 0,
    name        TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    sector      INTEGER NOT NULL DEFAULT 0,
    flags       TEXT[] NOT NULL DEFAULT '{}',
    extra_descs JSONB NOT NULL DEFAULT '[]',
    scripts     JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_rooms_zone ON rooms (zone_vnum);
CREATE INDEX idx_rooms_flags ON rooms USING GIN (flags);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `vnum` | INTEGER PK | 가상 번호 (전 게임 고유) |
| `zone_vnum` | INTEGER | 소속 존 |
| `name` | TEXT | 방 제목 |
| `description` | TEXT | 방 설명 (여러 줄) |
| `sector` | INTEGER | 지형 타입 (0=실내, 1=도시, 2=들판 ...) |
| `flags` | TEXT[] | 방 플래그 (`{'DARK','NO_MOB','INDOORS'}`) |
| `extra_descs` | JSONB | 추가 설명 (`[{"keywords":"sign","desc":"..."}]`) |
| `scripts` | JSONB | 트리거/스크립트 참조 (`[{"vnum":100,"type":"load"}]`) |
| `ext` | JSONB | 게임 고유 확장 |

**ext 예시:**

```jsonc
// tbaMUD
{"map_x": 5, "map_y": 10}

// 3eyes
{"lolevel": 10, "hilevel": 50, "trap": true}

// 10woongi
{"random_monster": true, "monster_rate": 30, "fast_heal": true}

// murim
{"area_type": "무림", "pk_allowed": true}
```

---

### 3.2 room_exits

방 출구. 방향별 연결을 그래프 간선으로 모델링.

```sql
CREATE TABLE room_exits (
    from_vnum   INTEGER NOT NULL REFERENCES rooms(vnum),
    direction   SMALLINT NOT NULL,
    to_vnum     INTEGER NOT NULL DEFAULT -1,
    description TEXT NOT NULL DEFAULT '',
    keywords    TEXT NOT NULL DEFAULT '',
    key_vnum    INTEGER NOT NULL DEFAULT -1,
    flags       TEXT[] NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (from_vnum, direction)
);
CREATE INDEX idx_exits_to ON room_exits (to_vnum);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `from_vnum` | INTEGER FK | 출발 방 |
| `direction` | SMALLINT | 방향 (0=N, 1=E, 2=S, 3=W, 4=UP, 5=DOWN, 6~9=확장) |
| `to_vnum` | INTEGER | 도착 방 (-1 = 없음) |
| `description` | TEXT | 출구 설명 |
| `keywords` | TEXT | 문 키워드 |
| `key_vnum` | INTEGER | 열쇠 아이템 vnum (-1 = 없음) |
| `flags` | TEXT[] | 출구 플래그 (`{'DOOR','LOCKED','PICKPROOF'}`) |
| `ext` | JSONB | 확장 (예: `{"hidden": true}`) |

**direction 매핑:**

| 값 | 표준 | 한국어 |
|----|------|--------|
| 0 | NORTH | 북 |
| 1 | EAST | 동 |
| 2 | SOUTH | 남 |
| 3 | WEST | 서 |
| 4 | UP | 위 |
| 5 | DOWN | 아래 |
| 6~9 | 게임별 확장 | (포탈, somewhere 등) |

---

### 3.3 mob_protos

몬스터 프로토타입. 런타임에 `MobInstance`로 복제되어 월드에 배치.

```sql
CREATE TABLE mob_protos (
    vnum        INTEGER PRIMARY KEY,
    zone_vnum   INTEGER NOT NULL DEFAULT 0,
    keywords    TEXT NOT NULL DEFAULT '',
    short_desc  TEXT NOT NULL DEFAULT '',
    long_desc   TEXT NOT NULL DEFAULT '',
    detail_desc TEXT NOT NULL DEFAULT '',
    level       INTEGER NOT NULL DEFAULT 1,
    max_hp      INTEGER NOT NULL DEFAULT 1,
    max_mana    INTEGER NOT NULL DEFAULT 0,
    max_move    INTEGER NOT NULL DEFAULT 0,
    armor_class INTEGER NOT NULL DEFAULT 100,
    hitroll     INTEGER NOT NULL DEFAULT 0,
    damroll     INTEGER NOT NULL DEFAULT 0,
    damage_dice TEXT NOT NULL DEFAULT '1d4+0',
    gold        INTEGER NOT NULL DEFAULT 0,
    experience  BIGINT NOT NULL DEFAULT 0,
    alignment   INTEGER NOT NULL DEFAULT 0,
    sex         SMALLINT NOT NULL DEFAULT 0,
    position    SMALLINT NOT NULL DEFAULT 8,
    class_id    INTEGER NOT NULL DEFAULT 0,
    race_id     INTEGER NOT NULL DEFAULT 0,
    act_flags   TEXT[] NOT NULL DEFAULT '{}',
    aff_flags   TEXT[] NOT NULL DEFAULT '{}',
    stats       JSONB NOT NULL DEFAULT '{}',
    skills      JSONB NOT NULL DEFAULT '{}',
    scripts     JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_mobs_zone ON mob_protos (zone_vnum);
CREATE INDEX idx_mobs_level ON mob_protos (level);
CREATE INDEX idx_mobs_act ON mob_protos USING GIN (act_flags);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `vnum` | INTEGER PK | 몬스터 가상 번호 |
| `zone_vnum` | INTEGER | 소속 존 |
| `keywords` | TEXT | 검색 키워드 (`"guard city"`) |
| `short_desc` | TEXT | 짧은 설명 (전투/인벤토리) |
| `long_desc` | TEXT | 방 안에서 보이는 설명 |
| `detail_desc` | TEXT | `look <mob>` 상세 설명 |
| `level` | INTEGER | 레벨 |
| `max_hp` | INTEGER | 최대 HP (hp_dice 계산 결과 정수) |
| `max_mana` | INTEGER | 최대 마나 |
| `max_move` | INTEGER | 최대 이동력 |
| `armor_class` | INTEGER | 방어도 (낮을수록 좋음) |
| `hitroll` | INTEGER | 명중 보너스 |
| `damroll` | INTEGER | 데미지 보너스 |
| `damage_dice` | TEXT | 기본 데미지 (`"2d6+3"`) |
| `gold` | INTEGER | 소지 골드 |
| `experience` | BIGINT | 경험치 보상 |
| `alignment` | INTEGER | 성향 (-1000~1000) |
| `sex` | SMALLINT | 성별 (0=중성, 1=남, 2=여) |
| `position` | SMALLINT | 기본 자세 (8=서있음) |
| `class_id` | INTEGER | 직업 |
| `race_id` | INTEGER | 종족 |
| `act_flags` | TEXT[] | 행동 플래그 (`{'SENTINEL','AGGRESSIVE','SCAVENGER'}`) |
| `aff_flags` | TEXT[] | 효과 플래그 (`{'INVISIBLE','DETECT_INVIS','SANCTUARY'}`) |
| `stats` | JSONB | 능력치 (게임별 가변) |
| `skills` | JSONB | 보유 스킬 (`{"bash": 80, "kick": 60}`) |
| `scripts` | JSONB | 트리거 참조 |
| `ext` | JSONB | 게임 고유 확장 |

**stats 예시 (게임별):**

```jsonc
// tbaMUD (6종)
{"str": 18, "int": 13, "wis": 11, "dex": 16, "con": 15, "cha": 10}

// 10woongi (6종, 한글)
{"힘": 80, "내공": 60, "지혜": 50, "기골": 70, "민첩": 55, "투지": 45}

// murim (18종)
{"str": 18, "dex": 15, "con": 16, "int": 12, "wis": 14,
 "외공": 90, "내공": 85, "소울": 40, "경공": 70, "암기": 55,
 "검술": 80, "도술": 75, "창술": 60, "봉술": 50, "권술": 65,
 "각술": 45, "암술": 35, "기문": 30}
```

**ext 예시:**

```jsonc
// 3eyes
{"talk": "안녕하세요, 모험자여!", "ddesc": "키가 큰 경비병"}

// muhan13
{"bank": 5000, "title": "은행장"}

// 99hunter
{"mob_type": "complex", "thac0": 15, "dam_plus": 5}
```

---

### 3.4 item_protos

아이템 프로토타입. 런타임에 복제되어 인벤토리/방에 배치.

```sql
CREATE TABLE item_protos (
    vnum        INTEGER PRIMARY KEY,
    zone_vnum   INTEGER NOT NULL DEFAULT 0,
    keywords    TEXT NOT NULL DEFAULT '',
    short_desc  TEXT NOT NULL DEFAULT '',
    long_desc   TEXT NOT NULL DEFAULT '',
    item_type   TEXT NOT NULL DEFAULT 'other',
    weight      INTEGER NOT NULL DEFAULT 0,
    cost        INTEGER NOT NULL DEFAULT 0,
    min_level   INTEGER NOT NULL DEFAULT 0,
    wear_slots  TEXT[] NOT NULL DEFAULT '{}',
    flags       TEXT[] NOT NULL DEFAULT '{}',
    values      JSONB NOT NULL DEFAULT '{}',
    affects     JSONB NOT NULL DEFAULT '[]',
    extra_descs JSONB NOT NULL DEFAULT '[]',
    scripts     JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_items_zone ON item_protos (zone_vnum);
CREATE INDEX idx_items_type ON item_protos (item_type);
CREATE INDEX idx_items_flags ON item_protos USING GIN (flags);
CREATE INDEX idx_items_wear ON item_protos USING GIN (wear_slots);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `vnum` | INTEGER PK | 아이템 가상 번호 |
| `zone_vnum` | INTEGER | 소속 존 |
| `keywords` | TEXT | 검색 키워드 |
| `short_desc` | TEXT | 짧은 설명 |
| `long_desc` | TEXT | 바닥에 놓였을 때 설명 |
| `item_type` | TEXT | 아이템 타입 문자열 (`'weapon'`, `'armor'`, `'potion'` 등) |
| `weight` | INTEGER | 무게 |
| `cost` | INTEGER | 가격 |
| `min_level` | INTEGER | 최소 착용/사용 레벨 |
| `wear_slots` | TEXT[] | 착용 가능 슬롯 (`{'BODY','ABOUT'}`) |
| `flags` | TEXT[] | 아이템 플래그 (`{'GLOW','HUM','NO_DROP'}`) |
| `values` | JSONB | 타입별 수치 데이터 |
| `affects` | JSONB | 스탯 수정치 (`[{"location":"STR","modifier":2}]`) |
| `extra_descs` | JSONB | 추가 설명 |
| `scripts` | JSONB | 트리거 참조 |
| `ext` | JSONB | 게임 고유 확장 |

**values 예시 (item_type별):**

```jsonc
// weapon
{"damage": "2d6+3", "weapon_type": "slash", "speed": 1.0}

// armor
{"ac": 5, "slot": "body"}

// potion
{"spell1": "cure_light", "spell2": "bless", "level": 10}

// container
{"capacity": 100, "key_vnum": 1234, "locked": true}

// food
{"hours": 5, "poisoned": false}

// drink
{"capacity": 20, "current": 15, "liquid": "water", "poisoned": false}

// scroll
{"level": 12, "spell1": "fireball", "spell2": "none", "spell3": "none"}

// wand / staff
{"level": 10, "max_charges": 20, "charges": 20, "spell": "magic_missile"}
```

**wear_slots 값 목록:**

```
TAKE, FINGER_R, FINGER_L, NECK_1, NECK_2, BODY, HEAD, LEGS,
FEET, HANDS, ARMS, SHIELD, ABOUT, WAIST, WRIST_R, WRIST_L,
WIELD, HOLD, FLOAT, FACE, EAR_R, EAR_L, ANKLE_R, ANKLE_L, ...
```

> murim은 최대 40개 슬롯까지 확장. `TEXT[]`로 정의하여 제한 없이 수용.

---

### 3.5 zones

존/에리어. 방, 몬스터, 아이템의 그룹 단위이자 리셋 범위.

```sql
CREATE TABLE zones (
    vnum        INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    builders    TEXT NOT NULL DEFAULT '',
    lifespan    INTEGER NOT NULL DEFAULT 30,
    reset_mode  SMALLINT NOT NULL DEFAULT 2,
    level_range INT4RANGE,
    flags       TEXT[] NOT NULL DEFAULT '{}',
    resets      JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `vnum` | INTEGER PK | 존 번호 |
| `name` | TEXT | 존 이름 |
| `builders` | TEXT | 빌더 이름 |
| `lifespan` | INTEGER | 리셋 주기 (분) |
| `reset_mode` | SMALLINT | 리셋 모드 (0=안함, 1=비었을때, 2=항상) |
| `level_range` | INT4RANGE | 권장 레벨 범위 (`[10,20)`) |
| `flags` | TEXT[] | 존 플래그 |
| `resets` | JSONB | 리셋 명령 목록 |
| `ext` | JSONB | 게임 고유 확장 |

**resets 예시:**

```jsonc
[
  {"cmd": "M", "mob_vnum": 3010, "max": 1, "room_vnum": 3001},
  {"cmd": "O", "obj_vnum": 3020, "max": 1, "room_vnum": 3001},
  {"cmd": "E", "obj_vnum": 3021, "slot": "WIELD"},
  {"cmd": "D", "room_vnum": 3005, "direction": 0, "state": "closed"}
]
```

---

### 3.6 skills

스킬 및 스펠 정의.

```sql
CREATE TABLE skills (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    skill_type  TEXT NOT NULL DEFAULT 'spell',
    mana_cost   INTEGER NOT NULL DEFAULT 0,
    target      TEXT NOT NULL DEFAULT 'ignore',
    violent     BOOLEAN NOT NULL DEFAULT false,
    min_position SMALLINT NOT NULL DEFAULT 0,
    routines    TEXT[] NOT NULL DEFAULT '{}',
    wearoff_msg TEXT NOT NULL DEFAULT '',
    class_levels JSONB NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}'
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | INTEGER PK | 스킬 ID |
| `name` | TEXT | 스킬 이름 |
| `skill_type` | TEXT | `'spell'`, `'skill'`, `'art'`(무공) |
| `mana_cost` | INTEGER | 마나 소모 |
| `target` | TEXT | 대상 (`'char_room'`, `'self_only'`, `'ignore'` 등) |
| `violent` | BOOLEAN | 적대적 여부 |
| `min_position` | SMALLINT | 최소 자세 |
| `routines` | TEXT[] | 실행 루틴 (`{'MAG_DAMAGE','MAG_AFFECTS'}`) |
| `wearoff_msg` | TEXT | 효과 종료 메시지 |
| `class_levels` | JSONB | 직업별 습득 레벨 (`{"warrior":5,"mage":1}`) |
| `ext` | JSONB | 게임 고유 확장 |

**ext 예시:**

```jsonc
// tbaMUD
{"korean_name": "치료의 빛"}

// 10woongi
{"korean_name": "기합", "category": "무술", "element": "양"}

// murim
{"category": "내공심법", "realm": "화산파", "tier": 3}
```

---

### 3.7 classes

직업 정의. 7~30개 직업을 게임별로 수용.

```sql
CREATE TABLE classes (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    abbrev      TEXT NOT NULL DEFAULT '',
    hp_gain     INT4RANGE NOT NULL DEFAULT '[1,10)',
    mana_gain   INT4RANGE NOT NULL DEFAULT '[0,0)',
    move_gain   INT4RANGE NOT NULL DEFAULT '[0,0)',
    base_stats  JSONB NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}'
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | INTEGER PK | 직업 ID |
| `name` | TEXT | 직업 이름 |
| `abbrev` | TEXT | 약자 (2~4자) |
| `hp_gain` | INT4RANGE | 레벨업 HP 획득 범위 (`[10,20)` = 10~19) |
| `mana_gain` | INT4RANGE | 레벨업 마나 획득 범위 |
| `move_gain` | INT4RANGE | 레벨업 이동력 획득 범위 |
| `base_stats` | JSONB | 기본 능력치 |
| `ext` | JSONB | 게임 고유 확장 |

**ext 예시:**

```jsonc
// 99hunter (진급 경로)
{"tier": 2, "base_class": "warrior", "promotion_level": 50}

// murim (계파)
{"realm": "화산파", "advancement_path": ["화산제자","화산검객","화산장로"]}
```

---

### 3.8 races

종족 정의.

```sql
CREATE TABLE races (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    abbrev      TEXT NOT NULL DEFAULT '',
    stat_mods   JSONB NOT NULL DEFAULT '{}',
    body_parts  TEXT[] NOT NULL DEFAULT '{}',
    size        TEXT NOT NULL DEFAULT 'medium',
    ext         JSONB NOT NULL DEFAULT '{}'
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | INTEGER PK | 종족 ID |
| `name` | TEXT | 종족 이름 |
| `abbrev` | TEXT | 약자 |
| `stat_mods` | JSONB | 능력치 수정 (`{"str":2,"dex":-1}`) |
| `body_parts` | TEXT[] | 신체 부위 (`{'HEAD','ARMS','LEGS','TAIL'}`) |
| `size` | TEXT | 크기 (`'tiny'`, `'small'`, `'medium'`, `'large'`, `'huge'`) |
| `ext` | JSONB | 게임 고유 확장 |

---

### 3.9 shops

상점 정의.

```sql
CREATE TABLE shops (
    vnum          INTEGER PRIMARY KEY,
    keeper_vnum   INTEGER NOT NULL,
    room_vnum     INTEGER NOT NULL DEFAULT 0,
    buy_types     TEXT[] NOT NULL DEFAULT '{}',
    buy_profit    REAL NOT NULL DEFAULT 1.1,
    sell_profit   REAL NOT NULL DEFAULT 0.9,
    hours         JSONB NOT NULL DEFAULT '{}',
    inventory     JSONB NOT NULL DEFAULT '[]',
    messages      JSONB NOT NULL DEFAULT '{}',
    ext           JSONB NOT NULL DEFAULT '{}'
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `vnum` | INTEGER PK | 상점 번호 |
| `keeper_vnum` | INTEGER | 상점 NPC vnum |
| `room_vnum` | INTEGER | 상점 위치 방 |
| `buy_types` | TEXT[] | 매입 가능 아이템 타입 (`{'weapon','armor'}`) |
| `buy_profit` | REAL | 매입 배율 (1.1 = 110%) |
| `sell_profit` | REAL | 판매 배율 (0.9 = 90%) |
| `hours` | JSONB | 영업 시간 (`{"open":6,"close":20}`) |
| `inventory` | JSONB | 고정 재고 (`[{"vnum":3020,"quantity":-1}]`, -1=무한) |
| `messages` | JSONB | 대사 (`{"no_item":"그건 안 팝니다.","missing_cash":"돈이 부족합니다."}`) |
| `ext` | JSONB | 게임 고유 확장 |

---

### 3.10 quests

퀘스트 정의.

```sql
CREATE TABLE quests (
    vnum        INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    quest_type  TEXT NOT NULL DEFAULT 'kill',
    level_range INT4RANGE,
    giver_vnum  INTEGER NOT NULL DEFAULT 0,
    target      JSONB NOT NULL DEFAULT '{}',
    rewards     JSONB NOT NULL DEFAULT '{}',
    chain       JSONB NOT NULL DEFAULT '{}',
    flags       TEXT[] NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}'
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `vnum` | INTEGER PK | 퀘스트 번호 |
| `name` | TEXT | 퀘스트 이름 |
| `description` | TEXT | 설명 |
| `quest_type` | TEXT | 유형 (`'kill'`, `'gather'`, `'escort'`, `'deliver'`) |
| `level_range` | INT4RANGE | 권장 레벨 |
| `giver_vnum` | INTEGER | 퀘스트 NPC |
| `target` | JSONB | 목표 (`{"mob_vnum":1234,"count":5}`) |
| `rewards` | JSONB | 보상 (`{"exp":5000,"gold":100,"item_vnum":2000}`) |
| `chain` | JSONB | 연계 퀘스트 (`{"prev":10,"next":12}`) |
| `flags` | TEXT[] | 퀘스트 플래그 (`{'REPEATABLE','DAILY'}`) |
| `ext` | JSONB | 게임 고유 확장 |

---

### 3.11 socials

소셜 명령어 (에모트).

```sql
CREATE TABLE socials (
    command     TEXT PRIMARY KEY,
    min_victim_position SMALLINT NOT NULL DEFAULT 0,
    messages    JSONB NOT NULL DEFAULT '{}'
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `command` | TEXT PK | 명령어 이름 (`"smile"`, `"nod"`) |
| `min_victim_position` | SMALLINT | 대상 최소 자세 |
| `messages` | JSONB | 메시지 셋 |

**messages 예시:**

```jsonc
{
  "char_no_arg":   "You smile happily.",
  "others_no_arg": "$n smiles happily.",
  "char_found":    "You smile at $N.",
  "others_found":  "$n smiles at $N.",
  "victim_found":  "$n smiles at you.",
  "not_found":     "Smile at who?",
  "char_auto":     "You smile to yourself.",
  "others_auto":   "$n smiles at $mself."
}
```

> 기존 9개 고정 TEXT 컬럼을 JSONB 1개로 통합. 게임별 메시지 키가 달라도 유연하게 수용.

---

### 3.12 help_entries

도움말 항목.

```sql
CREATE TABLE help_entries (
    id          SERIAL PRIMARY KEY,
    keywords    TEXT[] NOT NULL DEFAULT '{}',
    category    TEXT NOT NULL DEFAULT 'general',
    min_level   INTEGER NOT NULL DEFAULT 0,
    body        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_help_keywords ON help_entries USING GIN (keywords);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | SERIAL PK | 자동 증가 ID |
| `keywords` | TEXT[] | 검색 키워드 (`{'help','도움말','?'}`) |
| `category` | TEXT | 분류 (`'general'`, `'immortal'`, `'builder'`) |
| `min_level` | INTEGER | 열람 최소 레벨 |
| `body` | TEXT | 도움말 본문 |

---

### 3.13 combat_messages

전투 메시지. 스킬/무기별 공격 성공/실패 시 출력 메시지.

```sql
CREATE TABLE combat_messages (
    id          SERIAL PRIMARY KEY,
    skill_id    INTEGER NOT NULL,
    hit_type    TEXT NOT NULL,
    to_char     TEXT NOT NULL DEFAULT '',
    to_victim   TEXT NOT NULL DEFAULT '',
    to_room     TEXT NOT NULL DEFAULT '',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_cmsg_skill ON combat_messages (skill_id);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | SERIAL PK | 자동 증가 ID |
| `skill_id` | INTEGER | 스킬 참조 |
| `hit_type` | TEXT | 판정 유형 (`'hit'`, `'miss'`, `'god'`, `'death'`) |
| `to_char` | TEXT | 공격자에게 보이는 메시지 |
| `to_victim` | TEXT | 피해자에게 보이는 메시지 |
| `to_room` | TEXT | 방 안 다른 사람에게 보이는 메시지 |
| `ext` | JSONB | 확장 (예: 한국어 메시지 등) |

---

### 3.14 text_files

시스템 텍스트 파일 (MOTD, 뉴스, 크레딧 등).

```sql
CREATE TABLE text_files (
    name        TEXT PRIMARY KEY,
    category    TEXT NOT NULL DEFAULT 'system',
    content     TEXT NOT NULL DEFAULT ''
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `name` | TEXT PK | 파일 이름 (`'motd'`, `'news'`, `'credits'`) |
| `category` | TEXT | 분류 (`'system'`, `'login'`, `'info'`) |
| `content` | TEXT | 텍스트 내용 |

---

### 3.15 game_tables

범용 수치 테이블. 기존 6개 별도 테이블(experience_table, thac0_table, saving_throws, level_titles, attribute_modifiers, practice_params)을 하나로 통합.

```sql
CREATE TABLE game_tables (
    table_name  TEXT NOT NULL,
    key         JSONB NOT NULL,
    value       JSONB NOT NULL,
    PRIMARY KEY (table_name, key)
);
CREATE INDEX idx_gtables_name ON game_tables (table_name);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `table_name` | TEXT | 테이블 구분 (`'exp'`, `'thac0'`, `'saving_throw'`, `'title'`, `'attr_mod'`, `'practice'`) |
| `key` | JSONB | 복합 키 |
| `value` | JSONB | 값 |

**사용 예시:**

```jsonc
// 경험치 테이블
table_name: "exp"
key:   {"level": 10}
value: {"exp": 50000}

// THAC0 테이블
table_name: "thac0"
key:   {"class": "warrior", "level": 5}
value: {"thac0": 17}

// 세이빙 스로우
table_name: "saving_throw"
key:   {"class": "mage", "save_type": "spell", "level": 10}
value: {"save": 65}

// 레벨 타이틀
table_name: "title"
key:   {"class": "warrior", "level": 15, "sex": 1}
value: {"title": "the Warrior"}

// 능력치 수정
table_name: "attr_mod"
key:   {"stat": "str", "value": 18}
value: {"tohit": 1, "todam": 2, "carry": 220}

// 수련 파라미터
table_name: "practice"
key:   {"class": "mage"}
value: {"sessions_per_level": 3, "learn_rate": 25}
```

---

### 3.16 game_configs

게임 설정. 키-값 쌍으로 게임 동작 파라미터 저장.

```sql
CREATE TABLE game_configs (
    key         TEXT PRIMARY KEY,
    value       JSONB NOT NULL,
    category    TEXT NOT NULL DEFAULT 'general',
    description TEXT NOT NULL DEFAULT ''
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `key` | TEXT PK | 설정 키 (`'start_room'`, `'max_level'`, `'pk_allowed'`) |
| `value` | JSONB | 설정 값 (JSONB로 타입 자유) |
| `category` | TEXT | 분류 (`'general'`, `'movement'`, `'combat'`, `'economy'`) |
| `description` | TEXT | 설명 |

**사용 예시:**

```jsonc
key: "start_room",  value: 3001,     category: "general"
key: "max_level",   value: 34,       category: "general"
key: "pk_allowed",  value: false,    category: "combat"
key: "year_time",   value: 35,       category: "general"   // 10woongi
key: "max_users",   value: 100,      category: "system"    // 10woongi
```

---

### 3.17 players

플레이어 캐릭터 (Instance). 런타임 상태를 저장하며 주기적으로 DB에 flush.

```sql
CREATE TABLE players (
    id            SERIAL PRIMARY KEY,
    name          TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL DEFAULT '',
    class_id      INTEGER NOT NULL DEFAULT 0,
    race_id       INTEGER NOT NULL DEFAULT 0,
    sex           SMALLINT NOT NULL DEFAULT 0,
    level         INTEGER NOT NULL DEFAULT 1,
    experience    BIGINT NOT NULL DEFAULT 0,
    hp            INTEGER NOT NULL DEFAULT 100,
    max_hp        INTEGER NOT NULL DEFAULT 100,
    mana          INTEGER NOT NULL DEFAULT 100,
    max_mana      INTEGER NOT NULL DEFAULT 100,
    move          INTEGER NOT NULL DEFAULT 100,
    max_move      INTEGER NOT NULL DEFAULT 100,
    gold          INTEGER NOT NULL DEFAULT 0,
    bank_gold     INTEGER NOT NULL DEFAULT 0,
    armor_class   INTEGER NOT NULL DEFAULT 100,
    alignment     INTEGER NOT NULL DEFAULT 0,
    stats         JSONB NOT NULL DEFAULT '{}',
    equipment     JSONB NOT NULL DEFAULT '{}',
    inventory     JSONB NOT NULL DEFAULT '[]',
    affects       JSONB NOT NULL DEFAULT '[]',
    skills        JSONB NOT NULL DEFAULT '{}',
    flags         TEXT[] NOT NULL DEFAULT '{}',
    aliases       JSONB NOT NULL DEFAULT '{}',
    title         TEXT NOT NULL DEFAULT '',
    description   TEXT NOT NULL DEFAULT '',
    room_vnum     INTEGER NOT NULL DEFAULT 0,
    org_id        INTEGER NOT NULL DEFAULT 0,
    org_rank      INTEGER NOT NULL DEFAULT 0,
    ext           JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login    TIMESTAMPTZ
);
CREATE INDEX idx_players_name ON players (name);
CREATE INDEX idx_players_level ON players (level);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | SERIAL PK | 자동 증가 ID |
| `name` | TEXT UNIQUE | 캐릭터 이름 |
| `password_hash` | TEXT | bcrypt/argon2 해시 |
| `class_id` | INTEGER | 직업 |
| `race_id` | INTEGER | 종족 |
| `sex` | SMALLINT | 성별 |
| `level` | INTEGER | 현재 레벨 |
| `experience` | BIGINT | 누적 경험치 |
| `hp/max_hp` | INTEGER | 현재/최대 HP |
| `mana/max_mana` | INTEGER | 현재/최대 마나 |
| `move/max_move` | INTEGER | 현재/최대 이동력 |
| `gold` | INTEGER | 소지 골드 |
| `bank_gold` | INTEGER | 은행 골드 |
| `armor_class` | INTEGER | 방어도 |
| `alignment` | INTEGER | 성향 |
| `stats` | JSONB | 능력치 |
| `equipment` | JSONB | 장착 장비 (`{"WIELD":{"vnum":3020,"condition":95}}`) |
| `inventory` | JSONB | 인벤토리 (`[{"vnum":3021,"count":5}]`) |
| `affects` | JSONB | 활성 효과 (`[{"skill":"bless","duration":24,"mods":{"hitroll":2}}]`) |
| `skills` | JSONB | 습득 스킬 (`{"bash":85,"kick":70}`) |
| `flags` | TEXT[] | 플레이어 플래그 (`{'BRIEF','COMPACT','AUTOEXIT'}`) |
| `aliases` | JSONB | 명령어 별칭 (`{"k":"kill","q":"quaff recall"}`) |
| `title` | TEXT | 타이틀 |
| `description` | TEXT | 외형 설명 |
| `room_vnum` | INTEGER | 현재/마지막 위치 |
| `org_id` | INTEGER | 소속 조직 ID |
| `org_rank` | INTEGER | 조직 내 직급 |
| `ext` | JSONB | 게임 고유 확장 |
| `created_at` | TIMESTAMPTZ | 생성 시각 |
| `last_login` | TIMESTAMPTZ | 마지막 접속 |

**ext 예시:**

```jsonc
// muhan13
{"marriage_partner": "철수", "forge_level": 5}

// murim
{"art": [{"name":"태극혜검","level":80,"exp":12000}],
 "proficiency": {"검술":90,"내공심법":75},
 "realm": "화산파", "rebirth_count": 2}

// 99hunter
{"deity": "제우스", "council": "원로회의", "favor": 500}
```

---

### 3.18 organizations

클랜, 길드, 의회 등 플레이어 조직.

```sql
CREATE TABLE organizations (
    id          SERIAL PRIMARY KEY,
    org_type    TEXT NOT NULL DEFAULT 'clan',
    name        TEXT NOT NULL DEFAULT '',
    leader      TEXT NOT NULL DEFAULT '',
    treasury    INTEGER NOT NULL DEFAULT 0,
    room_vnum   INTEGER NOT NULL DEFAULT 0,
    ext         JSONB NOT NULL DEFAULT '{}'
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | SERIAL PK | 조직 ID |
| `org_type` | TEXT | 유형 (`'clan'`, `'guild'`, `'council'`, `'order'`) |
| `name` | TEXT | 조직 이름 |
| `leader` | TEXT | 리더 캐릭터 이름 |
| `treasury` | INTEGER | 조직 금고 |
| `room_vnum` | INTEGER | 본거지 방 |
| `ext` | JSONB | 게임 고유 확장 |

---

### 3.19 lua_scripts

Lua 스크립트 저장소. 게임별/카테고리별 스크립트 버전 관리.

```sql
CREATE TABLE lua_scripts (
    id          SERIAL PRIMARY KEY,
    game        TEXT NOT NULL DEFAULT '',
    category    TEXT NOT NULL DEFAULT '',
    name        TEXT NOT NULL DEFAULT '',
    source      TEXT NOT NULL DEFAULT '',
    version     INTEGER NOT NULL DEFAULT 1,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (game, category, name)
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | SERIAL PK | 자동 증가 ID |
| `game` | TEXT | 게임 식별자 (`'tbamud'`, `'10woongi'`, `'murim'`) |
| `category` | TEXT | 카테고리 (`'commands'`, `'combat'`, `'triggers'`, `'korean_nlp'`) |
| `name` | TEXT | 스크립트 이름 (`'movement.lua'`, `'combat_round.lua'`) |
| `source` | TEXT | Lua 소스 코드 |
| `version` | INTEGER | 버전 (핫 리로드시 증가) |
| `updated_at` | TIMESTAMPTZ | 최종 수정 시각 |

---

### 3.20~3.21 boards + board_posts (선택적)

게시판 시스템. muhan13(18개 게시판), 99hunter 등 게시판이 있는 게임에서 사용.

```sql
CREATE TABLE boards (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    board_type  TEXT NOT NULL DEFAULT 'general',
    room_vnum   INTEGER NOT NULL DEFAULT 0,
    min_read    INTEGER NOT NULL DEFAULT 0,
    min_write   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE board_posts (
    id          SERIAL PRIMARY KEY,
    board_id    INTEGER NOT NULL REFERENCES boards(id),
    author      TEXT NOT NULL DEFAULT '',
    subject     TEXT NOT NULL DEFAULT '',
    body        TEXT NOT NULL DEFAULT '',
    posted_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_bposts_board ON board_posts (board_id);
```

| boards 컬럼 | 타입 | 설명 |
|-------------|------|------|
| `id` | SERIAL PK | 게시판 ID |
| `name` | TEXT | 게시판 이름 |
| `board_type` | TEXT | 유형 (`'general'`, `'trade'`, `'clan'`, `'immortal'`) |
| `room_vnum` | INTEGER | 게시판 위치 방 |
| `min_read` | INTEGER | 읽기 최소 레벨 |
| `min_write` | INTEGER | 쓰기 최소 레벨 |

| board_posts 컬럼 | 타입 | 설명 |
|-----------------|------|------|
| `id` | SERIAL PK | 글 ID |
| `board_id` | INTEGER FK | 게시판 참조 |
| `author` | TEXT | 작성자 |
| `subject` | TEXT | 제목 |
| `body` | TEXT | 본문 |
| `posted_at` | TIMESTAMPTZ | 작성 시각 |

---

## 4. 기존 21테이블 대비 변경점 비교표

마이그레이션 도구의 기존 `GenosCompiler`가 생성하던 21테이블 DDL과 신규 20+2테이블의 주요 차이점.

| 관점 | 기존 (21T) | 신규 (20+2T) | 변경 이유 |
|------|-----------|-------------|----------|
| **exits** | `rooms.exits` JSONB 컬럼 | `room_exits` 별도 테이블 | 그래프 쿼리 최적화, FK 참조 무결성 |
| **flags** | JSONB 숫자 배열 (`[1,4,8]`) | `TEXT[]` 태그 + GIN 인덱스 (`{'DARK','NO_MOB'}`) | 가독성, 게임 간 번호 충돌 방지 |
| **스탯** | 고정 컬럼 (`str`, `int`, ...) | `stats JSONB` | 5~18종 동적 수용 |
| **장비 슬롯** | `wear_flags` 비트필드 | `TEXT[] wear_slots` | 16~40 슬롯 동적 수용 |
| **hp_dice** | `TEXT "10d8+100"` (dice) | `max_hp INTEGER` (확정값) | 런타임 dice 파싱 불필요, 엔진 단순화 |
| **item_type** | `INTEGER` 코드 (0~22) | `TEXT` 이름 (`'weapon'`, `'armor'`) | 게임 간 코드 충돌 방지, 가독성 |
| **수치 테이블** | 6개 별도 테이블 | `game_tables` 1개 통합 | DDL 단순화, 게임별 커스텀 테이블 유연 추가 |
| **소셜 메시지** | 9개 TEXT 컬럼 | `messages JSONB` | 게임별 메시지 키 차이 유연 수용 |
| **game_configs** | `value TEXT` + `value_type TEXT` | `value JSONB` | 타입 변환 불필요, 복합 값 지원 |
| **Proto/Instance** | `rooms`, `items` (혼용) | `mob_protos`, `item_protos` (명시 구분) | 테이블명에서 역할 명확화 |
| **organizations** | 없음 | `organizations` 신설 | 클랜/길드/의회 지원 |
| **boards** | 없음 | `boards` + `board_posts` 선택적 추가 | muhan13 18개 게시판 등 지원 |
| **lua_scripts** | 파일 기반 | DB 저장 + 버전 관리 | 핫 리로드, 멀티 게임 관리 용이 |
| **quests** | 없음 | `quests` 신설 | Simoon 16퀘, 10woongi 퀘스트 지원 |
| **level_range** | 없음 | `INT4RANGE` 타입 활용 | PostgreSQL 범위 타입으로 쿼리 최적화 |

### 테이블 매핑 상세

```
기존 21테이블                    신규 20+2테이블
─────────────────────────        ─────────────────────────
rooms                       →   rooms + room_exits (분리)
items                       →   item_protos (이름 변경)
mobs                        →   mob_protos (이름 변경)
zones                       →   zones (유지)
shops                       →   shops (유지)
skills                      →   skills (유지)
classes                     →   classes (유지)
races                       →   races (유지)
socials                     →   socials (메시지 JSONB화)
help_entries                →   help_entries (유지)
combat_messages             →   combat_messages (유지)
text_files                  →   text_files (유지)
game_configs                →   game_configs (value JSONB화)
experience_table            ─┐
thac0_table                  │
saving_throws                ├→ game_tables (통합)
level_titles                 │
attribute_modifiers          │
practice_params             ─┘
(없음)                      →   players (신설)
(없음)                      →   organizations (신설)
(없음)                      →   lua_scripts (신설)
(없음)                      →   quests (신설)
(없음)                      →   boards + board_posts (선택적)
```

---

## 5. 마이그레이션 도구 변환 흐름

### 5.1 전체 파이프라인

```
소스 게임 데이터
    │
    ▼
[Adapter] ── 파서별 파싱 ──> UIR (30 dataclasses)
    │
    ▼
[GenosCompiler] ── UIR → SQL 변환 ──> DDL + INSERT 문
    │
    ├── rooms.sql          (rooms + room_exits)
    ├── mob_protos.sql     (mob_protos)
    ├── item_protos.sql    (item_protos)
    ├── zones.sql          (zones)
    ├── shops.sql          (shops)
    ├── skills.sql         (skills)
    ├── classes.sql        (classes)
    ├── races.sql          (races)
    ├── socials.sql        (socials)
    ├── help.sql           (help_entries)
    ├── combat_msg.sql     (combat_messages)
    ├── text_files.sql     (text_files)
    ├── game_tables.sql    (game_tables)
    ├── game_configs.sql   (game_configs)
    ├── quests.sql         (quests)
    │
    ├── commands.lua       (명령어 스크립트)
    ├── combat.lua         (전투 스크립트)
    ├── triggers.lua       (트리거 스크립트)
    ├── korean_nlp.lua     (한국어 NLP)
    ├── korean_commands.lua(한국어 명령어)
    ├── config.lua         (설정)
    ├── exp_tables.lua     (경험치/수치)
    └── stat_tables.lua    (스탯 테이블)
```

### 5.2 UIR -> SQL 변환 규칙

| UIR 필드 | SQL 변환 |
|----------|----------|
| `Room.exits` (dict) | `room_exits` 행으로 분리 |
| `Room.flags` (int bitvector) | `TEXT[]` 태그명 배열로 변환 |
| `Mob.hp_dice` ("10d8+100") | `max_hp` = dice 기댓값 계산 (10*4.5+100=145) |
| `Item.item_type` (int) | `TEXT` 이름으로 매핑 (5 -> `'weapon'`) |
| `Item.wear_flags` (int bitvector) | `TEXT[]` 슬롯명 배열로 변환 |
| `Mob.stats` (dict) | `stats JSONB` 그대로 |
| `Social.messages` (9 fields) | `messages JSONB` 단일 객체 |
| `ExperienceEntry` | `game_tables` (table_name='exp') |
| `ThacOEntry` | `game_tables` (table_name='thac0') |
| `SavingThrowEntry` | `game_tables` (table_name='saving_throw') |
| `LevelTitle` | `game_tables` (table_name='title') |
| `AttributeModifier` | `game_tables` (table_name='attr_mod') |
| `PracticeParams` | `game_tables` (table_name='practice') |
| `GameConfig` | `game_configs` (value -> JSONB 자동 변환) |
| `*.extensions` (dict) | 각 테이블 `ext JSONB`로 병합 |

### 5.3 비트필드 -> 태그 변환 예시

```python
# 기존: 숫자 비트필드
room_flags = 0x0C  # DARK | NO_MOB (bits 2,3)

# 변환 후: 문자열 태그 배열
flags = ['DARK', 'NO_MOB']

# SQL
INSERT INTO rooms (vnum, flags) VALUES (3001, ARRAY['DARK','NO_MOB']);

# 쿼리: 특정 플래그가 있는 방 찾기
SELECT * FROM rooms WHERE flags @> ARRAY['DARK'];
```

### 5.4 hp_dice -> max_hp 변환 예시

```python
# 기존 UIR
hp_dice = "10d8+100"  # 10개의 8면체 주사위 + 100

# 변환 공식: NdS+B -> N*(S+1)/2 + B (기댓값)
max_hp = 10 * (8 + 1) / 2 + 100  # = 145

# 또는 최대값: N*S + B
max_hp = 10 * 8 + 100  # = 180

# 엔진은 정수 max_hp만 사용, dice 파싱 불필요
```

### 5.5 DB 초기화 흐름 (엔진 부팅 시)

```
Docker Compose 시작
    │
    ▼
PostgreSQL 기동
    │
    ▼
scripts/init-db.sh
    ├── CREATE DATABASE tbamud;
    ├── CREATE DATABASE 10woongi;
    ├── ...
    │
    ▼
게임 컨테이너 기동 (GAME=tbamud)
    │
    ▼
engine.py 부팅
    ├── asyncpg 연결
    ├── DDL 실행 (CREATE TABLE IF NOT EXISTS ...)
    ├── seed 데이터 INSERT (ON CONFLICT DO NOTHING)
    ├── 전체 DB → 인메모리 로드
    └── 5분 주기 flush 타이머 시작
```

---

## 부록: 전체 DDL (복사용)

아래는 모든 테이블의 CREATE 문을 순서대로 나열한 것으로, `init-db.sh`나 마이그레이션 스크립트에서 직접 사용할 수 있다.

```sql
-- =============================================================
-- GenOS Unified DB Schema v1.0
-- 20 + 2 (선택적) 테이블
-- =============================================================

-- Proto: 방
CREATE TABLE rooms (
    vnum        INTEGER PRIMARY KEY,
    zone_vnum   INTEGER NOT NULL DEFAULT 0,
    name        TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    sector      INTEGER NOT NULL DEFAULT 0,
    flags       TEXT[] NOT NULL DEFAULT '{}',
    extra_descs JSONB NOT NULL DEFAULT '[]',
    scripts     JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_rooms_zone ON rooms (zone_vnum);
CREATE INDEX idx_rooms_flags ON rooms USING GIN (flags);

-- Proto: 방 출구
CREATE TABLE room_exits (
    from_vnum   INTEGER NOT NULL REFERENCES rooms(vnum),
    direction   SMALLINT NOT NULL,
    to_vnum     INTEGER NOT NULL DEFAULT -1,
    description TEXT NOT NULL DEFAULT '',
    keywords    TEXT NOT NULL DEFAULT '',
    key_vnum    INTEGER NOT NULL DEFAULT -1,
    flags       TEXT[] NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (from_vnum, direction)
);
CREATE INDEX idx_exits_to ON room_exits (to_vnum);

-- Proto: 몬스터
CREATE TABLE mob_protos (
    vnum        INTEGER PRIMARY KEY,
    zone_vnum   INTEGER NOT NULL DEFAULT 0,
    keywords    TEXT NOT NULL DEFAULT '',
    short_desc  TEXT NOT NULL DEFAULT '',
    long_desc   TEXT NOT NULL DEFAULT '',
    detail_desc TEXT NOT NULL DEFAULT '',
    level       INTEGER NOT NULL DEFAULT 1,
    max_hp      INTEGER NOT NULL DEFAULT 1,
    max_mana    INTEGER NOT NULL DEFAULT 0,
    max_move    INTEGER NOT NULL DEFAULT 0,
    armor_class INTEGER NOT NULL DEFAULT 100,
    hitroll     INTEGER NOT NULL DEFAULT 0,
    damroll     INTEGER NOT NULL DEFAULT 0,
    damage_dice TEXT NOT NULL DEFAULT '1d4+0',
    gold        INTEGER NOT NULL DEFAULT 0,
    experience  BIGINT NOT NULL DEFAULT 0,
    alignment   INTEGER NOT NULL DEFAULT 0,
    sex         SMALLINT NOT NULL DEFAULT 0,
    position    SMALLINT NOT NULL DEFAULT 8,
    class_id    INTEGER NOT NULL DEFAULT 0,
    race_id     INTEGER NOT NULL DEFAULT 0,
    act_flags   TEXT[] NOT NULL DEFAULT '{}',
    aff_flags   TEXT[] NOT NULL DEFAULT '{}',
    stats       JSONB NOT NULL DEFAULT '{}',
    skills      JSONB NOT NULL DEFAULT '{}',
    scripts     JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_mobs_zone ON mob_protos (zone_vnum);
CREATE INDEX idx_mobs_level ON mob_protos (level);
CREATE INDEX idx_mobs_act ON mob_protos USING GIN (act_flags);

-- Proto: 아이템
CREATE TABLE item_protos (
    vnum        INTEGER PRIMARY KEY,
    zone_vnum   INTEGER NOT NULL DEFAULT 0,
    keywords    TEXT NOT NULL DEFAULT '',
    short_desc  TEXT NOT NULL DEFAULT '',
    long_desc   TEXT NOT NULL DEFAULT '',
    item_type   TEXT NOT NULL DEFAULT 'other',
    weight      INTEGER NOT NULL DEFAULT 0,
    cost        INTEGER NOT NULL DEFAULT 0,
    min_level   INTEGER NOT NULL DEFAULT 0,
    wear_slots  TEXT[] NOT NULL DEFAULT '{}',
    flags       TEXT[] NOT NULL DEFAULT '{}',
    values      JSONB NOT NULL DEFAULT '{}',
    affects     JSONB NOT NULL DEFAULT '[]',
    extra_descs JSONB NOT NULL DEFAULT '[]',
    scripts     JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_items_zone ON item_protos (zone_vnum);
CREATE INDEX idx_items_type ON item_protos (item_type);
CREATE INDEX idx_items_flags ON item_protos USING GIN (flags);
CREATE INDEX idx_items_wear ON item_protos USING GIN (wear_slots);

-- Proto: 존
CREATE TABLE zones (
    vnum        INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    builders    TEXT NOT NULL DEFAULT '',
    lifespan    INTEGER NOT NULL DEFAULT 30,
    reset_mode  SMALLINT NOT NULL DEFAULT 2,
    level_range INT4RANGE,
    flags       TEXT[] NOT NULL DEFAULT '{}',
    resets      JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);

-- Proto: 스킬
CREATE TABLE skills (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    skill_type  TEXT NOT NULL DEFAULT 'spell',
    mana_cost   INTEGER NOT NULL DEFAULT 0,
    target      TEXT NOT NULL DEFAULT 'ignore',
    violent     BOOLEAN NOT NULL DEFAULT false,
    min_position SMALLINT NOT NULL DEFAULT 0,
    routines    TEXT[] NOT NULL DEFAULT '{}',
    wearoff_msg TEXT NOT NULL DEFAULT '',
    class_levels JSONB NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}'
);

-- Proto: 직업
CREATE TABLE classes (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    abbrev      TEXT NOT NULL DEFAULT '',
    hp_gain     INT4RANGE NOT NULL DEFAULT '[1,10)',
    mana_gain   INT4RANGE NOT NULL DEFAULT '[0,0)',
    move_gain   INT4RANGE NOT NULL DEFAULT '[0,0)',
    base_stats  JSONB NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}'
);

-- Proto: 종족
CREATE TABLE races (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    abbrev      TEXT NOT NULL DEFAULT '',
    stat_mods   JSONB NOT NULL DEFAULT '{}',
    body_parts  TEXT[] NOT NULL DEFAULT '{}',
    size        TEXT NOT NULL DEFAULT 'medium',
    ext         JSONB NOT NULL DEFAULT '{}'
);

-- Proto: 상점
CREATE TABLE shops (
    vnum          INTEGER PRIMARY KEY,
    keeper_vnum   INTEGER NOT NULL,
    room_vnum     INTEGER NOT NULL DEFAULT 0,
    buy_types     TEXT[] NOT NULL DEFAULT '{}',
    buy_profit    REAL NOT NULL DEFAULT 1.1,
    sell_profit   REAL NOT NULL DEFAULT 0.9,
    hours         JSONB NOT NULL DEFAULT '{}',
    inventory     JSONB NOT NULL DEFAULT '[]',
    messages      JSONB NOT NULL DEFAULT '{}',
    ext           JSONB NOT NULL DEFAULT '{}'
);

-- Proto: 퀘스트
CREATE TABLE quests (
    vnum        INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    quest_type  TEXT NOT NULL DEFAULT 'kill',
    level_range INT4RANGE,
    giver_vnum  INTEGER NOT NULL DEFAULT 0,
    target      JSONB NOT NULL DEFAULT '{}',
    rewards     JSONB NOT NULL DEFAULT '{}',
    chain       JSONB NOT NULL DEFAULT '{}',
    flags       TEXT[] NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}'
);

-- Proto: 소셜
CREATE TABLE socials (
    command     TEXT PRIMARY KEY,
    min_victim_position SMALLINT NOT NULL DEFAULT 0,
    messages    JSONB NOT NULL DEFAULT '{}'
);

-- Proto: 도움말
CREATE TABLE help_entries (
    id          SERIAL PRIMARY KEY,
    keywords    TEXT[] NOT NULL DEFAULT '{}',
    category    TEXT NOT NULL DEFAULT 'general',
    min_level   INTEGER NOT NULL DEFAULT 0,
    body        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_help_keywords ON help_entries USING GIN (keywords);

-- Proto: 전투 메시지
CREATE TABLE combat_messages (
    id          SERIAL PRIMARY KEY,
    skill_id    INTEGER NOT NULL,
    hit_type    TEXT NOT NULL,
    to_char     TEXT NOT NULL DEFAULT '',
    to_victim   TEXT NOT NULL DEFAULT '',
    to_room     TEXT NOT NULL DEFAULT '',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_cmsg_skill ON combat_messages (skill_id);

-- Proto: 시스템 텍스트
CREATE TABLE text_files (
    name        TEXT PRIMARY KEY,
    category    TEXT NOT NULL DEFAULT 'system',
    content     TEXT NOT NULL DEFAULT ''
);

-- Proto: 수치 테이블 (통합)
CREATE TABLE game_tables (
    table_name  TEXT NOT NULL,
    key         JSONB NOT NULL,
    value       JSONB NOT NULL,
    PRIMARY KEY (table_name, key)
);
CREATE INDEX idx_gtables_name ON game_tables (table_name);

-- Proto: 게임 설정
CREATE TABLE game_configs (
    key         TEXT PRIMARY KEY,
    value       JSONB NOT NULL,
    category    TEXT NOT NULL DEFAULT 'general',
    description TEXT NOT NULL DEFAULT ''
);

-- Instance: 플레이어
CREATE TABLE players (
    id            SERIAL PRIMARY KEY,
    name          TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL DEFAULT '',
    class_id      INTEGER NOT NULL DEFAULT 0,
    race_id       INTEGER NOT NULL DEFAULT 0,
    sex           SMALLINT NOT NULL DEFAULT 0,
    level         INTEGER NOT NULL DEFAULT 1,
    experience    BIGINT NOT NULL DEFAULT 0,
    hp            INTEGER NOT NULL DEFAULT 100,
    max_hp        INTEGER NOT NULL DEFAULT 100,
    mana          INTEGER NOT NULL DEFAULT 100,
    max_mana      INTEGER NOT NULL DEFAULT 100,
    move          INTEGER NOT NULL DEFAULT 100,
    max_move      INTEGER NOT NULL DEFAULT 100,
    gold          INTEGER NOT NULL DEFAULT 0,
    bank_gold     INTEGER NOT NULL DEFAULT 0,
    armor_class   INTEGER NOT NULL DEFAULT 100,
    alignment     INTEGER NOT NULL DEFAULT 0,
    stats         JSONB NOT NULL DEFAULT '{}',
    equipment     JSONB NOT NULL DEFAULT '{}',
    inventory     JSONB NOT NULL DEFAULT '[]',
    affects       JSONB NOT NULL DEFAULT '[]',
    skills        JSONB NOT NULL DEFAULT '{}',
    flags         TEXT[] NOT NULL DEFAULT '{}',
    aliases       JSONB NOT NULL DEFAULT '{}',
    title         TEXT NOT NULL DEFAULT '',
    description   TEXT NOT NULL DEFAULT '',
    room_vnum     INTEGER NOT NULL DEFAULT 0,
    org_id        INTEGER NOT NULL DEFAULT 0,
    org_rank      INTEGER NOT NULL DEFAULT 0,
    ext           JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login    TIMESTAMPTZ
);
CREATE INDEX idx_players_name ON players (name);
CREATE INDEX idx_players_level ON players (level);

-- Instance: 조직
CREATE TABLE organizations (
    id          SERIAL PRIMARY KEY,
    org_type    TEXT NOT NULL DEFAULT 'clan',
    name        TEXT NOT NULL DEFAULT '',
    leader      TEXT NOT NULL DEFAULT '',
    treasury    INTEGER NOT NULL DEFAULT 0,
    room_vnum   INTEGER NOT NULL DEFAULT 0,
    ext         JSONB NOT NULL DEFAULT '{}'
);

-- Instance: Lua 스크립트
CREATE TABLE lua_scripts (
    id          SERIAL PRIMARY KEY,
    game        TEXT NOT NULL DEFAULT '',
    category    TEXT NOT NULL DEFAULT '',
    name        TEXT NOT NULL DEFAULT '',
    source      TEXT NOT NULL DEFAULT '',
    version     INTEGER NOT NULL DEFAULT 1,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (game, category, name)
);

-- 선택적: 게시판
CREATE TABLE boards (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    board_type  TEXT NOT NULL DEFAULT 'general',
    room_vnum   INTEGER NOT NULL DEFAULT 0,
    min_read    INTEGER NOT NULL DEFAULT 0,
    min_write   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE board_posts (
    id          SERIAL PRIMARY KEY,
    board_id    INTEGER NOT NULL REFERENCES boards(id),
    author      TEXT NOT NULL DEFAULT '',
    subject     TEXT NOT NULL DEFAULT '',
    body        TEXT NOT NULL DEFAULT '',
    posted_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_bposts_board ON board_posts (board_id);
```

---

*GenOS Unified DB Schema v1.0 -- 2026-02-12*
