# GenOS Engine Architecture

**Version**: 1.0
**Last Updated**: 2026-02-10
**Author**: 누렁이

---

## 1. 개요 및 목표

GenOS는 레거시 한국어 MUD(CircleMUD 파생, 바이너리 C 구조체 등)를 현대적 아키텍처로 재구축하는 MUD 엔진이다. 마이그레이션 도구(genos-migration)가 기존 MUD 데이터를 추출하여 PostgreSQL SQL + Lua 스크립트 형태로 출력하면, GenOS 엔진이 이를 **무수정으로** 소비하여 게임 서버를 구동한다.

### 핵심 목표

1. **마이그레이션 데이터 무수정 소비**: 21개 SQL 테이블 + 8개 Lua 스크립트를 변환 없이 직접 로드
2. **한국어 자연어순(SOV) 명령어 네이티브 지원**: "고블린에게 불기둥으로 공격해" 같은 자연스러운 한국어 입력
3. **전통 MUD 게임플레이 보존**: THAC0 전투, Zone 리셋, 텍스트 기반 인터페이스
4. **현대적 접속 방식**: Telnet(전통) + WebSocket(웹) + REST API(관리)
5. **Lua 스크립팅 확장**: 게임 로직을 Lua로 확장, 핫 리로드 지원
6. **수천 동시접속 지원**: 비동기 I/O 기반 고성능 네트워크

### 지원 데이터 소스

마이그레이션 도구가 추출한 3개 소스의 데이터를 모두 소비 가능:

| 소스 | Rooms | Items | Mobs | Zones | Shops | Help | Skills |
|------|-------|-------|------|-------|-------|------|--------|
| tbaMUD | 12,700 | 4,765 | 3,705 | 189 | 334 | 721 | 65 |
| Simoon | 6,508 | 1,753 | 1,374 | 128 | 103 | 2,220 | 121 |
| 3eyes | 7,439 | 1,362 | 1,394 | 103 | — | 116 | 63 |

---

## 2. 기술 스택

| 계층 | 기술 | 이유 |
|------|------|------|
| 언어 | **Rust** | 메모리 안전, async/await, C 수준 성능, GC 없음 |
| 비동기 런타임 | **tokio** | 수천 동시접속, select() 대체, 타이머/채널 내장 |
| 스크립팅 | **mlua** (Lua 5.4) | 마이그레이션 출력이 Lua, 성숙한 FFI, 핫 리로드 |
| DB | **PostgreSQL 16** | JSONB 컬럼 활용, 마이그레이션 출력 직접 로드 |
| DB 드라이버 | **sqlx** (async) | 컴파일 타임 쿼리 검증, tokio 네이티브 |
| 웹 | **axum** | tokio 네이티브 HTTP/WebSocket, tower 미들웨어 |
| 직렬화 | **serde** + serde_json | JSONB ↔ Rust 구조체 자동 변환 |
| 프로토콜 | Telnet (RFC 854) + WebSocket + HTTP | 전통 + 현대 클라이언트 동시 지원 |

### Rust 선택 근거 (vs Go)

- **Lua FFI 성숙도**: mlua는 Lua 5.4 전체 API를 안전하게 노출. Go의 gopher-lua는 Lua 5.1 수준이며 성능 열위
- **GC 없음**: 10Hz 게임 루프에서 GC 일시정지가 없어 안정적 tick 보장
- **패턴 매칭 + enum**: 게임 상태 머신(전투 상태, 플레이어 상태 등)을 타입 안전하게 표현
- **소유권 시스템**: 동시성 버그를 컴파일 타임에 방지 (방에 있는 캐릭터 목록 등)

---

## 3. 아키텍처 계층도

```
┌─────────────────────────────────────────────────────────────────┐
│                        클라이언트 계층                            │
│   Telnet (포트 4000)   │  WebSocket (포트 8080)   │  REST API   │
└───────────┬────────────┴──────────┬───────────────┴──────┬──────┘
            │                       │                       │
┌───────────▼───────────────────────▼───────────────────────▼──────┐
│                        네트워크 계층 (tokio)                      │
│   TelnetCodec   │   WsCodec   │   axum Router                   │
│   ← MCCP2 / GMCP / MSSP 지원 →                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                        세션 / 명령어 계층                         │
│   SessionManager → CommandDispatcher                             │
│       │                  │                                       │
│       │           ┌──────┴──────┐                                │
│       │           │  KoreanNLP  │ ← korean_nlp.lua               │
│       │           │  SOV Parser │ ← korean_commands.lua           │
│       │           └─────────────┘                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                        게임 로직 계층                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│   │ Combat   │  │ Movement │  │  Shop    │  │  Zone Reset   │  │
│   │ Engine   │  │ Engine   │  │  System  │  │  Scheduler    │  │
│   └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│   │ Social   │  │  Quest   │  │  Skill   │  │  Lua Script   │  │
│   │ System   │  │  System  │  │  System  │  │  Engine       │  │
│   └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                        월드 모델 계층                             │
│   World { rooms, items, monsters, zones, ... }                   │
│   Prototype (VNUM 기반, 불변) → Instance (런타임 ID, 가변)        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                        영속성 계층                                │
│   PostgreSQL 16 (21 마이그레이션 테이블 + players 테이블)         │
│   sqlx async pool  │  Redis (선택: 세션 캐시)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 부트 시퀀스

```
1. 설정 로드 (config.toml)
   - DB 연결 정보, 포트, 게임 설정 경로

2. PostgreSQL 연결 풀 초기화
   - sqlx::PgPool::connect() (max_connections = 10)

3. 월드 데이터 로드 (21 테이블 → 메모리)
   - rooms, items, monsters → Prototype HashMap<Vnum, T>
   - zones → ZoneManager (리셋 타이머 초기화)
   - shops, quests, socials, help_entries → 참조 테이블
   - commands, skills, races → 참조 테이블
   - game_configs → GameConfig 싱글톤
   - experience_table, thac0_table, saving_throws → StatTables 싱글톤
   - level_titles, attribute_modifiers, practice_params → StatTables 싱글톤

4. Lua VM 초기화
   - korean_nlp.lua 로드 (KoreanNLP 모듈)
   - korean_commands.lua 로드 (Commands 모듈)
   - combat.lua, classes.lua 로드
   - config.lua, exp_tables.lua, stat_tables.lua 로드
   - triggers.lua 로드 (있으면)
   - 엔진 API 함수 등록 (send_to_char, damage 등)

5. Zone 초기 리셋
   - 모든 Zone의 reset_commands 1회 실행
   - 몬스터/아이템 스폰, 문 상태 초기화

6. 네트워크 리스너 시작
   - Telnet: 0.0.0.0:4000
   - WebSocket: 0.0.0.0:8080
   - REST API: 0.0.0.0:8081

7. 게임 루프 시작 (10Hz tick)

8. Zone 리셋 스케줄러 시작
   - 각 Zone의 lifespan에 따라 주기적 리셋
```

---

## 5. 게임 루프 (10Hz 하이브리드)

전통 MUD(tbaMUD)의 10Hz tick 기반 게임 루프를 tokio single-task로 구현한다. 네트워크 I/O는 별도 tokio task에서 비동기 처리하고, 게임 상태 변경은 단일 task에서만 수행하여 동시성 문제를 원천 차단한다.

```
┌────────────────────────── 100ms tick ───────────────────────────┐
│                                                                  │
│  1. 입력 수집                                                    │
│     - 각 세션의 명령어 큐에서 dequeue (mpsc channel)              │
│     - 접속/접속해제 이벤트 처리                                   │
│                                                                  │
│  2. 명령어 처리                                                  │
│     - 한국어 SOV 파싱 (Lua Commands.parse 호출)                  │
│     - 핸들러 디스패치 (Rust handler_map)                         │
│     - 이동, 아이템, 대화 등 처리                                  │
│                                                                  │
│  3. 전투 라운드 (매 20tick = 2초)                                │
│     - fighting 상태인 모든 캐릭터 쌍 순회                        │
│     - THAC0 명중 판정 + 데미지 계산                              │
│     - HP 감소, 사망 처리, 전리품 생성                             │
│                                                                  │
│  4. Zone 리셋 (타이머 만료 시)                                   │
│     - reset_commands 실행                                        │
│     - 몬스터/아이템 리스폰                                       │
│                                                                  │
│  5. 환경 업데이트                                                │
│     - 게임 내 시간 진행                                          │
│     - 날씨 변경                                                  │
│     - 버프/디버프 타이머 감소                                     │
│     - Lua 타이머 트리거 실행                                     │
│                                                                  │
│  6. 출력 플러시                                                  │
│     - 각 세션의 출력 버퍼를 네트워크 task로 전송                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 동시성 모델

```
┌─────────────────┐     mpsc channel     ┌──────────────────┐
│  Network Task   │ ──── 입력 큐 ──────▶ │                  │
│  (per session)  │                       │   Game Loop      │
│  - Telnet read  │ ◀── 출력 큐 ──────── │   Task (단일)    │
│  - Telnet write │     mpsc channel      │                  │
└─────────────────┘                       │  - 명령어 처리    │
                                          │  - 전투 라운드    │
┌─────────────────┐     mpsc channel      │  - Zone 리셋     │
│  Network Task   │ ──── 입력 큐 ──────▶ │  - 환경 업데이트  │
│  (WebSocket)    │                       │                  │
│                 │ ◀── 출력 큐 ──────── │                  │
└─────────────────┘     mpsc channel      └────────┬─────────┘
                                                    │
                                          oneshot/  │ async
                                          mpsc      │ spawn
                                                    ▼
                                          ┌──────────────────┐
                                          │  DB Writer Task   │
                                          │  - 플레이어 저장   │
                                          │  - 비동기 쓰기     │
                                          └──────────────────┘
```

- **게임 루프 task**: 단일 tokio task. 모든 게임 상태 변경이 여기서만 발생 → `Mutex` 불필요
- **네트워크 task**: 세션당 1개. 입력을 읽어 큐에 넣고, 출력 큐에서 꺼내 전송
- **DB writer task**: 비동기 DB 쓰기 전담. 게임 루프가 블로킹되지 않음

---

## 6. 네트워크 계층

### 6.1 Telnet (전통 MUD 클라이언트)

- **RFC 854** 기본 Telnet 프로토콜
- **MCCP2** (Mud Client Compression Protocol v2): zlib 압축으로 대역폭 절약
- **GMCP** (Generic MUD Communication Protocol): 구조화된 JSON 데이터 (HP바, 미니맵 등)
- **MSSP** (MUD Server Status Protocol): MUD 목록 사이트에 서버 정보 노출
- **인코딩**: EUC-KR/UTF-8 자동 감지 (레거시 한국어 클라이언트 지원)
- **ANSI 색상**: 16색 + 256색 + 트루컬러 지원
- **라인 모드**: 줄바꿈 단위 입력 처리

### 6.2 WebSocket (현대 웹 클라이언트)

- **axum + tungstenite** 기반
- **JSON 메시지 프로토콜**:
  ```json
  // 서버 → 클라이언트
  {"type": "room", "data": {"vnum": 3001, "name": "마을 광장", "exits": ["north", "south"]}}
  {"type": "combat", "data": {"attacker": "전사", "target": "고블린", "damage": 15}}
  {"type": "text", "data": {"message": "고블린이 쓰러졌습니다!", "color": "green"}}

  // 클라이언트 → 서버
  {"type": "command", "data": {"input": "고블린을 공격해"}}
  ```
- 웹 기반 MUD 클라이언트 UI와 연동

### 6.3 REST API (관리/OLC)

- **axum** 기반 HTTP API
- **JWT 인증**: 관리자 토큰 기반
- **엔드포인트**:
  - `GET /api/server/status` — 서버 상태 (접속자, 업타임, Zone 상태)
  - `GET/PUT/POST /api/rooms/:vnum` — 방 CRUD (OLC)
  - `GET/PUT/POST /api/items/:vnum` — 아이템 CRUD
  - `GET/PUT/POST /api/monsters/:vnum` — 몬스터 CRUD
  - `POST /api/server/reload` — Lua 스크립트 핫 리로드
  - `POST /api/server/shutdown` — 서버 종료

---

## 7. 명령어 디스패치 + 한국어 SOV 파서

명령어 처리는 **Lua 파싱 + Rust 실행** 하이브리드 구조이다.

### 처리 흐름

```
입력: "고블린에게 불기둥으로 공격해"
  │
  ▼
┌───────────────────────────────────────────┐
│ 1. Lua Commands.parse(input) 호출          │
│                                            │
│    토크나이징: ["고블린에게", "불기둥으로",   │
│                "공격해"]                    │
│    동사 탐색:  "공격해" → 어간 "공격"       │
│               → VERBS["공격"] = "attack"   │
│    조사 스트리핑:                           │
│      "고블린에게" → "고블린" (role: target)  │
│      "불기둥으로" → "불기둥" (role: dir)     │
│                                            │
│    결과: {handler="attack",                │
│           roles={target="고블린",           │
│                  dir="불기둥"},             │
│           ordered={"고블린","불기둥"}}       │
└────────────────────┬──────────────────────┘
                     ▼
┌───────────────────────────────────────────┐
│ 2. Rust CommandDispatcher                  │
│    handler_map["attack"]                   │
│    → CombatEngine::do_attack(ch, parsed)   │
└────────────────────┬──────────────────────┘
                     ▼
┌───────────────────────────────────────────┐
│ 3. Target Resolution                       │
│    "고블린" → Room에서 Monster 검색         │
│    keyword 매칭 (한글/영문 동시 지원)       │
│    Monster.keywords에서 부분 매칭           │
└───────────────────────────────────────────┘
```

### 설계 원칙

- **Lua가 파싱**: 동사/조사 매핑은 데이터 테이블이므로 Lua에 적합. 핫 리로드로 운영 중 수정 가능
- **Rust가 실행**: 게임 상태 변경(HP 감소, 아이템 이동 등)은 Rust에서 안전하게 처리
- **SVO 폴백**: SOV 파싱 실패 시 첫 토큰을 동사로 시도 (기존 MUD 호환: "attack goblin")
- **방향어 직접 처리**: "북", "남쪽" 등은 DIRECTIONS 테이블에서 방향 번호로 변환
- **스펠 직접 캐스팅**: SPELL_NAMES 테이블에 한국어 스펠 이름 매핑 (UIR skills에서 추출)

---

## 8. 월드 모델 (Prototype/Instance 패턴)

VNUM 기반 Prototype과 런타임 Instance를 분리하는 전통적 MUD 데이터 모델을 채택한다.

### Prototype (불변, DB에서 로드)

```rust
/// 방 프로토타입 — rooms 테이블에서 로드
struct RoomProto {
    vnum: Vnum,
    name: String,
    description: String,
    zone_number: i32,
    sector_type: i32,
    room_flags: Vec<i32>,       // JSONB에서 파싱
    exits: Vec<ExitProto>,      // JSONB에서 파싱
    extra_descs: Vec<ExtraDesc>,
    trigger_vnums: Vec<Vnum>,
}

/// 아이템 프로토타입 — items 테이블에서 로드
struct ItemProto {
    vnum: Vnum,
    keywords: String,
    short_description: String,
    long_description: String,
    item_type: i32,
    extra_flags: Vec<i32>,
    wear_flags: Vec<i32>,
    values: [i32; 4],
    weight: i32,
    cost: i32,
    affects: Vec<ItemAffect>,
    trigger_vnums: Vec<Vnum>,
}

/// 몬스터 프로토타입 — monsters 테이블에서 로드
struct MobProto {
    vnum: Vnum,
    keywords: String,
    short_description: String,
    long_description: String,
    detailed_description: String,
    level: i32,
    hitroll: i32,
    armor_class: i32,
    hp_dice: DiceRoll,          // "3d8+30" → DiceRoll { num:3, size:8, bonus:30 }
    damage_dice: DiceRoll,
    gold: i32,
    experience: i32,
    action_flags: Vec<i32>,
    affect_flags: Vec<i32>,
    trigger_vnums: Vec<Vnum>,
}
```

### Instance (가변, 런타임 생성)

```rust
/// 방 인스턴스 — 런타임 상태
struct RoomInstance {
    proto: &RoomProto,
    characters: Vec<CharId>,        // 방에 있는 캐릭터
    ground_items: Vec<ItemInstance>, // 바닥에 있는 아이템
    door_states: HashMap<i32, DoorState>, // 방향 → 문 상태
}

/// 아이템 인스턴스 — Zone 리셋 또는 드랍으로 생성
struct ItemInstance {
    id: InstanceId,             // monotonic u64 카운터
    proto: &ItemProto,
    // 인스턴스 고유 상태 (향후 확장)
    // durability, enchantments, etc.
}

/// 캐릭터 인스턴스 — PC(플레이어) 또는 NPC(몬스터)
struct CharInstance {
    id: CharId,
    proto: Option<&MobProto>,   // NPC면 Some, PC면 None
    name: String,               // PC: 플레이어 이름, NPC: proto.short_description
    room: Vnum,
    // 스탯
    level: i32,
    hp: i32,
    max_hp: i32,
    mana: i32,
    max_mana: i32,
    move_points: i32,
    max_move: i32,
    // 전투
    hitroll: i32,
    armor_class: i32,
    fighting: Option<CharId>,
    // 장비/인벤토리
    inventory: Vec<ItemInstance>,
    equipment: [Option<ItemInstance>; 18], // NUM_WEARS = 18
    // PC 전용
    class_id: i32,
    race_id: i32,
    gold: i32,
    experience: i64,
    // 기타
    affects: Vec<Affect>,
    position: Position,         // Standing, Sitting, Sleeping, Fighting, ...
}
```

### Zone 리셋과 Instance 생명주기

```
Zone 리셋 (M 명령어)
  → MobProto에서 hp_dice 굴림 → max_hp 결정
  → CharInstance 생성, room에 배치

Zone 리셋 (O 명령어)
  → ItemProto에서 ItemInstance 생성
  → room.ground_items에 추가

몬스터 사망
  → CharInstance 제거
  → 전리품(gold, loot) ItemInstance 생성

플레이어 로그아웃
  → CharInstance → DB 저장 후 메모리에서 제거
```

---

## 9. 전투 엔진 (THAC0 기반)

마이그레이션 출력의 전투 데이터를 소비하여 THAC0 기반 전투를 구현한다.

### 소비하는 마이그레이션 데이터

| 출력 | 용도 |
|------|------|
| `combat.lua` | ATTACK_TYPES 이름, calculate_hit(), roll_damage() 함수 |
| `thac0_table` SQL | 클래스별/레벨별 THAC0 값 (tbaMUD 140행, 3eyes 160행) |
| `saving_throws` SQL | 클래스별/세이브타입별/레벨별 세이빙 값 (tbaMUD 870행) |
| `stat_tables.lua` | 능력치 보정 (str→tohit/todam, dex→ac 등) |
| `attribute_modifiers` SQL | 능력치별 보정 테이블 |

### 전투 흐름

```
1. 전투 개시
   - 플레이어가 "공격해" 명령 입력 또는 aggro 몬스터가 공격
   - attacker.fighting = target, target.fighting = attacker
   - 양측 position = Fighting

2. 전투 라운드 (매 2초 = 20 tick)
   a. THAC0 조회
      thac0 = thac0_table[attacker.class_id][attacker.level]
      // Lua: Combat.get_thac0(class_id, level)

   b. 명중 판정
      roll = d20
      needed = thac0 - target.armor_class - attacker.hitroll
      hit = (roll >= needed)
      // Lua: Combat.calculate_hit(thac0, ac, hitroll)

   c. 데미지 계산 (명중 시)
      damage = roll_dice(attacker.damage_dice) + str_bonus
      // Lua: Combat.roll_damage(num, size, bonus)

   d. 세이빙 스로우 (스펠 데미지 시)
      save = saving_throws[target.class_id][save_type][target.level]
      roll = d20
      saved = (roll <= save)

   e. HP 감소
      target.hp -= damage
      if target.hp <= 0: 사망 처리

3. 사망 처리
   - 경험치 지급 (monsters.experience)
   - 전리품 생성 (monsters.gold → gold_item)
   - 시체 생성 (corpse container)
   - CharInstance 제거

4. 전투 종료
   - 한쪽 사망, 도주(flee), 또는 다른 방으로 이동
```

---

## 10. Zone 리셋 시스템

마이그레이션 출력의 `zones` 테이블에서 `reset_commands` JSONB를 로드하여 실행한다.

### 리셋 명령어 유형

| 명령어 | 의미 | arg1 | arg2 | arg3 |
|--------|------|------|------|------|
| M | 몬스터 스폰 | mob_vnum | max_count | room_vnum |
| O | 아이템 로드 (방) | item_vnum | max_count | room_vnum |
| G | 아이템 지급 (마지막 M) | item_vnum | max_count | — |
| E | 장비 장착 (마지막 M) | item_vnum | max_count | wear_pos |
| P | 아이템 넣기 (컨테이너) | item_vnum | max_count | container_vnum |
| D | 문 상태 설정 | room_vnum | direction | state |
| T | 트리거 첨부 | trigger_type | trigger_vnum | target_vnum |

### 리셋 모드

```rust
enum ResetMode {
    Never    = 0,  // 리셋 안 함
    Empty    = 1,  // 방에 플레이어 없을 때만
    Always   = 2,  // 항상 리셋
}
```

### 리셋 스케줄링

```
각 Zone에 대해:
  - 타이머 = zone.lifespan 분
  - 매 tick에서 타이머 감소
  - 타이머 만료 시:
    if reset_mode == Never → skip
    if reset_mode == Empty → Zone 내 모든 방에 플레이어 없으면 실행
    if reset_mode == Always → 실행
  - reset_commands 순서대로 실행
  - if_flag 확인: 이전 명령어 성공 시에만 실행 (G, E는 M 성공 후)
  - max_count 확인: 이미 max_count 이상 존재하면 skip
```

---

## 11. Lua 스크립팅 엔진

mlua를 통해 Lua 5.4 VM을 통합한다. 마이그레이션 출력 Lua 8개를 읽기 전용으로 로드하고, 사용자 스크립트는 핫 리로드를 지원한다.

### 통합 구조

```
Lua VM (single instance, 게임 루프 task 소유)
  │
  ├─ 마이그레이션 출력 Lua (읽기 전용 모듈)
  │   ├─ combat.lua       → Combat 모듈
  │   ├─ classes.lua      → Classes 모듈
  │   ├─ triggers.lua     → 개별 트리거 스크립트
  │   ├─ config.lua       → GameConfig 모듈
  │   ├─ exp_tables.lua   → ExpTables 모듈
  │   ├─ stat_tables.lua  → StatTables 모듈
  │   ├─ korean_nlp.lua   → KoreanNLP 모듈
  │   └─ korean_commands.lua → Commands 모듈
  │
  ├─ 엔진 API (Rust → Lua 바인딩)
  │   ├─ send_to_char(char_id, message)
  │   ├─ send_to_room(room_vnum, message, except_char_id)
  │   ├─ get_char_room(room_vnum, keyword) → char_id
  │   ├─ get_obj_room(room_vnum, keyword) → item_id
  │   ├─ damage(attacker_id, victim_id, amount)
  │   ├─ move_char(char_id, direction)
  │   ├─ load_mob(mob_vnum, room_vnum) → char_id
  │   ├─ load_obj(item_vnum, room_vnum) → item_id
  │   ├─ purge(target_id)
  │   └─ ... (DG Script 호환 API 30+ 함수)
  │
  └─ 사용자/플러그인 스크립트 (핫 리로드)
      └─ plugins/*.lua
```

### DG Script → Lua 트리거 실행

마이그레이션 도구가 DG Script를 Lua로 변환하여 `triggers.lua`에 저장한다. 엔진은 트리거 이벤트 발생 시 해당 Lua 함수를 호출한다.

```lua
-- triggers.lua (마이그레이션 출력)
trigger_100 = function(self, actor, arg)
    -- on_greet 트리거: 방에 들어올 때 실행
    send_to_char(actor, "경비병이 당신을 노려봅니다.")
    if get_level(actor) < 10 then
        send_to_char(actor, "경비병이 길을 막습니다!")
        return false  -- 이동 차단
    end
    return true
end
```

### 트리거 이벤트 유형

| 이벤트 | attach_type | 발생 시점 |
|--------|-------------|-----------|
| on_greet | MOB | 캐릭터가 방에 들어올 때 |
| on_speech | MOB | 방에서 누가 말할 때 |
| on_command | MOB/OBJ/WLD | 명령어 입력 시 |
| on_timer | MOB | 타이머 만료 시 |
| on_get | OBJ | 아이템을 주울 때 |
| on_drop | OBJ | 아이템을 버릴 때 |
| on_enter | WLD | 방에 들어올 때 |
| on_reset | WLD | Zone 리셋 시 |

---

## 12. 상점 / 소셜 / 도움말 / 퀘스트

### 12.1 상점 시스템 (shops 테이블)

```
플레이어: "검을 사" (또는 "buy sword")
  │
  ├─ 현재 방의 keeper_vnum과 일치하는 NPC 확인
  ├─ shop.open1~close2로 영업시간 확인
  ├─ 키워드로 selling_items에서 아이템 검색
  ├─ 가격 = item.cost × shop.profit_buy
  ├─ 골드 확인 → ItemInstance 생성 → 인벤토리 추가
  └─ 골드 차감
```

### 12.2 소셜 시스템 (socials 테이블)

```
플레이어: "미소" (또는 "smile")
  │
  ├─ socials 테이블에서 command 매칭
  ├─ 타겟 유무에 따라 메시지 선택:
  │   - 타겟 없음: no_arg_to_char, no_arg_to_room
  │   - 타겟 있음: found_to_char, found_to_room, found_to_victim
  │   - 자신: self_to_char, self_to_room
  ├─ 메시지 템플릿 치환: $n → 행위자, $N → 대상
  └─ 한국어 조사 처리 (엔진 빌트인)
```

### 12.3 도움말 시스템 (help_entries 테이블)

```
플레이어: "도움 전투" (또는 "help combat")
  │
  ├─ help_entries.keywords JSONB에서 키워드 검색
  ├─ 한국어/영문 동시 매칭
  ├─ min_level 필터링 (레벨 이하만 표시)
  └─ text 필드 출력 (ANSI 색상 지원)
```

### 12.4 퀘스트 시스템 (quests 테이블)

```
플레이어: 퀘스트 NPC와 대화
  │
  ├─ quests.mob_vnum으로 퀘스트 검색
  ├─ prev_quest 확인 (선행 퀘스트 완료 여부)
  ├─ min_level/max_level 확인
  ├─ quest_type에 따라 목표 추적:
  │   - kill: target_vnum 몬스터 처치 카운트
  │   - collect: target_vnum 아이템 수집
  │   - explore: target_vnum 방 방문
  ├─ 완료 시: reward_gold, reward_exp, reward_obj 지급
  └─ next_quest 활성화
```

---

## 13. PostgreSQL 영속성

### 부트 시 로드 (마이그레이션 데이터, 읽기 전용)

```sql
-- 21개 마이그레이션 테이블을 전체 SELECT하여 메모리에 로드
SELECT * FROM rooms;              -- → HashMap<Vnum, RoomProto>
SELECT * FROM items;              -- → HashMap<Vnum, ItemProto>
SELECT * FROM monsters;           -- → HashMap<Vnum, MobProto>
SELECT * FROM classes;            -- → Vec<CharacterClass>
SELECT * FROM zones;              -- → Vec<Zone>
SELECT * FROM shops;              -- → HashMap<Vnum, Shop>
SELECT * FROM triggers;           -- → HashMap<Vnum, Trigger>
SELECT * FROM quests;             -- → HashMap<Vnum, Quest>
SELECT * FROM socials;            -- → HashMap<String, Social>
SELECT * FROM help_entries;       -- → Vec<HelpEntry>
SELECT * FROM commands;           -- → HashMap<String, Command>
SELECT * FROM skills;             -- → HashMap<i32, Skill>
SELECT * FROM races;              -- → Vec<Race>
SELECT * FROM game_configs;       -- → HashMap<String, GameConfig>
SELECT * FROM experience_table;   -- → HashMap<(class_id, level), i64>
SELECT * FROM thac0_table;        -- → HashMap<(class_id, level), i32>
SELECT * FROM saving_throws;      -- → HashMap<(class_id, save_type, level), i32>
SELECT * FROM level_titles;       -- → HashMap<(class_id, level, gender), String>
SELECT * FROM attribute_modifiers;-- → HashMap<(stat_name, score), Modifiers>
SELECT * FROM practice_params;    -- → HashMap<class_id, PracticeParams>
```

### 런타임 저장 (플레이어 데이터)

마이그레이션 범위 밖이지만 엔진에 필수인 테이블:

```sql
CREATE TABLE players (
    id              SERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    class_id        INTEGER REFERENCES classes(id),
    race_id         INTEGER REFERENCES races(id),
    level           INTEGER DEFAULT 1,
    hp              INTEGER,
    max_hp          INTEGER,
    mana            INTEGER,
    max_mana        INTEGER,
    move_points     INTEGER,
    max_move        INTEGER,
    room_vnum       INTEGER DEFAULT 3001,  -- 시작 방
    gold            INTEGER DEFAULT 0,
    experience      BIGINT DEFAULT 0,
    equipment       JSONB DEFAULT '{}',     -- wear_pos → item_vnum
    inventory       JSONB DEFAULT '[]',     -- [item_vnum, ...]
    affects         JSONB DEFAULT '[]',     -- [{type, duration, modifier}, ...]
    quest_progress  JSONB DEFAULT '{}',     -- {quest_vnum: {state, count}, ...}
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_login      TIMESTAMPTZ
);

CREATE INDEX idx_players_name ON players(name);
```

### 저장 전략

- **비동기 저장**: 게임 루프에서 `tokio::spawn`으로 DB 쓰기 task 위임
- **자동 저장**: 5분마다 온라인 플레이어 전원 저장
- **로그아웃 저장**: 정상/비정상 접속 해제 시 즉시 저장
- **배치 처리**: 여러 플레이어 업데이트를 하나의 트랜잭션으로 묶음

---

## 14. 한국어 NLP 모듈 (엔진 빌트인)

마이그레이션 출력의 Lua NLP 모듈을 엔진에서 로드하되, 핵심 NLP 로직은 **Rust 네이티브**로도 구현한다.

### 역할 분담

| 기능 | 구현 위치 | 이유 |
|------|-----------|------|
| 입력 파싱 (SOV) | Lua (korean_commands.lua) | 동사/조사 매핑 핫 리로드 |
| 동사 어간 추출 | Lua (korean_nlp.lua) | 어미 목록 수정 용이 |
| 조사 스트리핑 | Lua (korean_nlp.lua) | 조사 목록 수정 용이 |
| 출력 조사 선택 | **Rust 네이티브** | 성능, 메시지 시스템 통합 |
| 받침 검사 | **Rust 네이티브** | Unicode 연산, 성능 |
| 메시지 템플릿 | **Rust 네이티브** | 조사 자동 선택 통합 |

### Rust 네이티브 한국어 모듈

```rust
/// 받침(종성) 검사 — Unicode 수학
fn has_batchim(s: &str) -> bool {
    s.chars().rev().find(|&c| ('\u{AC00}'..='\u{D7A3}').contains(&c))
        .map(|c| (c as u32 - 0xAC00) % 28 != 0)
        .unwrap_or(false)
}

/// 출력용 조사 선택
enum ParticleType { Subject, Object, Topic, Comitative, Instrumental, Copula }

fn particle(noun: &str, ptype: ParticleType) -> &'static str {
    let batchim = has_batchim(noun);
    match (ptype, batchim) {
        (ParticleType::Subject, true)  => "이",
        (ParticleType::Subject, false) => "가",
        (ParticleType::Object, true)   => "을",
        (ParticleType::Object, false)  => "를",
        (ParticleType::Topic, true)    => "은",
        (ParticleType::Topic, false)   => "는",
        (ParticleType::Comitative, true)  => "과",
        (ParticleType::Comitative, false) => "와",
        (ParticleType::Instrumental, true)  => "으로",
        (ParticleType::Instrumental, false) => "로",
        (ParticleType::Copula, true)  => "이다",
        (ParticleType::Copula, false) => "다",
    }
}

/// 메시지 템플릿 렌더링
/// 입력: "{name}{이/가} {target}{을/를} 공격합니다."
/// 변수: name="전사", target="고블린"
/// 출력: "전사가 고블린을 공격합니다."
fn render_message(template: &str, vars: &HashMap<&str, &str>) -> String {
    // {name} → 변수 치환
    // {이/가} → 직전 명사의 받침에 따라 선택
    ...
}
```

---

## 15. 관리자 / OLC 시스템

### REST API 기반 웹 대시보드

```
GET  /api/server/status           서버 상태 (접속자, 업타임, 메모리)
GET  /api/server/zones            Zone 상태 (리셋 타이머, 인구)

GET  /api/rooms                   방 목록 (페이지네이션)
GET  /api/rooms/:vnum             방 상세
PUT  /api/rooms/:vnum             방 수정 → DB 업데이트 + Prototype 핫 리로드
POST /api/rooms                   방 생성

GET  /api/items/:vnum             아이템 상세
PUT  /api/items/:vnum             아이템 수정
GET  /api/monsters/:vnum          몬스터 상세
PUT  /api/monsters/:vnum          몬스터 수정

POST /api/server/reload           Lua 스크립트 핫 리로드
POST /api/server/shutdown         서버 종료 (카운트다운)
```

### 인게임 OLC (전통 MUD 관리)

```
redit <vnum>    방 편집 모드 진입
oedit <vnum>    아이템 편집 모드 진입
medit <vnum>    몬스터 편집 모드 진입
zedit <vnum>    Zone 편집 모드 진입

set <필드> <값>  편집 중인 엔티티 필드 수정
done            편집 완료 → DB 저장 + Prototype 리로드
```

OLC 수정은 DB에 직접 반영되며, 메모리의 Prototype을 핫 리로드한다.

---

## 16. 데이터 매핑 매트릭스

마이그레이션 도구 출력 → GenOS 엔진 소비 전체 매핑:

### SQL 테이블 (21개)

| 테이블 | 엔진 소비 위치 | Rust 타입 | 로드 시점 |
|--------|---------------|-----------|-----------|
| rooms | World.rooms | HashMap<Vnum, RoomProto> | 부트 |
| items | World.item_protos | HashMap<Vnum, ItemProto> | 부트 |
| monsters | World.mob_protos | HashMap<Vnum, MobProto> | 부트 |
| classes | World.classes | Vec\<CharacterClass\> | 부트 |
| zones | ZoneManager.zones | Vec\<Zone\> | 부트 |
| shops | ShopSystem.shops | HashMap<Vnum, Shop> | 부트 |
| triggers | LuaEngine.triggers | HashMap<Vnum, TriggerDef> | 부트 |
| quests | QuestSystem.quests | HashMap<Vnum, Quest> | 부트 |
| socials | SocialSystem.socials | HashMap<String, Social> | 부트 |
| help_entries | HelpSystem.entries | Vec\<HelpEntry\> | 부트 |
| commands | CommandDispatcher.cmds | HashMap<String, CommandDef> | 부트 |
| skills | SkillSystem.skills | HashMap<i32, Skill> | 부트 |
| races | World.races | Vec\<Race\> | 부트 |
| game_configs | GameConfig 싱글톤 | HashMap<String, ConfigValue> | 부트 |
| experience_table | StatTables.exp | HashMap<(i32,i32), i64> | 부트 |
| thac0_table | StatTables.thac0 | HashMap<(i32,i32), i32> | 부트 |
| saving_throws | StatTables.saves | HashMap<(i32,i32,i32), i32> | 부트 |
| level_titles | StatTables.titles | HashMap<(i32,i32,String), String> | 부트 |
| attribute_modifiers | StatTables.attr_mods | HashMap<(String,i32), Mods> | 부트 |
| practice_params | StatTables.practice | HashMap<i32, PracticeParams> | 부트 |

### Lua 스크립트 (8개)

| 파일 | 엔진 소비 위치 | 호출 방식 |
|------|---------------|-----------|
| combat.lua | CombatEngine | Lua 함수 호출 (calculate_hit, roll_damage) |
| classes.lua | CharacterSystem | Lua 함수 호출 (level_up logic) |
| triggers.lua | LuaEngine | 이벤트 기반 트리거 함수 호출 |
| config.lua | Lua 코드 내 설정 접근 | require("config") |
| exp_tables.lua | Lua 코드 내 경험치 조회 | require("exp_tables") |
| stat_tables.lua | Lua 코드 내 능력치 조회 | require("stat_tables") |
| korean_nlp.lua | CommandDispatcher | Lua 함수 호출 (has_batchim, strip_particle 등) |
| korean_commands.lua | CommandDispatcher | Lua 함수 호출 (Commands.parse) |

---

## 17. Rust 크레이트 구조

```
genos-engine/
├── Cargo.toml                  # workspace 정의
├── crates/
│   ├── genos-core/             # 핵심 타입 정의
│   │   └── src/lib.rs          # Vnum, InstanceId, DiceRoll, Position, etc.
│   │
│   ├── genos-world/            # 월드 모델
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── room.rs         # RoomProto, RoomInstance
│   │       ├── item.rs         # ItemProto, ItemInstance
│   │       ├── mob.rs          # MobProto, CharInstance
│   │       ├── zone.rs         # Zone, ZoneManager, 리셋 로직
│   │       └── world.rs        # World 통합 구조체
│   │
│   ├── genos-net/              # 네트워크 계층
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── telnet.rs       # Telnet 서버 + codec
│   │       ├── websocket.rs    # WebSocket 서버
│   │       └── session.rs      # SessionManager, 입출력 큐
│   │
│   ├── genos-combat/           # 전투 엔진
│   │   └── src/lib.rs          # THAC0 판정, 데미지, 사망 처리
│   │
│   ├── genos-lua/              # Lua 스크립팅 통합
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── engine.rs       # Lua VM 관리, 모듈 로드
│   │       ├── api.rs          # Rust→Lua API 바인딩
│   │       └── triggers.rs     # 트리거 이벤트 디스패치
│   │
│   ├── genos-korean/           # 한국어 NLP (Rust 네이티브)
│   │   └── src/lib.rs          # has_batchim, particle, render_message
│   │
│   ├── genos-db/               # PostgreSQL 영속성
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── loader.rs       # 21 테이블 로드
│   │       └── player.rs       # 플레이어 저장/로드
│   │
│   └── genos-admin/            # REST API + OLC
│       └── src/
│           ├── lib.rs
│           ├── routes.rs       # axum 라우터
│           └── olc.rs          # 인게임 OLC 명령어
│
├── src/
│   └── main.rs                 # 엔진 진입점, 부트 시퀀스
│
├── sql/                        # ← 마이그레이션 출력 복사
│   ├── schema.sql
│   └── seed_data.sql
│
├── lua/                        # ← 마이그레이션 출력 복사
│   ├── combat.lua
│   ├── classes.lua
│   ├── triggers.lua
│   ├── config.lua
│   ├── exp_tables.lua
│   ├── stat_tables.lua
│   ├── korean_nlp.lua
│   └── korean_commands.lua
│
├── plugins/                    # 사용자 Lua 플러그인
│   └── example.lua
│
└── config.toml                 # 엔진 설정
```

### config.toml 예시

```toml
[server]
name = "GenOS MUD"
telnet_port = 4000
websocket_port = 8080
api_port = 8081
tick_rate_hz = 10

[database]
url = "postgresql://genos:password@localhost/genos"
max_connections = 10

[game]
start_room = 3001
max_level = 34
pk_allowed = false
auto_save_minutes = 5

[lua]
script_dir = "lua/"
plugin_dir = "plugins/"
hot_reload = true

[logging]
level = "info"
file = "logs/genos.log"
```

---

## 18. 확장성 및 플러그인

### Lua 플러그인 시스템

```lua
-- plugins/auction.lua
local Plugin = {}

Plugin.name = "경매 시스템"
Plugin.version = "1.0"

-- 커스텀 명령어 등록
function Plugin.init()
    register_command("경매", Plugin.do_auction)
    register_command("auction", Plugin.do_auction)
end

function Plugin.do_auction(ch, args)
    -- 경매 로직
    send_to_char(ch, "경매 시스템입니다.")
end

return Plugin
```

### 이벤트 훅

```lua
-- 플레이어 로그인 시 환영 메시지
register_hook("on_player_login", function(ch)
    local name = get_name(ch)
    send_to_all(name .. "님이 접속했습니다.")
end)

-- 플레이어 사망 시 경험치 페널티
register_hook("on_player_death", function(ch, killer)
    local exp = get_exp(ch)
    set_exp(ch, math.max(0, exp - 1000))
    send_to_char(ch, "경험치 1000을 잃었습니다.")
end)

-- 레벨업 시 축하 메시지
register_hook("on_level_up", function(ch, new_level)
    send_to_room(get_room(ch), get_name(ch) .. "님이 레벨 " .. new_level .. "이 되었습니다!")
end)
```

### 핫 리로드

- `/reload` 인게임 명령어 또는 `POST /api/server/reload` API 호출
- Lua VM의 package.loaded를 초기화하고 스크립트 재로드
- 게임 루프 중단 없이 동작
- 마이그레이션 출력 Lua도 핫 리로드 가능 (동사 매핑 추가 등)

---

## 19. 구현 우선순위 (제안)

### Phase A: 기반 (4주)

```
- Rust workspace + 크레이트 구조 생성
- PostgreSQL 연결 (sqlx) + 21 테이블 로드
- 기본 Telnet 서버 (접속, 로그인, 캐릭터 생성)
- 세션 관리 (mpsc 채널 기반 입출력)
- 게임 루프 프레임워크 (10Hz tick)
```

### Phase B: 핵심 게임플레이 (4주)

```
- 이동 (방, 출구, 방향 명령어)
- look (방 묘사, 캐릭터/아이템 표시)
- inventory, equipment
- 한국어 SOV 명령어 (korean_nlp.lua + korean_commands.lua 연동)
- 영문 명령어 동시 지원
- 기본 전투 (THAC0 명중, 데미지, 사망)
- get/drop/wear/remove
```

### Phase C: 게임 시스템 (4주)

```
- Zone 리셋 (M/O/G/E/P/D/T 명령어)
- 상점 (buy/sell)
- 소셜 (100+ 감정 표현)
- 퀘스트 (기본 추적/완료)
- 도움말 (help 명령어)
- 스킬/스펠 (기본 시전)
```

### Phase D: 고급 기능 (4주)

```
- Lua 트리거 실행 (DG Script 변환본)
- WebSocket 서버
- REST API (axum) + JWT 인증
- 인게임/웹 OLC
- Lua 플러그인 시스템 + 핫 리로드
- MCCP2/GMCP/MSSP 지원
```

---

## 부록 A: 전통 MUD 엔진과의 비교

| 특성 | tbaMUD (전통) | GenOS (현대) |
|------|-------------|-------------|
| 언어 | C | Rust |
| I/O | select() 단일 스레드 | tokio 비동기 |
| 데이터 저장 | 텍스트 파일 | PostgreSQL |
| 스크립팅 | DG Script | Lua 5.4 |
| 접속 방식 | Telnet만 | Telnet + WebSocket + REST |
| 인코딩 | ASCII/EUC-KR | UTF-8 |
| 한국어 입력 | SVO만 (영어식) | SOV + SVO 폴백 |
| 한국어 출력 | 수동 조사 | 자동 조사 선택 |
| 관리 도구 | 인게임 텍스트 | 웹 대시보드 + 인게임 |
| 동시접속 | ~300 (select 한계) | 수천+ (async) |
| 핫 리로드 | 불가 (재컴파일) | Lua 핫 리로드 |

---

## 부록 B: 마이그레이션 데이터 활용 흐름 전체도

```
┌──────────────────────────────────────────────────────────────┐
│                    마이그레이션 도구 (Python)                  │
│                                                               │
│  tbaMUD ─┐                                                    │
│  Simoon ─┼─→ Adapter → UIR (25 dataclasses) → Compiler       │
│  3eyes ──┘                                   │                │
│                                              ▼                │
│                               ┌──────────────────────┐        │
│                               │  sql/schema.sql      │        │
│                               │  sql/seed_data.sql   │        │
│                               │  lua/*.lua (8개)     │        │
│                               └──────────┬───────────┘        │
└──────────────────────────────────────────┼────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    GenOS 엔진 (Rust)                          │
│                                                               │
│  1. psql -f schema.sql  ─→  PostgreSQL 21 테이블 생성         │
│  2. psql -f seed_data.sql ─→ 데이터 INSERT                    │
│  3. 엔진 부트 ─→ 21 테이블 메모리 로드                         │
│  4. Lua VM ─→ 8개 Lua 스크립트 로드                            │
│  5. 게임 서버 가동                                             │
│                                                               │
│  플레이어 접속 → 한국어 SOV 파싱 → 게임플레이                   │
└──────────────────────────────────────────────────────────────┘
```

---

**문서 버전**: 1.0
**최종 업데이트**: 2026-02-10 — 초판 작성
