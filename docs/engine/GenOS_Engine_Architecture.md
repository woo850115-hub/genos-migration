# GenOS Engine Architecture

**Version**: 2.3
**Last Updated**: 2026-02-10
**Author**: 누렁이

---

# Part I: 비전 및 전략

## 1. 프로젝트 비전

GenOS는 4개의 클래식 한국어 MUD를 **각각 95% 재현**하여 개별 게임 서버로 구동한 뒤, 구현 과정에서 발견된 공통 패턴을 **프레임워크로 추출**하고, 최종적으로 **게임 생성 마법사**를 통해 기획자가 시스템을 조합하여 5분 내에 실행 가능한 MUD를 생성할 수 있도록 하는 것이 목표이다.

### 왜 전략을 바꾸는가

v1.0은 "범용 엔진을 먼저 설계하고, 4개 소스를 모두 수용"하는 **탑다운 접근**이었다. 그러나 4개 소스의 데이터 이질성이 극적이다:

| 영역 | tbaMUD | Simoon | 3eyes | 10woongi |
|------|--------|--------|-------|----------|
| 전투 | THAC0 (d20 + AC) | THAC0 (CircleMUD 3.0) | THAC0 (Mordor 변형) | stat-based (sigma 공식) |
| 스탯 | D&D 6종 (STR~CHA) | D&D 6종 | D&D 6종 | 무협 6종 (체력~지력) |
| 장비 슬롯 | 18개 | 18개 | 18개 | 22개 (귀걸이, 허리띠 등) |
| Zone 스폰 | M/O/G/E/P/D/T 커맨드 | M/O/G/E/P/D/T | 바이너리 내장 | setRoomInventory() LPC |
| VNUM | 순차 정수 (0~99999) | 순차 정수 | 순차 정수 | SHA-256 해시 (파일 경로) |
| 스킬 | 54종 (spello) | 79종 (spello 8-arg) | 63종 (C struct) | 51종 (LPC mapping) |
| 클래스 | 4종 | 7종 | 8종 (선택 4/비활성 4 + 환생 4등급) | 14종 |
| 인코딩 | ASCII (영문) | EUC-KR | EUC-KR | EUC-KR |

이 이질성을 범용 추상화로 한꺼번에 해결하면 **어느 게임도 95%를 달성하지 못하는 타협의 산물**이 된다. 따라서 v2.0에서는 **바텀업 접근**으로 전환한다:

1. **개별 게임을 완전하게 구현**한다 → 각 게임의 특수성 100% 보존
2. 4개 구현에서 **자연스럽게 반복되는 패턴을 발견**한다
3. 발견된 패턴만 **프레임워크로 추출**한다 → 쓸모없는 추상화 없음

### 핵심 원칙

1. **마이그레이션 데이터 무수정 소비**: 21개 SQL 테이블 + 8개 Lua 스크립트를 변환 없이 직접 로드
2. **전체 한글화**: 시스템 메시지, 도움말, 소셜, 명령어 — 플레이어가 보는 모든 것을 한글로
3. **한국어 + 영문 이중 명령어**: `고블린 공격` / `attack goblin` 동시 지원
4. **받침 기반 자동 조사**: 출력에서 "전사**가**" / "마법사**가**" 자동 선택
5. **전통 MUD 게임플레이 95% 보존**: 이동, 전투, 상점, 퀘스트, Zone 리셋, 트리거

---

## 2. 3단계 로드맵

```
Phase A: 4개 게임 개별 구현 (각 95% 재현, 전체 한글화)
├── A-1. tbaMUD-KR     ← 첫 번째 구현 대상 (본 문서의 주제)
├── A-2. Simoon-KR     ← tbaMUD-KR 코드 70% 재사용 (CircleMUD 3.0 파생)
├── A-3. 3eyes-KR      ← 바이너리 포맷, Mordor 변형
└── A-4. 10woongi-KR   ← LP-MUD 계열, sigma 전투, 22슬롯

Phase B: 공통 패턴 추출 → GenOS Framework
  (A에서 실제 코드 중복을 분석하여 추출)

Phase C: 게임 생성 마법사
  기획자 → 시스템 선택 UI → 5분 내 실행 가능한 MUD 생성
```

### Phase A 순서 근거

| 순서 | 게임 | 이유 |
|------|------|------|
| A-1 | tbaMUD-KR | 가장 많은 데이터(12,701방 + 1,461트리거), 영문→한글 완전 번역 경험 축적 |
| A-2 | Simoon-KR | CircleMUD 3.0 파생이라 tbaMUD-KR 코드 재사용률 최고 |
| A-3 | 3eyes-KR | THAC0 계열이지만 Mordor 변형 — A-1/A-2와 전투 로직 비교 가능 |
| A-4 | 10woongi-KR | 완전히 다른 시스템 (sigma 전투, 14클래스, 22슬롯) — 프레임워크 추출의 핵심 |

---

## 3. 기술 스택

| 계층 | 기술 | 이유 |
|------|------|------|
| 언어 | **Python 3.12** | 마이그레이션 도구와 동일 언어, 빠른 프로토타이핑, 풍부한 라이브러리 |
| 비동기 런타임 | **asyncio** | 표준 라이브러리, 코루틴 기반 동시성, Telnet/WebSocket 통합 |
| DB | **PostgreSQL 16** | JSONB 컬럼 활용, 마이그레이션 출력 직접 로드 |
| DB 드라이버 | **asyncpg** | asyncio 네이티브 PostgreSQL 드라이버, C 확장 고성능 |
| 웹 프레임워크 | **FastAPI** | 비동기 HTTP/WebSocket, 자동 API 문서, Pydantic 검증 |
| Lua 통합 | **lupa** (선택적) | LuaJIT 바인딩, 트리거/한국어 파서 실행 |
| 직렬화 | **pydantic** + json | 타입 검증, JSONB ↔ Python 객체 변환 |
| 프로토콜 | Telnet (RFC 854) + WebSocket + HTTP | 전통 + 현대 클라이언트 동시 지원 |

### Python 선택 근거 (vs Rust)

v1.0에서 Rust를 선택했으나, **Phase A의 목표는 빠른 구현과 반복**이다:

- **마이그레이션 도구와 동일 언어**: UIR 스키마, 파서 로직 직접 참조/재사용 가능
- **프로토타이핑 속도**: Rust 대비 3~5배 빠른 기능 구현 (컴파일 없음, 동적 타이핑)
- **asyncio 성숙도**: Telnet/WebSocket/HTTP 모두 표준 라이브러리로 통합
- **충분한 성능**: MUD는 I/O 바운드 (수백 동시접속 수준), GIL은 실질적 병목 아님
- **Phase B에서 Rust 전환 가능**: 프레임워크 추출 시 핫패스만 Rust/C 확장으로 교체

### GIL 고려사항

Python의 GIL(Global Interpreter Lock)은 CPU-bound 멀티스레딩을 제한하지만:

- MUD 게임 루프는 **단일 스레드 설계**가 원래부터 자연스러움 (tbaMUD도 select() 단일 스레드)
- 네트워크 I/O는 **asyncio 코루틴**으로 처리 → GIL 영향 없음
- DB 접근은 **asyncpg**의 C 확장이 GIL 해제 상태에서 실행
- 전투 계산은 O(N) 단순 연산 (수백 몬스터 × d20 주사위) → 1ms 미만
- 필요 시 **lupa** (LuaJIT)로 CPU-heavy 로직 오프로드 가능

---

# Part II: tbaMUD-KR 게임서버 설계 (Phase A-1)

## 4. 아키텍처 계층도

```
┌─────────────────────────────────────────────────────────────────┐
│                        클라이언트 계층                            │
│   Telnet (포트 4000)   │  WebSocket + REST API (포트 8080)       │
└───────────┬────────────┴──────────┬───────────────┴──────┬──────┘
            │                       │                       │
┌───────────▼───────────────────────▼───────────────────────▼──────┐
│                      네트워크 계층 (asyncio)                      │
│   TelnetServer  │  FastAPI WebSocket  │  FastAPI REST Router     │
│   ← MCCP2 / GMCP / MSSP 지원 →                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      세션 / 명령어 계층                           │
│   SessionManager → CommandDispatcher                             │
│       │                  │                                       │
│       │           ┌──────┴──────────────┐                        │
│       │           │  위치 기반 명령어 파서 │                        │
│       │           │  [대상] [args] [cmd] │                        │
│       │           └─────────────────────┘                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      게임 로직 계층                               │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│   │ Combat   │  │ Movement │  │  Shop    │  │  Zone Reset   │  │
│   │ Engine   │  │ Engine   │  │  System  │  │  Scheduler    │  │
│   └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│   │ Social   │  │  Quest   │  │  Skill   │  │  Trigger      │  │
│   │ System   │  │  System  │  │  System  │  │  Engine       │  │
│   └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      월드 모델 계층                               │
│   World { rooms, items, monsters, zones, ... }                   │
│   Prototype (VNUM 기반, 불변) → Instance (런타임 ID, 가변)        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      영속성 계층                                  │
│   PostgreSQL 16 (게임별 DB 분리 — 4 databases in 1 instance)     │
│   asyncpg pool  │  인메모리 dict (Redis 불필요)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 부트 시퀀스

```
1. 설정 로드 (config.yaml + GAME 환경변수)
   - GAME=tbamud → config/tbamud.yaml 로드
   - DB 연결 정보, 포트, 게임 설정 경로

2. asyncpg 연결 풀 초기화
   - pool = asyncpg.create_pool(dsn="postgresql://genos:genos@postgres/genos_tbamud")

3. DB 자동 초기화 (최초 실행 시)
   - rooms 테이블 존재 여부 확인
   - 없으면: data/{game}/sql/schema.sql + seed_data.sql 자동 실행
   - 있으면: 스킵 (이미 초기화됨)

4. 월드 데이터 로드 (21 테이블 → 메모리)
   ┌───────────────────────────────────────────────────────┐
   │ 핵심 엔티티                                            │
   │   rooms       → dict[int, RoomProto]      (12,701)    │
   │   items       → dict[int, ItemProto]       (4,765)    │
   │   monsters    → dict[int, MobProto]        (3,705)    │
   │   zones       → list[Zone]                   (189)    │
   │   shops       → dict[int, Shop]              (334)    │
   │   triggers    → dict[int, TriggerDef]      (1,461)    │
   │   quests      → dict[int, Quest]               (1)    │
   │                                                       │
   │ 콘텐츠 테이블                                           │
   │   socials     → dict[str, Social]            (104)    │
   │   help_entries → list[HelpEntry]             (721)    │
   │   commands    → dict[str, CommandDef]        (301)    │
   │   skills      → dict[int, Skill]              (54)    │
   │   races       → list[Race]                     (0)    │
   │   classes     → list[CharacterClass]           (4)    │
   │                                                       │
   │ 시스템 테이블                                           │
   │   game_configs      → dict[str, ConfigValue]  (98)    │
   │   experience_table  → dict[(cls,lv), int]             │
   │   thac0_table       → dict[(cls,lv), int]             │
   │   saving_throws     → dict[(cls,save,lv), int]        │
   │   level_titles      → dict[(cls,lv,gender), str]      │
   │   attribute_modifiers → dict[(stat,score), Mods]      │
   │   practice_params   → dict[int, PracticeParams]       │
   └───────────────────────────────────────────────────────┘

5. 게임 플러그인 로드
   - GAME 환경변수로 games/{game}/game.py 임포트
   - GamePlugin 인터페이스 (register_commands, create_combat, get_messages 등)

6. 명령어 사전 초기화
   - 한국어 명령어 → 핸들러 매핑 dict 로드 (공격→attack, 북→go 등)
   - 한국어 출력 모듈 로드 (has_batchim, render_message)

7. Lua VM 초기화 (lupa, 선택적)
   - triggers.lua 로드 (1,461 트리거, 40,924줄)
   - 엔진 API 함수 등록 (send_to_char, damage 등)

8. Zone 초기 리셋
   - 189개 Zone의 reset_commands 1회 실행
   - M/O/G/E/P/D/T 명령어로 몬스터/아이템 스폰

9. 네트워크 리스너 시작
   - Telnet: 0.0.0.0:4000  (asyncio.start_server)
   - WebSocket: 0.0.0.0:8080  (FastAPI)
   - REST API: 0.0.0.0:8081  (FastAPI)

10. 게임 루프 시작 (asyncio.create_task, 10Hz tick)

11. Zone 리셋 스케줄러 시작
    - 각 Zone의 lifespan에 따라 주기적 리셋
```

---

## 6. 게임 루프 (asyncio 10Hz)

전통 MUD(tbaMUD)의 10Hz tick 기반 게임 루프를 asyncio 단일 코루틴으로 구현한다. 네트워크 I/O는 별도 코루틴에서 비동기 처리하고, 게임 상태 변경은 단일 코루틴에서만 수행하여 동시성 문제를 원천 차단한다.

### Tick 구조 (100ms)

```
┌────────────────────────── 100ms tick ───────────────────────────┐
│                                                                  │
│  1. 입력 수집                                                    │
│     - 각 세션의 명령어 큐에서 dequeue (asyncio.Queue)             │
│     - 접속/접속해제 이벤트 처리                                   │
│                                                                  │
│  2. 명령어 처리                                                  │
│     - 위치 기반 파싱: [대상] [args] [명령어]                     │
│     - 명령어 사전에서 핸들러 조회 (한국어/영문)                  │
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
│     - Lua 트리거 타이머 실행                                     │
│                                                                  │
│  6. 출력 플러시                                                  │
│     - 각 세션의 출력 버퍼를 네트워크 코루틴으로 전송              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 동시성 모델

```
┌─────────────────┐    asyncio.Queue     ┌──────────────────┐
│  Network Coro   │ ──── 입력 큐 ──────▶ │                  │
│  (per session)  │                       │   Game Loop      │
│  - telnet read  │ ◀── 출력 큐 ──────── │   Coro (단일)    │
│  - telnet write │    asyncio.Queue      │                  │
└─────────────────┘                       │  - 명령어 처리    │
                                          │  - 전투 라운드    │
┌─────────────────┐    asyncio.Queue      │  - Zone 리셋     │
│  Network Coro   │ ──── 입력 큐 ──────▶ │  - 환경 업데이트  │
│  (WebSocket)    │                       │                  │
│                 │ ◀── 출력 큐 ──────── │                  │
└─────────────────┘    asyncio.Queue      └────────┬─────────┘
                                                    │
                                          asyncio.  │ create_
                                          Queue     │ task
                                                    ▼
                                          ┌──────────────────┐
                                          │  DB Writer Coro   │
                                          │  - 플레이어 저장   │
                                          │  - 비동기 asyncpg  │
                                          └──────────────────┘
```

- **게임 루프 코루틴**: 단일 asyncio task. 모든 게임 상태 변경이 여기서만 발생 → Lock 불필요
- **네트워크 코루틴**: 세션당 reader/writer 페어. 입력을 읽어 큐에 넣고, 출력 큐에서 꺼내 전송
- **DB writer 코루틴**: 비동기 asyncpg로 플레이어 데이터 저장. 게임 루프 블로킹 없음

### 성능 예상

```
100ms tick 내 처리:
  - 명령어 파싱: ~0.01ms × 50명 = 0.5ms (dict lookup)
  - 전투 라운드: ~0.01ms × 200쌍 = 2ms (d20 연산)
  - Zone 리셋: ~1ms (최대 1개 Zone/tick)
  - 출력 조립: ~0.1ms × 50명 = 5ms
  - 여유: ~87ms (87% idle)

→ 수백 동시접속에서 안정적 10Hz 유지 가능
```

---

## 7. 네트워크 계층

### 7.1 Telnet (전통 MUD 클라이언트)

```python
class TelnetServer:
    """asyncio 기반 Telnet 서버"""

    async def start(self, host: str, port: int):
        server = await asyncio.start_server(
            self._handle_client, host, port
        )
        # ...

    async def _handle_client(self, reader, writer):
        session = self.session_manager.create_session(reader, writer)
        try:
            await session.run()  # 로그인 → 게임 루프 입력
        finally:
            self.session_manager.remove_session(session.id)
```

- **RFC 854** 기본 Telnet 프로토콜
- **MCCP2** (Mud Client Compression Protocol v2): zlib 압축으로 대역폭 절약
- **GMCP** (Generic MUD Communication Protocol): 구조화된 JSON 데이터 (HP바, 미니맵 등)
- **MSSP** (MUD Server Status Protocol): MUD 목록 사이트에 서버 정보 노출
- **인코딩**: UTF-8 기본. 첫 입력에서 invalid UTF-8 바이트 감지 시 EUC-KR로 자동 전환 (세션 단위 상태 유지)
- **ANSI 색상**: 16색 + 256색 + 트루컬러(24-bit RGB) 지원 — GenOS 공통 포맷 (섹션 17.4 참조)
- **Rate limiting**: 세션당 초당 10 명령어 제한. 초과 시 무시 + 경고 메시지. 서버 전체 DoS 방지

### 7.2 WebSocket (현대 웹 클라이언트)

```python
# FastAPI WebSocket 엔드포인트
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session = session_manager.create_ws_session(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # {"type": "command", "data": {"input": "고블린 공격"}}
            await session.input_queue.put(data["data"]["input"])
    except WebSocketDisconnect:
        session_manager.remove_session(session.id)
```

- **JSON 메시지 프로토콜**:
  ```json
  // 서버 → 클라이언트
  {"type": "room", "data": {"vnum": 3001, "name": "마을 광장", "exits": ["north", "south"]}}
  {"type": "combat", "data": {"attacker": "전사", "target": "고블린", "damage": 15}}
  {"type": "text", "data": {"message": "고블린이 쓰러졌습니다!", "color": "green"}}

  // 클라이언트 → 서버
  {"type": "command", "data": {"input": "고블린 공격"}}
  ```

### 7.3 REST API (관리/OLC) — 동일 FastAPI 인스턴스

WebSocket과 REST API는 **동일한 FastAPI 인스턴스 (포트 8080)**에서 경로로 분리된다:
- WebSocket: `ws://host:8080/ws`
- REST API: `http://host:8080/api/*`
- API 문서: `http://host:8080/docs` (Swagger UI)

- **JWT 인증**: 관리자 토큰 기반
- **엔드포인트**:
  - `GET /api/server/status` — 서버 상태 (접속자, 업타임, 틱 지연, 메모리)
  - `GET/PUT/POST /api/rooms/:vnum` — 방 CRUD (OLC)
  - `GET/PUT/POST /api/items/:vnum` — 아이템 CRUD
  - `GET/PUT/POST /api/monsters/:vnum` — 몬스터 CRUD
  - `POST /api/server/reload` — 게임 모듈 핫 리로드 (games/ 전체)
  - `POST /api/server/reload/:module` — 특정 모듈 리로드 (combat, commands 등)
  - `POST /api/server/shutdown` — 서버 종료 (graceful)

---

## 8. 명령어 시스템 (위치 기반 파서)

명령어 처리는 **위치 기반 파싱 + Python 핸들러 실행** 구조이다. 자연어 처리(NLP) 없이, 토큰 위치만으로 명령어와 인자를 구분한다.

### 명령어 문법

```
(옵션: [대상]) (옵션: [args...]) [명령어]
```

마지막 토큰이 명령어, 앞의 토큰들이 위치 인자이다. 영문 SVO(`[cmd] [대상] [args]`)도 자동 폴백으로 지원한다.

### 입력 예시

```
"공격"                → cmd=공격, args=[]
"고블린 공격"         → cmd=공격, args=["고블린"]
"고블린 불기둥 공격"  → cmd=공격, args=["고블린", "불기둥"]
"북"                  → cmd=북 (방향 매핑)
"attack goblin"       → cmd=attack, args=["goblin"]  (SVO 폴백)
```

### 처리 흐름

```
입력: "고블린 공격"
  │
  ▼
┌───────────────────────────────────────────┐
│ 1. CommandParser.parse(input)              │
│                                            │
│    tokens = ["고블린", "공격"]              │
│                                            │
│    1차: 마지막 토큰 "공격" → CMD["공격"]?  │
│          → 있음! handler = "attack"        │
│          → args = ["고블린"]               │
│                                            │
│    (실패 시) 2차: 첫 토큰으로 SVO 시도     │
│                                            │
│    결과: ParseResult(                      │
│             handler="attack",              │
│             args=["고블린"])               │
└────────────────────┬──────────────────────┘
                     ▼
┌───────────────────────────────────────────┐
│ 2. CommandDispatcher                       │
│    handler_map["attack"]                   │
│    → combat_engine.do_attack(ch, args)     │
└────────────────────┬──────────────────────┘
                     ▼
┌───────────────────────────────────────────┐
│ 3. Target Resolution (핸들러 내부)          │
│    args[0] = "고블린"                      │
│    → Room에서 keyword 부분 매칭            │
└───────────────────────────────────────────┘
```

### 파서 구현

```python
@dataclass
class ParseResult:
    handler: str       # 매핑된 영문 핸들러명
    args: list[str]    # 위치 인자 (대상, 추가 args)

# 명령어 사전 — 한국어 + 영문 모두 같은 dict에 등록
CMD: dict[str, str] = {
    # 이동
    "북": "go_north", "남": "go_south", "동": "go_east", "서": "go_west",
    "위": "go_up", "아래": "go_down",
    "north": "go_north", "south": "go_south", "east": "go_east", "west": "go_west",
    "up": "go_up", "down": "go_down",
    # 전투
    "공격": "attack", "attack": "attack",
    "도망": "flee", "flee": "flee",
    "시전": "cast", "cast": "cast",
    # 아이템
    "집어": "get", "get": "get",
    "버려": "drop", "drop": "drop",
    "입어": "wear", "wear": "wear",
    "벗어": "remove", "remove": "remove",
    # 정보
    "봐": "look", "look": "look",
    "소지품": "inventory", "inventory": "inventory",
    "능력": "score", "score": "score",
    # 상점
    "사": "buy", "buy": "buy",
    "팔아": "sell", "sell": "sell",
    # 소통
    "말": "say", "say": "say",
    "외쳐": "shout", "shout": "shout",
    # 시스템
    "도움": "help", "help": "help",
    "접속자": "who", "who": "who",
    "종료": "quit", "quit": "quit",
    # 초성 약칭 (한국어)
    "ㅂ": "go_north", "ㄷ": "go_east", "ㄴ": "go_south", "ㅅ": "go_west",
    "ㄱ": "attack", "ㅎ": "help",
    # 영문 약칭 (1글자)
    "n": "go_north", "e": "go_east", "s": "go_south", "w": "go_west",
    "u": "go_up", "d": "go_down", "l": "look", "i": "inventory",
    # ... 301개 명령어 + 약칭
}

def parse(input_text: str) -> ParseResult | None:
    tokens = input_text.strip().split()
    if not tokens:
        return None

    # 1차: 마지막 토큰을 명령어로 시도 (한국어 어순)
    handler = CMD.get(tokens[-1])
    if handler:
        return ParseResult(handler=handler, args=tokens[:-1])

    # 2차: 첫 토큰을 명령어로 시도 (영문 SVO 폴백)
    handler = CMD.get(tokens[0])
    if handler:
        return ParseResult(handler=handler, args=tokens[1:])

    # 3차: prefix 매칭 (한국어/영문 약칭 — "도" → "도움말", "att" → "attack")
    for token_idx in (-1, 0):
        token = tokens[token_idx]
        matches = [k for k in CMD if k.startswith(token) and len(k) > len(token)]
        if len(matches) == 1:
            handler = CMD[matches[0]]
            args = tokens[:-1] if token_idx == -1 else tokens[1:]
            return ParseResult(handler=handler, args=args)

    return None
```

### 301개 명령어 매핑

tbaMUD의 301개 명령어를 한국어 매핑한다:

| 범주 | 영문 | 한국어 | 수량 |
|------|------|--------|------|
| 이동 | north, south, ... | 북, 남, ... | 10 |
| 전투 | attack, kill, flee | 공격, 죽여, 도망 | 8 |
| 아이템 | get, drop, wear, remove | 집어, 버려, 입어, 벗어 | 12 |
| 상점 | buy, sell, list | 사, 팔아, 목록 | 5 |
| 정보 | look, inventory, score | 봐, 소지품, 능력 | 15 |
| 소셜 | smile, laugh, ... | 미소, 웃어, ... | 104 |
| 소통 | say, tell, shout | 말, 귓속말, 외쳐 | 8 |
| 스킬 | cast, practice | 시전, 연습 | 5 |
| 시스템 | who, help, quit | 접속자, 도움, 종료 | 20+ |
| 기타 | 관리자, 퀘스트, 설정 등 | — | 100+ |

### 설계 원칙

- **NLP 없음**: 조사 스트리핑, 어간 추출, 의미역 분석 불필요. 유저가 명확한 단어를 입력
- **마지막 토큰 우선**: 한국어 어순 (`고블린 공격`)에서 마지막이 동사
- **SVO 폴백**: 영문 어순 (`attack goblin`)에서 첫 토큰이 동사
- **prefix 매칭**: 정확 매칭 실패 시 약칭으로 시도 (`도` → `도움말`, `att` → `attack`). 결과가 1개일 때만 매칭
- **초성 약칭**: 방향/핵심 명령어에 ㄱ~ㅎ 단일 초성 등록 (`ㅂ`=북, `ㄷ`=동, `ㄱ`=공격)
- **인자 해석은 핸들러 책임**: 파서는 토큰만 분리, 대상 해석(keyword 매칭)은 각 핸들러가 수행

### Alias (줄임말) 시스템

플레이어가 여러 명령어를 하나의 줄임말로 등록하고 일괄 실행하는 기능이다. **명령어 파서 앞단**에서 처리한다.

```
등록: "줄임말 순찰 동;동;서;남"   → aliases["순찰"] = ["동","동","서","남"]
사용: "순찰" → 입력 큐에 4개 push → tick당 1개씩 처리
```

- 플레이어별 저장: `players` 테이블 `aliases JSONB DEFAULT '{}'`
- **재귀 방지**: alias 확장 결과는 다시 alias 확장하지 않음
- **큐 제한**: 확장 후 최대 20개 명령어 (무한 큐 방지)

```python
def expand_alias(session, input_text: str) -> list[str]:
    """alias 확장 — 파서 앞단에서 호출"""
    if input_text in session.character.aliases:
        commands = session.character.aliases[input_text][:20]
        return commands
    return [input_text]
```

---

## 9. 월드 모델 (Prototype/Instance 패턴)

VNUM 기반 Prototype과 런타임 Instance를 분리하는 전통적 MUD 데이터 모델을 채택한다.

### Prototype (불변, DB에서 로드)

```python
@dataclass(frozen=True)
class RoomProto:
    """방 프로토타입 — rooms 테이블에서 로드"""
    vnum: int
    name: str
    description: str
    zone_number: int
    sector_type: int
    room_flags: list[int]       # JSONB에서 파싱
    exits: list[ExitProto]      # JSONB에서 파싱
    extra_descs: list[ExtraDesc]
    trigger_vnums: list[int]

@dataclass(frozen=True)
class ItemProto:
    """아이템 프로토타입 — items 테이블에서 로드"""
    vnum: int
    keywords: str
    short_description: str
    long_description: str
    item_type: int
    extra_flags: list[int]
    wear_flags: list[int]
    values: list[int]           # [v0, v1, v2, v3]
    weight: int
    cost: int
    affects: list[ItemAffect]
    trigger_vnums: list[int]

@dataclass(frozen=True)
class MobProto:
    """몬스터 프로토타입 — monsters 테이블에서 로드"""
    vnum: int
    keywords: str
    short_description: str
    long_description: str
    detailed_description: str
    level: int
    hitroll: int
    armor_class: int
    hp_dice: DiceRoll           # "3d8+30" → DiceRoll(num=3, size=8, bonus=30)
    damage_dice: DiceRoll
    gold: int
    experience: int
    action_flags: list[int]
    affect_flags: list[int]
    trigger_vnums: list[int]
```

### Instance (가변, 런타임 생성)

```python
@dataclass
class RoomInstance:
    """방 인스턴스 — 런타임 상태"""
    proto: RoomProto
    characters: list[int]              # 방에 있는 캐릭터 ID
    ground_items: list['ItemInstance']  # 바닥에 있는 아이템
    door_states: dict[int, DoorState]  # 방향 → 문 상태

@dataclass
class ItemInstance:
    """아이템 인스턴스 — Zone 리셋 또는 드랍으로 생성"""
    id: int                    # monotonic 카운터
    proto: ItemProto
    # 인스턴스 고유 상태 (향후 확장)

@dataclass
class CharInstance:
    """캐릭터 인스턴스 — PC(플레이어) 또는 NPC(몬스터)"""
    id: int
    proto: MobProto | None     # NPC면 MobProto, PC면 None
    name: str                  # PC: 플레이어 이름, NPC: proto.short_description
    room: int                  # 현재 방 VNUM
    # 스탯
    level: int
    hp: int
    max_hp: int
    mana: int
    max_mana: int
    move_points: int
    max_move: int
    # 전투
    hitroll: int
    armor_class: int
    fighting: int | None       # 교전 중인 상대 ID
    # 장비/인벤토리
    inventory: list[ItemInstance]
    equipment: list[ItemInstance | None]  # 18슬롯 (NUM_WEARS = 18)
    # PC 전용
    class_id: int
    race_id: int
    gold: int
    experience: int
    # 기타
    affects: list[Affect]
    position: Position         # Standing, Sitting, Sleeping, Fighting, ...
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

## 10. 전투 엔진 (THAC0 기반)

마이그레이션 출력의 전투 데이터를 소비하여 THAC0 기반 전투를 구현한다.

### 소비하는 마이그레이션 데이터

| 출력 | 용도 | 데이터량 |
|------|------|----------|
| `thac0_table` SQL | 클래스별/레벨별 THAC0 값 | 4 클래스 × 50 레벨 |
| `saving_throws` SQL | 클래스별/세이브타입별/레벨별 세이빙 값 | 5 유형 × 4 클래스 × 50 레벨 |
| `attribute_modifiers` SQL | 능력치별 보정 (str→tohit/todam, dex→ac) | 6 스탯 × 25 스코어 |
| `combat.lua` | ATTACK_TYPES 15종, calculate_hit(), roll_damage() | 59줄 |
| `stat_tables.lua` | THAC0/세이빙스로우/스탯 보정 통합 | 215줄 |

### 전투 흐름

```
1. 전투 개시
   - 플레이어가 "공격해" 명령 입력 또는 aggro 몬스터가 공격
   - attacker.fighting = target.id, target.fighting = attacker.id
   - 양측 position = Fighting

2. 전투 라운드 (매 2초 = 20 tick)
   a. THAC0 조회
      thac0 = thac0_table[(attacker.class_id, attacker.level)]

   b. 명중 판정
      roll = random.randint(1, 20)
      needed = thac0 - target.armor_class - attacker.hitroll
      hit = (roll >= needed)

   c. 데미지 계산 (명중 시)
      damage = roll_dice(attacker.damage_dice) + str_bonus

   d. 세이빙 스로우 (스펠 데미지 시)
      save = saving_throws[(target.class_id, save_type, target.level)]
      roll = random.randint(1, 20)
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

### 15종 공격 타입 (combat.lua)

```python
ATTACK_TYPES = {
    0: "hit",  1: "sting",  2: "whip",   3: "slash",  4: "bite",
    5: "bludgeon", 6: "crush", 7: "pound", 8: "claw",  9: "maul",
    10: "thrash", 11: "pierce", 12: "blast", 13: "punch", 14: "stab",
}
```

### 54종 스킬/스펠

마이그레이션의 `skills` 테이블에서 로드. 주요 스펠:

| 카테고리 | 예시 | 수량 |
|----------|------|------|
| 공격 스펠 | magic missile, fireball, lightning bolt | ~15종 |
| 힐링 | cure light, heal, sanctuary | ~8종 |
| 버프/디버프 | bless, curse, poison, blind | ~12종 |
| 유틸리티 | detect invis, fly, teleport | ~10종 |
| 전투 스킬 | kick, bash, rescue | ~8종 |
| 기타 | identify, enchant weapon | ~12종 |

### 5종 세이빙 스로우

```python
SAVE_TYPES = {
    0: "paralyzation",    # 마비
    1: "rod",             # 마법봉
    2: "petrification",   # 석화
    3: "breath",          # 브레스
    4: "spell",           # 스펠
}
```

---

## 11. Zone/스폰 시스템

마이그레이션 출력의 `zones` 테이블에서 `reset_commands` JSONB를 로드하여 실행한다.

### tbaMUD 데이터 규모

- **189개 Zone**: 각각 lifespan(분)과 reset_mode를 가짐
- **334개 Shop**: keeper_vnum으로 NPC와 연결

### 리셋 명령어 유형 (7종)

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

```python
class ResetMode(IntEnum):
    NEVER  = 0  # 리셋 안 함
    EMPTY  = 1  # 방에 플레이어 없을 때만
    ALWAYS = 2  # 항상 리셋
```

### 리셋 스케줄링

```python
async def zone_reset_scheduler(world: World):
    """Zone 리셋 스케줄러 — 게임 루프에서 매 tick 호출"""
    for zone in world.zones:
        zone.timer -= 1
        if zone.timer <= 0:
            zone.timer = zone.lifespan * 60 * 10  # 분→tick 변환

            if zone.reset_mode == ResetMode.NEVER:
                continue
            if zone.reset_mode == ResetMode.EMPTY:
                if any_players_in_zone(world, zone):
                    continue

            execute_reset_commands(world, zone)

def execute_reset_commands(world: World, zone: Zone):
    """M/O/G/E/P/D/T 리셋 명령어 순서대로 실행"""
    last_mob: CharInstance | None = None
    last_cmd_success = True

    for cmd in zone.reset_commands:
        if cmd.if_flag and not last_cmd_success:
            last_cmd_success = False
            continue

        match cmd.command:
            case "M":
                mob = spawn_mob(world, cmd.arg1, cmd.arg3, cmd.arg2)
                last_mob = mob
                last_cmd_success = mob is not None
            case "O":
                last_cmd_success = load_obj_to_room(world, cmd.arg1, cmd.arg3, cmd.arg2)
            case "G":
                if last_mob:
                    last_cmd_success = give_obj_to_mob(world, cmd.arg1, last_mob, cmd.arg2)
            case "E":
                if last_mob:
                    last_cmd_success = equip_obj_on_mob(world, cmd.arg1, last_mob, cmd.arg3, cmd.arg2)
            case "P":
                last_cmd_success = put_obj_in_container(world, cmd.arg1, cmd.arg3, cmd.arg2)
            case "D":
                set_door_state(world, cmd.arg1, cmd.arg2, cmd.arg3)
                last_cmd_success = True
            case "T":
                attach_trigger(world, cmd.arg1, cmd.arg2, cmd.arg3)
                last_cmd_success = True
```

---

## 12. DG Script 트리거 실행

### 트리거 규모

tbaMUD에서 1,461개의 DG Script 트리거가 Lua로 변환되어 `triggers.lua` (40,924줄)에 저장된다. 이는 엔진에서 가장 큰 스크립팅 자산이다.

### 실행 방법: lupa (LuaJIT) 또는 Python 변환

두 가지 접근이 가능하며, Phase A-1에서는 **lupa 기반 실행을 우선** 시도한다:

**옵션 1: lupa (LuaJIT 바인딩) — 우선**

```python
import lupa

lua = lupa.LuaRuntime(unpack_returned_tuples=True)

# 엔진 API 등록 (Python → Lua)
lua.globals()["send_to_char"] = engine.send_to_char
lua.globals()["send_to_room"] = engine.send_to_room
lua.globals()["damage"] = engine.damage
lua.globals()["get_level"] = engine.get_level
lua.globals()["move_char"] = engine.move_char
lua.globals()["load_mob"] = engine.load_mob
lua.globals()["load_obj"] = engine.load_obj
lua.globals()["purge"] = engine.purge
# ... 30+ DG Script 호환 API 함수

# triggers.lua 로드
lua.execute(open("lua/triggers.lua").read())

# 트리거 실행
def fire_trigger(trigger_vnum: int, self_id: int, actor_id: int, arg: str) -> bool:
    trigger_func = lua.globals()[f"trigger_{trigger_vnum}"]
    if trigger_func:
        return trigger_func(self_id, actor_id, arg)
    return True
```

**옵션 2: Python 변환 (lupa 없이)**

triggers.lua를 Python 코드로 변환하거나, 간이 인터프리터 작성. lupa 의존성 없는 경량 실행.

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

### DG Script → Lua 변환 패턴

마이그레이션 도구가 수행하는 변환:

| DG Script | Lua |
|-----------|-----|
| `* comment` | `-- comment` |
| `if/elseif/else/end` | `if/elseif/else/end` |
| `wait 5 sec` | `coroutine.yield(5)` |
| `say Hello!` | `self:say("Hello!")` |
| `emote grins` | `self:emote("grins")` |
| `%actor.name%` | `actor_name` (변수 치환) |
| `&&`, `\|\|`, `!=` | `and`, `or`, `~=` |
| `%send% %actor% msg` | `send_to_char(actor, "msg")` |
| `%load% mob 1234` | `load_mob(1234, self_room)` |
| `%load% obj 5678` | `load_obj(5678, self_room)` |
| `%purge% %self%` | `purge(self_id)` |
| `%teleport% %actor% 3001` | `move_char(actor, 3001)` |
| `%force% %actor% cmd` | `force_command(actor, "cmd")` |
| `%door% room dir flags` | `set_door(room, dir, flags)` |
| `%transform% 1234` | `transform_mob(self_id, 1234)` |

---

## 13. 한글화 전략

tbaMUD-KR의 한글화 범위를 정의한다. 목표는 플레이어가 **한글만으로** 게임을 플레이할 수 있는 것이다.

### 한글화 대상

| 대상 | 수량 | 한글화 방법 | Phase A-1 범위 |
|------|------|------------|---------------|
| 시스템 메시지 | ~200종 | 메시지 테이블 (i18n key → 한글 문자열) | 전체 |
| 도움말 | 721개 | DB help_entries 한글 번역 | 주요 50개 |
| 소셜 | 104개 | socials 테이블에 한글 메시지 추가 | 전체 |
| 명령어 | 301개 | CMD dict 매핑 (한국어 키워드 → 핸들러) | 전체 |
| 스킬/스펠 | 54개 | extensions["korean_name"] 필드 | 전체 |
| 클래스 | 4개 | 마법사/성직자/도적/전사 | 전체 |
| 방향 | 10개 | 이미 매핑 완료 (북/동/남/서/위/아래 등) | 완료 |
| 방/아이템/몬스터 이름 | 21,171개 | 영문 유지, 점진적 번역 | 영문 유지 |
| 출력 조사 | 6종 | Python 받침 검사 자동 선택 | 전체 |

### 시스템 메시지 테이블 (i18n)

```python
# messages.py — 한국어 시스템 메시지
MSG = {
    # 이동
    "cant_go":     "그쪽으로는 갈 수 없습니다.",
    "enter_room":  "{name}{이/가} 들어옵니다.",
    "leave_room":  "{name}{이/가} {dir}쪽으로 떠납니다.",

    # 전투
    "you_hit":     "당신이 {target}{을/를} {attack_type}으로 공격하여 {damage} 피해를 줍니다.",
    "you_miss":    "당신이 {target}{을/를} 공격하지만 빗나갑니다.",
    "mob_dies":    "{name}{이/가} 쓰러집니다!",
    "you_die":     "당신은 죽었습니다... 안식을 위해 기도합니다.",
    "gain_exp":    "경험치 {amount}을(를) 획득했습니다.",

    # 상점
    "buy_item":    "{item}{을/를} {cost}골드에 구매했습니다.",
    "cant_afford": "골드가 부족합니다.",
    "shop_closed": "지금은 영업시간이 아닙니다.",

    # 시스템
    "welcome":     "GenOS MUD에 오신 것을 환영합니다!",
    "goodbye":     "안녕히 가세요. 다음에 또 만나요!",
    "level_up":    "축하합니다! 레벨 {level}{이/가} 되었습니다!",
    # ... ~200종
}
```

### 조사 자동 선택 (출력 렌더링)

출력 시 `{name}{이/가}` 템플릿에서 받침 여부에 따라 조사를 자동 선택한다. 상세 구현은 **섹션 14** 참조.

예시: `"{name}{이/가} {target}{을/를} 공격합니다."` + name="다람쥐", target="고블린" → `"다람쥐가 고블린을 공격합니다."`

---

## 14. 한국어 출력 모듈 (받침 기반 조사)

입력 파싱은 섹션 8의 위치 기반 파서가 담당하며 NLP가 불필요하다. 이 섹션에서는 **출력 시 한국어 조사를 자동 선택**하는 모듈만 다룬다.

### 핵심 함수 (2개)

```python
def has_batchim(s: str) -> bool:
    """마지막 한글 글자에 받침(종성)이 있는지 검사 — Unicode 수학"""
    for ch in reversed(s):
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7A3:
            return (code - 0xAC00) % 28 != 0
    return False

def render_message(template: str, **kwargs: str) -> str:
    """메시지 템플릿 렌더링 — 변수 치환 + 받침 기반 조사 선택"""
    # 1. 변수 치환: {name} → "전사"
    # 2. 조사 선택: {이/가} → 직전 명사 받침에 따라 "이" 또는 "가"
    ...
```

### 지원 조사 (6종)

| 조사 쌍 | 받침 있음 | 받침 없음 | 예시 |
|----------|-----------|-----------|------|
| `{이/가}` | 이 | 가 | 전사**가**, 고블린**이** |
| `{을/를}` | 을 | 를 | 고블린**을**, 드래곤**을** |
| `{은/는}` | 은 | 는 | 전사**는**, 기사**는** |
| `{과/와}` | 과 | 와 | 전사**와**, 기사**와** |
| `{으로/로}` | 으로 | 로 | 검**으로**, 창**으로** |
| `{이다/다}` | 이다 | 다 | 전사**이다**, 기사**다** |

---

## 15. PostgreSQL 영속성

### DB 분리 전략

4개 게임 서버가 **1개 PostgreSQL 인스턴스** 안의 **4개 별도 데이터베이스**를 사용한다. 스키마 분리(schema separation)가 아닌 DB 분리(database separation)를 선택한 이유:

- 마이그레이션 출력(schema.sql, seed_data.sql)이 `CREATE TABLE rooms ...` 형태로 스키마 접두사 없이 생성됨 → DB 분리면 SQL 무수정 로드 가능
- `pg_dump`/`pg_restore`로 게임 단위 독립 백업/복원
- 게임 간 데이터 격리 완전 보장

```
PostgreSQL 16 (1 instance, 1 container)
├── genos_tbamud    ← tbaMUD-KR 서버 전용
├── genos_simoon    ← Simoon-KR 서버 전용
├── genos_3eyes     ← 3eyes-KR 서버 전용
└── genos_10woongi  ← 10woongi-KR 서버 전용
```

### DB 자동 초기화

서버 부트 시 DB가 비어있으면 자동으로 마이그레이션 데이터를 로드한다. 별도 init 컨테이너나 프로파일 없이 **부팅 시 자동 확인**:

```python
async def ensure_initialized(pool: asyncpg.Pool, game_name: str):
    """DB가 비어있으면 마이그레이션 SQL을 자동 실행"""
    exists = await pool.fetchval(
        "SELECT EXISTS(SELECT FROM information_schema.tables "
        "WHERE table_name='rooms')"
    )
    if not exists:
        logger.info(f"[{game_name}] DB 초기화 시작...")
        schema = Path(f"data/{game_name}/sql/schema.sql").read_text()
        seed = Path(f"data/{game_name}/sql/seed_data.sql").read_text()
        async with pool.acquire() as conn:
            await conn.execute(schema)
            await conn.execute(seed)
        logger.info(f"[{game_name}] DB 초기화 완료")
    else:
        logger.info(f"[{game_name}] DB 이미 초기화됨, 스킵")
```

### Redis 불필요 판단

MUD의 DB 접근 패턴은 **부팅 시 전체 로드 → 런타임에는 인메모리** 구조이다:

- **부팅**: 21 테이블 전체 SELECT → Python dict/list에 적재 (~2초)
- **런타임**: 100% 인메모리 dict 조회 (게임 루프 내 DB 접근 없음)
- **저장**: 5분 주기 플레이어 자동 저장 + 로그아웃 시 즉시 저장 (소량, 비동기)

따라서 세션 캐시용 Redis는 불필요하다. `dict`가 곧 캐시이다.

### 부트 시 로드 (마이그레이션 데이터, 읽기 전용)

```python
async def load_world(pool: asyncpg.Pool) -> World:
    """21개 마이그레이션 테이블을 전체 SELECT하여 메모리에 로드"""
    async with pool.acquire() as conn:
        # 핵심 엔티티
        rooms = {r["vnum"]: RoomProto(**r) for r in await conn.fetch("SELECT * FROM rooms")}
        items = {r["vnum"]: ItemProto(**r) for r in await conn.fetch("SELECT * FROM items")}
        monsters = {r["vnum"]: MobProto(**r) for r in await conn.fetch("SELECT * FROM monsters")}
        classes = [CharacterClass(**r) for r in await conn.fetch("SELECT * FROM classes")]
        zones = [Zone(**r) for r in await conn.fetch("SELECT * FROM zones")]
        shops = {r["keeper_vnum"]: Shop(**r) for r in await conn.fetch("SELECT * FROM shops")}
        triggers = {r["vnum"]: TriggerDef(**r) for r in await conn.fetch("SELECT * FROM triggers")}
        quests = {r["vnum"]: Quest(**r) for r in await conn.fetch("SELECT * FROM quests")}

        # 콘텐츠 테이블
        socials = {r["command"]: Social(**r) for r in await conn.fetch("SELECT * FROM socials")}
        help_entries = [HelpEntry(**r) for r in await conn.fetch("SELECT * FROM help_entries")]
        commands = {r["command"]: CommandDef(**r) for r in await conn.fetch("SELECT * FROM commands")]
        skills = {r["id"]: Skill(**r) for r in await conn.fetch("SELECT * FROM skills")}
        races = [Race(**r) for r in await conn.fetch("SELECT * FROM races")]

        # 시스템 테이블
        game_configs = {r["key"]: r["value"] for r in await conn.fetch("SELECT * FROM game_configs")}
        exp_table = {(r["class_id"], r["level"]): r["experience"]
                     for r in await conn.fetch("SELECT * FROM experience_table")}
        thac0_table = {(r["class_id"], r["level"]): r["thac0"]
                       for r in await conn.fetch("SELECT * FROM thac0_table")}
        saving_throws = {(r["class_id"], r["save_type"], r["level"]): r["save_value"]
                         for r in await conn.fetch("SELECT * FROM saving_throws")}
        # ...

    return World(rooms=rooms, items=items, monsters=monsters, ...)
```

### 런타임 저장 (플레이어 데이터)

마이그레이션 범위 밖이지만 엔진에 필수인 테이블:

```sql
CREATE TABLE players (
    id              SERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    class_id        INTEGER REFERENCES classes(id),
    race_id         INTEGER,
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
    aliases         JSONB DEFAULT '{}',     -- {"순찰": ["동","동","서","남"], ...}
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_login      TIMESTAMPTZ
);

CREATE INDEX idx_players_name ON players(name);
```

### 저장 전략

- **비동기 저장**: `asyncio.create_task`로 DB 쓰기 위임
- **자동 저장**: 5분마다 온라인 플레이어 전원 저장
- **로그아웃 저장**: 정상/비정상 접속 해제 시 즉시 저장
- **배치 처리**: 여러 플레이어 업데이트를 하나의 트랜잭션으로 묶음

```python
async def auto_save(pool: asyncpg.Pool, sessions: dict[int, Session]):
    """5분마다 온라인 플레이어 전원 저장"""
    while True:
        await asyncio.sleep(300)  # 5분
        async with pool.acquire() as conn:
            async with conn.transaction():
                for session in sessions.values():
                    if session.character:
                        await save_player(conn, session.character)
```

---

## 16. 관리자 시스템 (FastAPI)

### REST API 웹 대시보드

```python
from fastapi import FastAPI, HTTPException, Depends

app = FastAPI(title="GenOS tbaMUD-KR 관리 API")

@app.get("/api/server/status")
async def server_status():
    return {
        "name": "GenOS tbaMUD-KR",
        "uptime": get_uptime(),
        "players_online": len(session_manager.sessions),
        "rooms_loaded": len(world.rooms),
        "mobs_alive": count_alive_mobs(world),
        "zones": len(world.zones),
    }

@app.get("/api/rooms/{vnum}")
async def get_room(vnum: int):
    room = world.rooms.get(vnum)
    if not room:
        raise HTTPException(404, "Room not found")
    return room_to_dict(room)

@app.put("/api/rooms/{vnum}")
async def update_room(vnum: int, data: RoomUpdate, pool=Depends(get_pool)):
    """방 수정 → DB 업데이트 + Prototype 핫 리로드"""
    from dataclasses import replace
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE rooms SET name=$1, description=$2 WHERE vnum=$3",
            data.name, data.description, vnum
        )
    world.rooms[vnum] = replace(world.rooms[vnum], **data.dict())
    return {"status": "ok"}

@app.post("/api/server/reload")
async def reload_scripts():
    """Lua 스크립트 핫 리로드"""
    trigger_engine.reload()
    return {"status": "reloaded"}

@app.post("/api/server/shutdown")
async def shutdown(countdown: int = 30):
    """서버 종료 (카운트다운)"""
    asyncio.create_task(graceful_shutdown(countdown))
    return {"status": f"shutting down in {countdown}s"}
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

### 상점 / 소셜 / 도움말 / 퀘스트

**상점 시스템** (334개 shops 테이블):
```
플레이어: "검을 사" (또는 "buy sword")
  → 현재 방의 keeper_vnum과 일치하는 NPC 확인
  → shop.open1~close2로 영업시간 확인
  → 키워드로 selling_items에서 아이템 검색
  → 가격 = item.cost × shop.profit_buy
  → 골드 확인 → ItemInstance 생성 → 인벤토리 추가
```

**소셜 시스템** (104개 socials 테이블):
```
플레이어: "미소" (또는 "smile")
  → socials 테이블에서 command 매칭
  → 타겟 유무에 따라 메시지 선택 (6종)
  → 메시지 템플릿 치환: $n → 행위자, $N → 대상
  → 한글 조사 자동 선택
```

**도움말 시스템** (721개 help_entries 테이블):
```
플레이어: "도움 전투" (또는 "help combat")
  → help_entries.keywords JSONB에서 키워드 검색
  → 한국어/영문 동시 매칭
  → min_level 필터링
  → text 필드 출력 (ANSI 색상 지원)
```

**퀘스트 시스템** (quests 테이블):
```
플레이어: 퀘스트 NPC와 대화
  → quests.mob_vnum으로 퀘스트 검색
  → prev_quest 확인, min/max_level 확인
  → quest_type에 따라 목표 추적 (kill/collect/explore)
  → 완료 시: reward_gold, reward_exp, reward_obj 지급
```

### Graceful Shutdown (안전 종료)

SIGTERM/SIGINT 수신 또는 관리자 `"서버 종료"` / `POST /api/server/shutdown` 호출 시:

```
1. 전체 공지: "서버가 {N}초 후 종료됩니다" (기본 30초)
2. 신규 접속 거부 (Telnet/WebSocket 리스너 close)
3. 카운트다운 완료 → 온라인 플레이어 전원 DB 저장
4. 전 세션에 종료 메시지 전송 + 연결 해제
5. asyncpg 풀 close
6. 프로세스 종료 (exit code 0)
```

### 에러 처리 정책

| 계층 | 정책 |
|------|------|
| 네트워크 | 개별 세션 오류는 해당 세션만 종료, 서버 계속 운영 |
| 명령어 | 잘못된 입력 → 에러 메시지 출력 + 세션 유지 |
| 전투/게임 로직 | exception → 로그 기록 + 해당 tick 스킵, 게임 루프 계속 |
| Lua 트리거 | `pcall()` 래핑, 오류 시 로그 + 해당 트리거 비활성화 (서버 크래시 방지) |
| DB | asyncpg 재연결 풀 (`min_size`), 저장 실패 시 3회 재시도 후 로그 |

---

## 17. 로그인/캐릭터 생성 플로우

마이그레이션 범위에 포함되지 않는 영역으로, 엔진에서 각 게임 원본을 참고하여 새로 구현한다.

### 17.1 공통 규칙 (core/)

| 항목 | 규칙 |
|------|------|
| **이름 문자** | 한글/영문/숫자 모두 허용 |
| **이름 길이** | UTF-8 기준 15바이트 이내 (한글 5자 = 15바이트) |
| **비밀번호** | bcrypt 또는 argon2 해싱 (원본 CRYPT() 대체) |
| **인코딩** | 전부 UTF-8 (원본 EUC-KR/ASCII 텍스트는 마이그레이션 시 변환) |
| **주민번호** | 전 게임 제거 (3eyes, 10woongi 원본에 있었으나 삭제) |
| **원본 문구** | 모든 프롬프트/메시지/인트로 아트를 원본 그대로 유지 (UTF-8 변환만) |
| **영문 아트** | 문구가 있으면 한글화 가능한 부분은 한글화 |

```python
# core/validation.py
def validate_name(name: str) -> bool:
    """캐릭터 이름 검증 — 한글/영문/숫자, 15바이트 이내"""
    if not name or len(name.encode("utf-8")) > 15:
        return False
    return all(
        ('\uAC00' <= ch <= '\uD7A3') or  # 한글 음절
        ch.isascii() and ch.isalnum()     # 영문/숫자
        for ch in name
    )
```

### 17.2 세션 상태 머신 (core/ 프레임워크)

`core/session.py`에 공통 상태 머신 프레임워크를 두고, 각 게임 플러그인에서 구체적 단계를 정의한다:

```python
# core/session.py
class SessionState(Protocol):
    """세션 상태 인터페이스 — 각 게임이 구현"""
    async def on_input(self, session: 'Session', text: str) -> 'SessionState | None':
        """입력 처리 후 다음 상태 반환. None이면 현재 상태 유지."""
        ...
    def prompt(self) -> str:
        """현재 상태의 프롬프트 문자열"""
        ...
```

### 17.3 게임별 로그인 플로우

#### tbaMUD-KR

```
TCP 접속
  → 인트로 화면 (text/greetings — ASCII 타이틀)
  → 이름 입력 ← 존재하지 않으면 자동 신규 분기
  → [기존] 비밀번호 → MOTD → 메인 메뉴 (0-5)
  → [신규] 이름 확인 (Y/N) → 비밀번호 설정 → 성별 (M/F) → 클래스 (4종)
           → 자동 스탯 롤링 → MOTD → 메인 메뉴
  → 메인 메뉴 "1" → 게임 진입 (시작방 3001)
```

| 단계 | 상태 | 프롬프트 |
|------|------|---------|
| 이름 | GetName | `By what name do you wish to be known?` |
| 이름 확인 | ConfirmName | `Did I get that right, {name} (Y/N)?` |
| 비밀번호 | GetPassword | `Password:` |
| 신규 비밀번호 | NewPassword | `Give me a password for {name}:` |
| 비밀번호 확인 | ConfirmPassword | `Please retype password:` |
| 성별 | SelectSex | `What is your sex (M/F)?` |
| 클래스 | SelectClass | `[C]leric [T]hief [W]arrior [M]agic-user` |
| MOTD | ReadMotd | `*** PRESS RETURN:` |
| 메인 메뉴 | MainMenu | `(0) Exit (1) Enter (2) Description (3) Background (4) Password (5) Delete` |

#### Simoon-KR

```
TCP 접속
  → ANSI 컬러 선택 (예/아니오)
  → 인트로 화면 (ANSI 환영)
  → 이름 입력 ← "환영" 입력 시 신규 모드 진입
  → [기존] 비밀번호 → MOTD → 메인 메뉴 (0-6)
  → [신규] "환영" → 이름 → 이름 확인 → 비밀번호 → 성별 (남자/여자)
           → 머리색 (5종) → 눈색 (5종) → 종족 (5종) → 직업 (7종)
           → 캐릭터상 (10종) → 연락처 → 포인트 배분 스탯
           → MOTD → 메인 메뉴
  → 메인 메뉴 "1" → 게임 진입
```

| 단계 | 프롬프트 |
|------|---------|
| ANSI | `색상을 지원하십니까 (예/아니오)?` |
| 이름 (기존) | `당신의 이름이 무엇입니까?` |
| 이름 (신규) | `"환영"` → `새로운 이름을 입력해주세요:` |
| 성별 | `캐릭터의 성(性)을 선택하십니까? (남자/여자)?` |
| 머리색 | `머리색의 선택: (1)검은색 (2)빨간색 (3)녹색 (4)황금색 (5)노란색` |
| 눈색 | `눈의 선택: (1)검은색 (2)빨간색 (3)파란색 (4)금색 (5)초록색` |
| 종족 | `종족선택: 인간/드워프/엘프/호빗/하프엘프` |
| 직업 | `직업선택: 신령사/도둑/전사/마법사/흑마법사/광전사/소환사` |
| 캐릭터상 | `캐릭터상: (1)정 ~ (10)바바` |
| 연락처 | `연락처를 입력하시오 (E-mail 또는 전화):` |
| 스탯 배분 | `총 능력치를 분배하십니다. STR/INT/WIS/DEX/CON/CHA` |

#### 3eyes-KR

```
TCP 접속
  → ANSI 선택 (1/2)
  → 인트로 화면 (log/logo — 드래곤 ASCII 아트)
  → 이름 입력 (한글) ← 존재하지 않으면 자동 신규 분기
  → [기존] 비밀번호 → 메뉴 (게임/뉴스/암호변경/복구/삭제/종료)
  → [신규] 신규 확인 (1.네/2.아니오) → 비밀번호 설정
           → 성별 (남/여) → 직업 (선택 4종: 도둑/야만인/마술사/전사) → 종족 (4종)
           → 종족별 자동 스탯 보정 → 메뉴
  → [전직] 레벨 200 도달 시 환생 (INVINCIBLE→CARETAKER→CARE_II→CARE_III, 레벨1 리셋 + 보상)
  → 메뉴 "게임" → 게임 진입
```

| 단계 | 프롬프트 |
|------|---------|
| 이름 | `당신의 이름은?` |
| 신규 확인 | `{name}이라는 이름으로 새 ID를 만드시겠습니까? 1.네 2.아니오` |
| 비밀번호 | `당신의 암호는?` |
| 성별 | `남녀입니까? 1.남 2.여` |
| 직업 | `직업을 선택: 도둑/야만인/마술사/전사` (선택 4종, 비활성 4종: 암살자/성직자/기사/탐험가) |
| 종족 | `종족을 선택: 드워프/엘프/인간/오크` |
| 환생 | 레벨 200 도달 시 `train` 명령 → 상위 등급 전직 + 레벨1 리셋 + 보상 아이템 |

#### 10woongi-KR

```
TCP 접속
  → 인트로 화면 (ASCII 아트 + 접속자 수)
  → 이름 입력 ← "새로" 입력 시 신규 모드 진입
  → [기존] 비밀번호 → 공지사항 → 게임 진입 (바로)
  → [신규] "새로" → 이름 → 비밀번호 설정/확인
           → 성별 (남/여) → 실명 입력
           → 히스토리 선택 (10개 이야기 → 스탯 자동 결정)
           → 공지사항 → 게임 진입
```

| 단계 | 프롬프트 |
|------|---------|
| 이름 | `캐릭터 이름을 입력해 주세요 (처음 만드시는 분은 '새로'라고 치세요):` |
| 비밀번호 | `비밀번호를 입력해 주세요:` |
| 성별 | `캐릭터를 입력해 주세요 (남/여):` |
| 실명 | `실명을 입력하세요:` |
| 히스토리 | 10개 캐릭터 이야기 표시 → 선택 → 스탯 자동 결정 |

### 17.4 ANSI 컬러 처리

4개 게임의 컬러 코드 시스템이 모두 다르므로, **GenOS 공통 포맷**으로 통일한다.

| 게임 | 원본 포맷 | 예시 |
|------|----------|------|
| tbaMUD | `\tX` 코드 | `\tR` = 밝은 빨강 |
| Simoon | `&X` 코드 | `&R` = 밝은 빨강 |
| 3eyes | `[=NF`/`{한글}` | `[=11F` = 밝은 청록 |
| 10woongi | `%^NAME%^` | `%^RED%^` = 빨강 |

**GenOS 공통 포맷**: `{코드명}` 형식으로 통일.

```
전경(dark):   {black} {red} {green} {yellow} {blue} {magenta} {cyan} {white}
전경(bright): {BLACK} {RED} {GREEN} {YELLOW} {BLUE} {MAGENTA} {CYAN} {WHITE}
배경:         {bg:red} {bg:blue} ... / {BG:RED} {BG:BLUE} ...
256색:        {fg:N} {bg:N}           (N = 0~255)
트루컬러:     {fg:R,G,B} {bg:R,G,B}   (24-bit RGB)
포맷:         {bold} {underline} {blink} {reverse} {italic} ...
리셋:         {reset}
```

- **마이그레이션 도구**에서 원본 → GenOS 포맷으로 변환 (DB/Lua에 GenOS 포맷으로 저장)
- **엔진**에서 GenOS 포맷 → ANSI 이스케이프로 출력 (변환기 1개, `core/ansi.py`)
- 비컬러 클라이언트에는 `strip()` 함수로 코드 제거

상세 사양은 별도 문서 참조: `docs/engine/GenOS_ANSI_Format_Reference.md`

---

## 18. 인프라 및 배포

### 18.1 Docker Compose 아키텍처

5개 컨테이너 (1 PostgreSQL + 4 게임 서버):

```
┌────────────────────────────────────────────────────────────────┐
│                     Docker Compose                              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐ │
│  │  tbamud     │  │  simoon     │  │  3eyes   │  │ 10woongi │ │
│  │  :4000      │  │  :4010      │  │  :4020   │  │  :4030   │ │
│  │  :8080      │  │  :8090      │  │  :8100   │  │  :8110   │ │
│  │  GAME=tbamud│  │  GAME=simoon│  │ GAME=    │  │ GAME=    │ │
│  └──────┬──────┘  └──────┬──────┘  └────┬─────┘  └────┬─────┘ │
│         │                │               │              │       │
│         └────────────────┼───────────────┼──────────────┘       │
│                          │               │                      │
│                    ┌─────▼───────────────▼─────┐                │
│                    │     postgres              │                │
│                    │     PostgreSQL 16          │                │
│                    │     :5432                  │                │
│                    │                            │                │
│                    │  ├── genos_tbamud          │                │
│                    │  ├── genos_simoon          │                │
│                    │  ├── genos_3eyes           │                │
│                    │  └── genos_10woongi        │                │
│                    │                            │                │
│                    │     pgdata (volume)        │                │
│                    └────────────────────────────┘                │
└────────────────────────────────────────────────────────────────┘
```

### 18.2 docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
    environment:
      POSTGRES_USER: genos
      POSTGRES_PASSWORD: genos
    ports:
      - "5432:5432"
    healthcheck:
      test: pg_isready -U genos
      interval: 5s
      retries: 5

  tbamud:
    build: .
    command: python -m core.engine
    environment:
      GAME: tbamud
      DB_URL: postgresql://genos:genos@postgres/genos_tbamud
    ports:
      - "4000:4000"     # Telnet
      - "8080:8080"     # WebSocket + REST API (/ws, /api/*)
    depends_on:
      postgres:
        condition: service_healthy

  simoon:
    build: .
    command: python -m core.engine
    environment:
      GAME: simoon
      DB_URL: postgresql://genos:genos@postgres/genos_simoon
    ports:
      - "4010:4000"
      - "8090:8080"
    depends_on:
      postgres:
        condition: service_healthy

  3eyes:
    build: .
    command: python -m core.engine
    environment:
      GAME: 3eyes
      DB_URL: postgresql://genos:genos@postgres/genos_3eyes
    ports:
      - "4020:4000"
      - "8100:8080"
    depends_on:
      postgres:
        condition: service_healthy

  10woongi:
    build: .
    command: python -m core.engine
    environment:
      GAME: 10woongi
      DB_URL: postgresql://genos:genos@postgres/genos_10woongi
    ports:
      - "4030:4000"
      - "8110:8080"
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  pgdata:
```

### 18.3 init-db.sh (PostgreSQL 초기 DB 생성)

```bash
#!/bin/bash
# docker-entrypoint-initdb.d에서 최초 1회 실행
set -e
for db in genos_tbamud genos_simoon genos_3eyes genos_10woongi; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE $db OWNER $POSTGRES_USER;
EOSQL
done
```

### 18.4 Dockerfile (단일 이미지)

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ core/
COPY games/ games/
COPY data/ data/
COPY config/ config/

# GAME 환경변수로 어떤 게임을 구동할지 결정
# 예: GAME=tbamud → config/tbamud.yaml + games/tbamud/ + data/tbamud/
ENV GAME=tbamud

CMD ["python", "-m", "core.engine"]
```

4개 게임 서버가 **동일한 Docker 이미지**를 사용하고, `GAME` 환경변수만으로 동작이 달라진다.

### 18.5 리소스 예상

서버 사양: ARM Neoverse-N1 4-core, 24GB RAM, 193GB disk

| 컨테이너 | 메모리 (예상) | 비고 |
|----------|-------------|------|
| PostgreSQL | ~200MB | 4 DB, 부팅 후 캐시 |
| tbaMUD-KR | ~150MB | 12,701방 + 1,461 트리거 인메모리 |
| Simoon-KR | ~100MB | 6,508방 |
| 3eyes-KR | ~80MB | 7,439방 |
| 10woongi-KR | ~60MB | 17,590방 (경량 엔티티) |
| **합계** | **~590MB** | 24GB 중 2.5% |

### 18.6 게임 플러그인 아키텍처

4개 게임의 서로 다른 로직(전투, 스폰, 메시지)을 **플러그인 자동 탐색**으로 관리한다:

```python
# core/plugin.py
from typing import Protocol, runtime_checkable
from pathlib import Path
import importlib

@runtime_checkable
class GamePlugin(Protocol):
    """게임별 구현이 제공해야 하는 인터페이스"""
    name: str

    def register_commands(self, cmd_dict: dict[str, str]) -> None:
        """게임 고유 명령어를 CMD dict에 등록"""
        ...

    def create_combat(self, world) -> 'CombatSystem':
        """전투 시스템 인스턴스 생성 (THAC0 or Sigma)"""
        ...

    def create_spawner(self, world) -> 'SpawnSystem':
        """스폰 시스템 인스턴스 생성"""
        ...

    def get_messages(self) -> dict[str, str]:
        """한국어 시스템 메시지 테이블 반환"""
        ...


def load_game_plugin(game_name: str) -> GamePlugin:
    """GAME 환경변수로 지정된 게임 플러그인 로드"""
    module = importlib.import_module(f"games.{game_name}.game")
    return module.plugin
```

**자동 탐색 (개발/디버그용)**:

```python
def discover_all_games() -> dict[str, type]:
    """games/ 하위 디렉토리를 스캔하여 모든 플러그인 발견"""
    games_dir = Path(__file__).parent.parent / "games"
    found = {}
    for d in games_dir.iterdir():
        if d.is_dir() and (d / "game.py").exists():
            module = importlib.import_module(f"games.{d.name}.game")
            found[d.name] = module.plugin
    return found
```

**플러그인 구현 예시 (tbaMUD)**:

```python
# games/tbamud/game.py
from games.tbamud.combat import ThacoCombat
from games.tbamud.zone import ZoneResetSpawner
from games.tbamud.messages import MESSAGES

class TbaMudPlugin:
    name = "tbamud"

    def register_commands(self, cmd_dict):
        cmd_dict.update({
            "공격": "attack", "attack": "attack",
            "도망": "flee", "flee": "flee",
            # ... 301개 명령어
        })

    def create_combat(self, world):
        return ThacoCombat(world.thac0_table, world.saving_throws)

    def create_spawner(self, world):
        return ZoneResetSpawner(world)

    def get_messages(self):
        return MESSAGES

plugin = TbaMudPlugin()
```

### 18.7 핫 리로드 아키텍처

`core/` = 재시작 필요, `games/` = 핫 리로드 가능. 핵심은 **상태(data)와 로직(logic)의 분리**이다.

#### 설계 규칙

1. **`games/` 모듈은 순수 함수만** — `world`/`ch`를 매개변수로 받고, 클래스 인스턴스를 생성하지 않음
2. **모듈 레벨 전역 상태 금지** — 상태는 모두 `World`/`CharInstance`에 저장
3. **등록은 함수 호출** — `register(cmd_dict)` 패턴으로 리로드 시 재등록

#### 핫 리로드 범위

| 범주 | 파일 | 핫 리로드 | 방법 |
|------|------|:---------:|------|
| 명령어 핸들러 | `games/*/commands.py` | O | `importlib.reload` |
| 전투 계산 | `games/*/combat.py` | O | `importlib.reload` |
| 스킬/스펠 효과 | `games/*/skills.py` | O | `importlib.reload` |
| 메시지 템플릿 | `games/*/messages.py` | O | `importlib.reload` |
| 소셜/Zone/로그인 | `games/*/social.py` 등 | O | `importlib.reload` |
| Lua 트리거 | `data/*/lua/*.lua` | O | `lupa` reload |
| 게임 루프 | `core/loop.py` | X | 재시작 |
| 네트워크/세션 | `core/network/` | X | 재시작 |
| DB 계층 | `core/db/` | X | 재시작 |

#### 리로드 메커니즘

```python
# core/reload.py
import importlib, sys

reload_queue: list[str] = []   # 파일 경로 대기열

def queue_reload(path: str):
    """리로드 요청을 큐에 추가 (즉시 실행하지 않음)"""
    reload_queue.append(path)

def apply_pending_reloads(game_name: str, cmd_dict: dict, world):
    """tick 경계에서 호출 — 대기 중인 리로드 일괄 적용"""
    if not reload_queue:
        return

    for path in reload_queue:
        module_name = path_to_module(path)
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

    # 명령어 사전 재등록
    cmd_dict.clear()
    mod_cmd = importlib.import_module(f"games.{game_name}.commands")
    mod_cmd.register(cmd_dict)

    # 전투 시스템 교체
    mod_combat = importlib.import_module(f"games.{game_name}.combat")
    world.combat = mod_combat.create_combat(world)

    reload_queue.clear()
```

#### Tick 경계 안전 적용

게임 루프가 단일 asyncio 코루틴이므로, tick 사이에만 리로드를 적용하면 핸들러 실행 중 코드 교체가 발생하지 않는다:

```
Tick N:   [입력 → 명령어 → 전투 → Zone → 출력]
           ↕ apply_pending_reloads() ← 여기서만 적용
Tick N+1: [입력 → 명령어(새 코드) → 전투(새 코드) → Zone → 출력]
```

#### 자동 리로드 (개발 환경)

`watchfiles` 라이브러리로 파일 변경 감지 → 자동 큐 등록:

```python
# core/watcher.py
from watchfiles import awatch

async def watch_and_reload(game_name: str):
    """games/ + data/lua/ 감시 → 변경 시 자동 리로드 큐 등록"""
    watch_dirs = [f"games/{game_name}/", f"data/{game_name}/lua/"]
    async for changes in awatch(*watch_dirs):
        for change_type, path in changes:
            queue_reload(path)
            logger.info(f"변경 감지 → 리로드 큐: {path}")
```

#### 설정

```yaml
# config.yaml
reload:
  auto_reload: true          # 개발: true, 운영: false
  watch_dirs:
    - "games/${GAME}/"
    - "data/${GAME}/lua/"
```

운영에서는 `auto_reload: false`로 두고, 관리자 명령(`"전체 리로드"`, `"명령어 리로드"`)이나 REST API(`POST /api/server/reload`)로만 수동 리로드한다.

#### 인게임 리로드 명령어

```
관리자: "명령어 리로드"   → games/{game}/commands.py
관리자: "전투 리로드"     → games/{game}/combat.py
관리자: "전체 리로드"     → games/{game}/* 전체
관리자: "트리거 리로드"   → data/{game}/lua/triggers.lua
```

### 18.8 개발 워크플로

로컬 개발 시에는 **Docker의 PostgreSQL만 사용**하고, 게임 서버는 로컬에서 직접 실행한다:

```bash
# 1. PostgreSQL만 Docker로 실행
docker compose up -d postgres

# 2. 로컬에서 게임 서버 실행 (hot reload 가능)
GAME=tbamud DB_URL=postgresql://genos:genos@localhost/genos_tbamud \
  python -m core.engine

# 3. 프로덕션: 전체 컨테이너 실행
docker compose up -d --build
```

이렇게 하면:
- DB가 Docker 볼륨(pgdata)에만 존재 → 마이그레이션 1회만 실행
- 로컬 코드 수정 → `watchfiles` 자동 리로드 즉시 반영 (프로세스 재시작 불필요)
- `docker compose down`해도 pgdata 볼륨은 유지

**Docker 환경에서 개발 시** — `games/`를 볼륨 마운트하면 호스트 수정이 컨테이너에서 즉시 감지:

```yaml
# docker-compose.override.yml (개발용, 버전 관리에서 제외)
services:
  tbamud:
    volumes:
      - ./games/tbamud:/app/games/tbamud
      - ./data/tbamud/lua:/app/data/tbamud/lua
    environment:
      AUTO_RELOAD: "true"
```

---

# Part III: 프레임워크 확장 (Phase B 미리보기)

## 19. 데이터 이질성 매트릭스

Phase A에서 4개 게임을 개별 구현한 후, Phase B에서 공통 패턴을 추출한다. 아래는 이질성의 전체 지도이다:

### 전투 시스템

| | tbaMUD | Simoon | 3eyes | 10woongi |
|---|--------|--------|-------|----------|
| **판정 방식** | THAC0 (d20 - AC) | THAC0 (CircleMUD 3.0) | THAC0 (Mordor 변형) | sigma 공식 (stat-based) |
| **데미지** | dice roll + str_bonus | dice roll + str_bonus | dice roll | 무기크기 × 치명타 계수 |
| **방어** | AC (단일) | AC (단일) | AC (단일) | armor_slot별 (22개) |
| **세이빙** | 5종 (class/level) | 5종 (class/level) | — | — |
| **라운드** | 2초 (20 tick) | 2초 | 2초 | 1초 |

### 캐릭터 스탯

| | tbaMUD | Simoon | 3eyes | 10woongi |
|---|--------|--------|-------|----------|
| **스탯 종류** | STR, DEX, CON, INT, WIS, CHA | STR, DEX, CON, INT, WIS, CHA | STR, DEX, CON, INT, WIS, CHA | 체력, 정신, 민첩, 지력, 의지, 매력 |
| **범위** | 3~25 (18/00 특수) | 3~25 | 3~18 | 1~100+ |
| **계산 영향** | 보정 테이블 (tohit, todam, ac) | 보정 테이블 | 보정 테이블 | 직접 공식 (sigma, bonus) |

### 장비 슬롯

| | tbaMUD | Simoon | 3eyes | 10woongi |
|---|--------|--------|-------|----------|
| **슬롯 수** | 18 | 18 | 18 | 22 |
| **추가 슬롯** | — | — | — | 귀걸이, 허리띠, 어깨, 팔찌 |

### Zone/스폰 시스템

| | tbaMUD | Simoon | 3eyes | 10woongi |
|---|--------|--------|-------|----------|
| **방식** | M/O/G/E/P/D/T 커맨드 | M/O/G/E/P/D/T | 바이너리 내장 | setRoomInventory() LPC |
| **리셋 모드** | Never/Empty/Always | Never/Empty/Always | — | — |
| **Zone 단위** | VNUM 범위 | VNUM 범위 | 디렉토리 | 파일 디렉토리 |

### VNUM 체계

| | tbaMUD | Simoon | 3eyes | 10woongi |
|---|--------|--------|-------|----------|
| **생성 방식** | 순차 정수 | 순차 정수 | 순차 정수 | SHA-256 해시 |
| **범위** | 0~99,999 | 0~99,999 | 0~99,999 | 32-bit int |
| **안정성** | 파일 내 고정 | 파일 내 고정 | 파일 내 고정 | 파일 경로 기반 결정적 |

---

## 20. Protocol 기반 플러그형 시스템

Phase B에서 4개 구현을 분석한 뒤, **Protocol**(Python의 구조적 서브타이핑)을 사용하여 교체 가능한 시스템을 설계한다.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class CombatSystem(Protocol):
    """전투 판정 프로토콜 — THAC0 또는 sigma 공식"""
    def calculate_hit(self, attacker: CharInstance, target: CharInstance) -> bool: ...
    def calculate_damage(self, attacker: CharInstance, target: CharInstance) -> int: ...
    def process_round(self, world: World) -> None: ...

@runtime_checkable
class SpawnSystem(Protocol):
    """스폰/리셋 프로토콜 — Zone 커맨드 또는 setRoomInventory"""
    def reset_zone(self, world: World, zone: Zone) -> None: ...
    def spawn_mob(self, world: World, proto_id: int, room_id: int) -> CharInstance | None: ...

@runtime_checkable
class StatCalculator(Protocol):
    """스탯 계산 프로토콜 — D&D 보정 테이블 또는 직접 공식"""
    def get_hit_bonus(self, char: CharInstance) -> int: ...
    def get_dam_bonus(self, char: CharInstance) -> int: ...
    def get_ac_bonus(self, char: CharInstance) -> int: ...
```

### 구현 예시 (Phase B 예상)

```python
class ThacoCombat:
    """tbaMUD/Simoon/3eyes용 THAC0 전투 시스템"""
    def __init__(self, thac0_table: dict, saving_throws: dict):
        self.thac0_table = thac0_table
        self.saving_throws = saving_throws

    def calculate_hit(self, attacker, target) -> bool:
        thac0 = self.thac0_table[(attacker.class_id, attacker.level)]
        roll = random.randint(1, 20)
        needed = thac0 - target.armor_class - attacker.hitroll
        return roll >= needed

class SigmaCombat:
    """10woongi용 sigma 공식 전투 시스템"""
    def __init__(self, sigma: float, formulas: dict):
        self.sigma = sigma
        self.formulas = formulas

    def calculate_hit(self, attacker, target) -> bool:
        atk = attacker.stats["민첩"] * self.sigma + attacker.stats["지력"] * 0.5
        defense = target.stats["민첩"] * self.sigma
        return random.random() < (atk / (atk + defense))
```

---

## 21. 유연한 데이터 모델

Phase B 프레임워크에서는 하드코딩된 필드 대신 **dict 기반**으로 스탯/장비/리소스 풀을 처리한다.

```python
@dataclass
class FlexCharInstance:
    """유연한 캐릭터 인스턴스 — Phase B 프레임워크"""
    id: int
    name: str
    room: int

    # 유연한 스탯 (D&D STR~CHA 또는 무협 체력~지력)
    stats: dict[str, int]           # {"str": 18} 또는 {"체력": 85}

    # 유연한 리소스 풀 (hp/mana/move 또는 hp/sp/mp)
    resources: dict[str, tuple[int, int]]  # {"hp": (100, 150), "mana": (50, 50)}

    # 유연한 장비 슬롯 (18개 또는 22개)
    equipment: dict[str, ItemInstance | None]  # {"head": item, "body": item, ...}

    # 유연한 인벤토리
    inventory: list[ItemInstance]

    # 확장 필드
    extensions: dict[str, Any]      # 게임별 커스텀 데이터
```

이 설계는 Phase A에서 각 게임을 개별 구현한 **후에** 리팩터링으로 도달하는 것이지, 미리 만들지 않는다.

---

# Part IV: 게임 생성 마법사 (Phase C 미리보기)

## 22. 마법사 개념

Phase C에서는 기획자가 웹 UI를 통해 시스템을 조합하고 5분 내에 실행 가능한 MUD를 생성한다.

### 마법사 워크플로

```
1. 기본 설정
   - 게임 이름, 설명
   - 포트 번호, 최대 레벨

2. 전투 시스템 선택
   ○ THAC0 기반 (tbaMUD/CircleMUD 스타일)
   ○ Stat-based (무협 스타일)
   ○ 커스텀 (Python 코드 직접 작성)

3. 스탯 체계 선택
   ○ D&D 6종 (STR, DEX, CON, INT, WIS, CHA)
   ○ 무협 6종 (체력, 정신, 민첩, 지력, 의지, 매력)
   ○ 커스텀 (스탯 이름/범위 직접 정의)

4. 장비 슬롯 설정
   ○ 표준 18슬롯
   ○ 확장 22슬롯
   ○ 커스텀 (슬롯 이름/수량 직접 정의)

5. 데이터 소스 선택
   ○ 빈 세계 (처음부터 OLC로 빌드)
   ○ tbaMUD 데이터 임포트
   ○ Simoon 데이터 임포트
   ○ 3eyes 데이터 임포트
   ○ 10woongi 데이터 임포트

6. 한글화 수준
   ○ 전체 한글화 (시스템 + 콘텐츠)
   ○ 시스템만 한글화 (콘텐츠 영문 유지)
   ○ 영문 전용

7. 빌드 & 실행
   → config.yaml 생성
   → DB 스키마 적용
   → 데이터 시드
   → 서버 시작
```

---

## 23. 선택 가능 시스템 매핑

Phase C 마법사에서 제공할 시스템 조합:

| 시스템 | 옵션 A | 옵션 B | 옵션 C |
|--------|--------|--------|--------|
| 전투 | THAC0 (d20+AC) | Sigma (stat 공식) | 커스텀 Python |
| 스탯 | D&D 6종 | 무협 6종 | 커스텀 N종 |
| 장비 | 18슬롯 | 22슬롯 | 커스텀 N슬롯 |
| 스폰 | Zone 커맨드 (M/O/G/E/P/D/T) | Room-based (setInventory) | 커스텀 |
| 명령어 | 한국어 + 영문 이중 지원 | 영문 전용 | 커스텀 매핑 |
| 스크립팅 | Lua (lupa) | Python only | None |
| DB | PostgreSQL (게임별 DB 분리) | — | — |

---

# 부록

## 부록 A: 마이그레이션 데이터 흐름도 (4소스)

```
┌──────────────────────────────────────────────────────────────┐
│                    마이그레이션 도구 (Python)                  │
│                                                               │
│  tbaMUD ───┐                                                  │
│  Simoon ───┼─→ Adapter → UIR (30 dataclasses) → Compiler     │
│  3eyes  ───┤                                    │             │
│  10woongi ─┘                                    ▼             │
│                                  ┌──────────────────────┐     │
│                                  │  sql/schema.sql      │     │
│                                  │  sql/seed_data.sql   │     │
│                                  │  lua/*.lua (8개)     │     │
│                                  └──────────┬───────────┘     │
└──────────────────────────────────────────────┼────────────────┘
                                               │
     ┌──────────────────┼──────────────────┼──────────────────┐
     │                  │                  │                  │
     ▼                  ▼                  ▼                  ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│tbaMUD-KR │  │Simoon-KR │  │ 3eyes-KR │  │ 10woongi-KR  │
│(Phase A-1)│  │(Phase A-2)│  │(Phase A-3)│  │ (Phase A-4)  │
│           │  │           │  │           │  │              │
│THAC0 전투 │  │THAC0 전투 │  │THAC0 전투 │  │ Sigma 전투   │
│D&D 6스탯  │  │D&D 6스탯  │  │D&D 6스탯  │  │ 무협 6스탯   │
│18슬롯     │  │18슬롯     │  │18슬롯     │  │ 22슬롯       │
│Zone M/O/G │  │Zone M/O/G │  │바이너리   │  │ LPC Spawn    │
│12,701방   │  │6,508방    │  │7,439방    │  │ 17,590방     │
│ASCII→한글 │  │EUC-KR     │  │EUC-KR    │  │ EUC-KR       │
│           │  │→UTF-8     │  │→UTF-8    │  │ →UTF-8       │
└──────────┘  └──────────┘  └──────────┘  └──────────────┘
     │              │              │              │
     └──────────────┼──────────────┼──────────────┘
                                 │
                                 ▼
                    ┌───────────────────────┐
                    │  GenOS Framework      │
                    │  (Phase B)            │
                    │                       │
                    │  Protocol 기반 시스템  │
                    │  유연한 데이터 모델    │
                    │  공통 인프라 추출      │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  게임 생성 마법사      │
                    │  (Phase C)            │
                    │                       │
                    │  시스템 선택 UI        │
                    │  데이터 선택           │
                    │  5분 내 빌드 & 실행    │
                    └───────────────────────┘
```

---

## 부록 B: tbaMUD 데이터 규모 상세

### 핵심 엔티티

| 엔티티 | 수량 | SQL 테이블 | 비고 |
|--------|------|-----------|------|
| Rooms | 12,701 | rooms | 189 Zone에 걸쳐 분포 |
| Items | 4,765 | items | 무기/방어구/포션/스크롤 등 |
| Monsters | 3,705 | monsters | NPC, 보스, 상점 주인 포함 |
| Zones | 189 | zones | lifespan 기반 자동 리셋 |
| Shops | 334 | shops | keeper_vnum으로 NPC 연결 |
| Triggers | 1,461 | triggers | DG Script → Lua 변환 |
| Quests | 1 | quests | 기본 퀘스트 |

### 콘텐츠 테이블

| 엔티티 | 수량 | SQL 테이블 | 비고 |
|--------|------|-----------|------|
| Socials | 104 | socials | 감정 표현 (smile, laugh, ...) |
| Help | 721 | help_entries | 게임 도움말 |
| Commands | 301 | commands | 게임 명령어 |
| Skills | 54 | skills | 스킬/스펠 |
| Classes | 4 | classes | Magic User, Cleric, Thief, Warrior |
| Races | 0 | races | (tbaMUD 기본은 race 없음) |

### 시스템 테이블

| 엔티티 | SQL 테이블 | 비고 |
|--------|-----------|------|
| Game Configs | game_configs | 98개 설정 (8 카테고리) |
| Experience Table | experience_table | 4 클래스 × 50 레벨 |
| THAC0 Table | thac0_table | 4 클래스 × 50 레벨 |
| Saving Throws | saving_throws | 5 유형 × 4 클래스 × 50 레벨 |
| Level Titles | level_titles | 클래스/레벨/성별별 칭호 |
| Attribute Modifiers | attribute_modifiers | 6 스탯 × 25 스코어 |
| Practice Params | practice_params | 4 클래스 |

### 마이그레이션 출력 파일 크기

| 파일 | 크기 | 줄 수 |
|------|------|-------|
| sql/schema.sql | 8 KB | 224줄 (21 테이블 DDL) |
| sql/seed_data.sql | 17 MB | 104,280줄 (25,874 INSERT) |
| lua/triggers.lua | 1.5 MB | 40,924줄 (1,461 트리거) |
| lua/combat.lua | 1.4 KB | 59줄 |
| lua/classes.lua | 1.4 KB | 63줄 |
| lua/config.lua | 1.7 KB | 84줄 |
| lua/exp_tables.lua | 2.7 KB | 152줄 |
| lua/stat_tables.lua | 15 KB | 215줄 |
| lua/korean_nlp.lua | ~5 KB | ~150줄 |
| lua/korean_commands.lua | ~8 KB | ~250줄 |
| uir.yaml | 20 MB | 905,549줄 |

---

## 부록 C: 한글화 대상 목록

### 시스템 메시지 카테고리 (~200종)

| 카테고리 | 예시 | 수량 |
|----------|------|------|
| 이동 | "그쪽으로는 갈 수 없습니다." | ~15 |
| 전투 | "당신이 {target}{을/를} 공격합니다." | ~30 |
| 아이템 | "그런 물건은 없습니다." | ~20 |
| 상점 | "영업시간이 아닙니다." | ~15 |
| 정보 | "레벨: {level}, HP: {hp}/{max_hp}" | ~20 |
| 스킬 | "마나가 부족합니다." | ~15 |
| 소통 | "{name}{이/가} 말합니다: '{msg}'" | ~10 |
| 로그인 | "캐릭터 이름을 입력하세요:" | ~15 |
| 관리자 | "권한이 없습니다." | ~10 |
| 퀘스트 | "퀘스트를 완료했습니다!" | ~10 |
| 기타 | "서버가 곧 재시작됩니다." | ~40 |

### 명령어 한국어 매핑 (301개 중 주요)

CMD dict에 한국어 키워드와 동의어를 모두 등록한다. 동의어도 별도 키로 같은 핸들러에 매핑:

| 영문 | 한국어 | 동의어 (모두 CMD dict 별도 키) |
|------|--------|-------------------------------|
| look | 봐 | 살펴, 보기 |
| north | 북 | 북쪽 |
| attack | 공격 | 때려, 쳐 |
| get | 집어 | 줍, 들어 |
| drop | 버려 | 놓 |
| wear | 입어 | 착용, 써 |
| inventory | 소지품 | 인벤 |
| score | 능력 | 능력치, 상태 |
| say | 말 | — |
| help | 도움 | 도움말 |
| who | 접속자 | 누구 |
| quit | 종료 | 나가 |
| buy | 사 | 구매 |
| sell | 팔아 | 판매 |
| cast | 시전 | 마법 |
| flee | 도망 | 도주 |

### 클래스 한국어 이름

| 영문 | 한국어 | 약칭 |
|------|--------|------|
| Magic User | 마법사 | 마 |
| Cleric | 성직자 | 성 |
| Thief | 도적 | 도 |
| Warrior | 전사 | 전 |

### 방향 한국어 매핑 (완료)

| 영문 | 한국어 | 약칭 |
|------|--------|------|
| north | 북 | 북쪽 |
| east | 동 | 동쪽 |
| south | 남 | 남쪽 |
| west | 서 | 서쪽 |
| up | 위 | 올라 |
| down | 아래 | 내려 |

### 출력 조사 자동 선택 (6종)

| 조사 쌍 | 받침 있음 | 받침 없음 | 예시 |
|----------|-----------|-----------|------|
| 이/가 | 이 | 가 | 전사**가** / 기사**가** |
| 을/를 | 을 | 를 | 고블린**을** / 드래곤**을** → 드래곤**을** |
| 은/는 | 은 | 는 | 전사**는** / 기사**는** |
| 과/와 | 과 | 와 | 전사**와** / 기사**와** |
| 으로/로 | 으로 | 로 | 검**으로** / 창**으로** |
| 이다/다 | 이다 | 다 | 전사**이다** / 기사**다** |

---

## 부록 D: 전통 MUD 엔진과의 비교

| 특성 | tbaMUD (전통) | GenOS tbaMUD-KR (v2.0) |
|------|-------------|------------------------|
| 언어 | C | Python 3.12 |
| I/O | select() 단일 스레드 | asyncio 코루틴 |
| 데이터 저장 | 텍스트 파일 | PostgreSQL 16 |
| 스크립팅 | DG Script | Lua (lupa) + Python |
| 접속 방식 | Telnet만 | Telnet + WebSocket + REST |
| 인코딩 | ASCII | UTF-8 (EUC-KR 자동 변환) |
| 한국어 입력 | SVO만 (영어식) | 마지막 토큰=명령어 + SVO 폴백 |
| 한국어 출력 | — (영문 전용) | 받침 기반 자동 조사 |
| 관리 도구 | 인게임 텍스트 | FastAPI 웹 대시보드 + 인게임 |
| 동시접속 | ~300 (select 한계) | 수백+ (asyncio) |
| 핫 리로드 | 불가 (재컴파일) | Lua 핫 리로드, Python 모듈 리로드 |
| 데이터 로딩 | 텍스트 파싱 | SQL SELECT (마이그레이션 출력) |
| API | 없음 | REST API + Swagger 문서 |

---

## 부록 E: 프로젝트 디렉토리 구조 (4개 게임 완료 시)

```
genos-engine/
├── docker-compose.yml          # 5 컨테이너 정의 (1 postgres + 4 game)
├── Dockerfile                  # 단일 이미지 (GAME env var로 분기)
├── requirements.txt            # Python 의존성
│
├── scripts/
│   └── init-db.sh              # PostgreSQL 최초 4 DB 생성
│
├── config/                     # 게임별 설정 파일
│   ├── tbamud.yaml
│   ├── simoon.yaml
│   ├── 3eyes.yaml
│   └── 10woongi.yaml
│
├── core/                       # 공통 프레임워크 (모든 게임이 공유)
│   ├── __init__.py
│   ├── engine.py               # 엔진 진입점, 부트 시퀀스
│   ├── loop.py                 # 10Hz 게임 루프
│   ├── session.py              # SessionState Protocol, Session 클래스
│   ├── plugin.py               # GamePlugin Protocol, load/discover
│   ├── reload.py               # 핫 리로드 메커니즘 (importlib.reload, tick 경계 적용)
│   ├── watcher.py              # watchfiles 기반 자동 리로드 (개발용)
│   │
│   ├── network/
│   │   ├── __init__.py
│   │   ├── telnet.py           # asyncio Telnet 서버
│   │   ├── websocket.py        # FastAPI WebSocket
│   │   ├── rest.py             # FastAPI REST API
│   │   └── session.py          # SessionManager, 입출력 큐
│   │
│   ├── world/
│   │   ├── __init__.py
│   │   ├── loader.py           # 21 테이블 → 메모리 로드
│   │   ├── prototype.py        # RoomProto, ItemProto, MobProto
│   │   ├── instance.py         # RoomInstance, ItemInstance, CharInstance
│   │   └── world.py            # World 통합 구조체
│   │
│   ├── command/
│   │   ├── __init__.py
│   │   ├── parser.py           # 위치 기반 명령어 파서 (CMD dict)
│   │   └── dispatcher.py       # 핸들러 디스패치
│   │
│   ├── korean/
│   │   ├── __init__.py
│   │   └── output.py           # has_batchim, render_message (출력 조사)
│   │
│   ├── ansi.py                 # GenOS ANSI 포맷 → ANSI 이스케이프 변환기
│   ├── validation.py           # 이름 검증 (한글/영문/숫자, 15바이트)
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── pool.py             # asyncpg 연결 풀 + 자동 초기화
│   │   └── player.py           # 플레이어 저장/로드
│   │
│   └── admin/
│       ├── __init__.py
│       ├── api.py              # FastAPI REST 라우터
│       └── olc.py              # 인게임 OLC 명령어
│
├── games/                      # 게임별 플러그인 (GamePlugin 구현)
│   ├── tbamud/
│   │   ├── __init__.py
│   │   ├── game.py             # TbaMudPlugin (플러그인 진입점)
│   │   ├── login.py            # 로그인 플로우 (자동 신규 분기, 4클래스, 자동 롤링)
│   │   ├── combat.py           # ThacoCombat (THAC0 전투)
│   │   ├── zone.py             # ZoneResetSpawner (M/O/G/E/P/D/T)
│   │   ├── commands.py         # 301개 명령어 핸들러
│   │   ├── messages.py         # 한국어 시스템 메시지 (~200종)
│   │   └── triggers.py         # lupa Lua VM, DG Script 트리거
│   │
│   ├── simoon/
│   │   ├── __init__.py
│   │   ├── game.py             # SimoonPlugin
│   │   ├── login.py            # 로그인 플로우 ("환영" 신규, 7클래스/5종족, 외형, 포인트 배분)
│   │   ├── combat.py           # ThacoCombat (CircleMUD 3.0 변형)
│   │   ├── zone.py             # ZoneResetSpawner
│   │   ├── commands.py         # 546개 명령어 핸들러
│   │   ├── messages.py         # 한국어 시스템 메시지
│   │   └── quest.py            # 16 퀘스트 시스템
│   │
│   ├── 3eyes/
│   │   ├── __init__.py
│   │   ├── game.py             # ThreeEyesPlugin
│   │   ├── login.py            # 로그인 플로우 (자동 신규 분기, 4클래스/4종족, 종족 스탯 보정)
│   │   ├── combat.py           # ThacoCombat (Mordor 변형)
│   │   ├── zone.py             # 바이너리 내장 스폰
│   │   ├── commands.py         # 명령어 핸들러
│   │   └── messages.py         # 한국어 시스템 메시지
│   │
│   └── 10woongi/
│       ├── __init__.py
│       ├── game.py             # WoongiPlugin
│       ├── login.py            # 로그인 플로우 ("새로" 신규, 히스토리→스탯, 실명)
│       ├── combat.py           # SigmaCombat (stat-based 공식)
│       ├── zone.py             # LPC 스폰 (setRoomInventory)
│       ├── commands.py         # 51개 명령어 핸들러
│       ├── messages.py         # 한국어 시스템 메시지
│       ├── stats.py            # 무협 6스탯 + sigma 공식
│       └── equipment.py        # 22슬롯 장비 시스템
│
├── data/                       # 마이그레이션 출력 (게임별)
│   ├── tbamud/
│   │   ├── sql/
│   │   │   ├── schema.sql      # 21 테이블 DDL
│   │   │   └── seed_data.sql   # 25,874 INSERT 문 (17MB)
│   │   └── lua/
│   │       ├── combat.lua      # THAC0 계산
│   │       ├── classes.lua     # 4 클래스 정의
│   │       ├── triggers.lua    # 1,461 DG Script → Lua (1.5MB)
│   │       ├── config.lua      # 98개 게임 설정
│   │       ├── exp_tables.lua  # 경험치 테이블
│   │       ├── stat_tables.lua # THAC0/세이빙/스탯 테이블
│   │       ├── korean_nlp.lua  # 한글 유틸
│   │       └── korean_commands.lua  # 한국어 명령어 매핑
│   │
│   ├── simoon/
│   │   ├── sql/ (schema.sql + seed_data.sql)
│   │   └── lua/ (8개 Lua 스크립트)
│   │
│   ├── 3eyes/
│   │   ├── sql/ (schema.sql + seed_data.sql)
│   │   └── lua/ (8개 Lua 스크립트)
│   │
│   └── 10woongi/
│       ├── sql/ (schema.sql + seed_data.sql)
│       └── lua/ (8개 Lua 스크립트)
│
└── tests/
    ├── core/                   # 프레임워크 테스트
    │   ├── test_parser.py
    │   ├── test_korean.py
    │   ├── test_session.py
    │   └── test_world.py
    │
    ├── games/                  # 게임별 테스트
    │   ├── test_tbamud.py
    │   ├── test_simoon.py
    │   ├── test_3eyes.py
    │   └── test_10woongi.py
    │
    └── integration/            # 통합 테스트
        ├── test_boot.py
        └── test_commands.py
```

### config/tbamud.yaml 예시

```yaml
server:
  name: "GenOS tbaMUD-KR"
  telnet_port: 4000
  websocket_port: 8080
  api_port: 8081
  tick_rate_hz: 10

database:
  url: "postgresql://genos:genos@localhost/genos_tbamud"   # DB_URL 환경변수가 있으면 우선
  max_connections: 10

game:
  start_room: 3001
  max_level: 50
  pk_allowed: false
  auto_save_minutes: 5

lua:
  script_dir: "data/tbamud/lua/"
  hot_reload: true

korean:
  enabled: true
  cmd_last_token: true         # 마지막 토큰 = 명령어 (한국어 어순)
  svo_fallback: true           # 첫 토큰 = 명령어 (영문 SVO 폴백)

reload:
  auto_reload: true              # 개발: true, 운영: false
  watch_dirs:
    - "games/tbamud/"
    - "data/tbamud/lua/"

logging:
  level: "info"
  file: "logs/tbamud.log"
```

**환경변수 우선**: YAML에는 기본값을 기재하고, Python에서 환경변수를 우선 적용한다:

```python
db_url = os.environ.get("DB_URL", config["database"]["url"])
auto_reload = os.environ.get("AUTO_RELOAD", str(config["reload"]["auto_reload"])).lower() == "true"
```

---

## 부록 F: 구현 우선순위 (Phase A-1: tbaMUD-KR)

### 스프린트 1: 기반 + 인프라 (2주)

```
- Docker Compose + Dockerfile + init-db.sh
- core/ 프로젝트 구조 + asyncio 프레임워크
- GamePlugin Protocol + 플러그인 로더
- asyncpg 연결 풀 + DB 자동 초기화 (rooms 체크)
- 21 테이블 → 메모리 로드 (load_world)
- 기본 Telnet 서버 (접속, 텍스트 송수신)
- 세션 관리 (asyncio.Queue 기반 입출력)
- 게임 루프 프레임워크 (10Hz tick)
- 핫 리로드 프레임워크 (core/reload.py, tick 경계 적용)
- 로그인/캐릭터 생성 (players 테이블)
- 테스트: pytest + pytest-asyncio fixture 구축
```

### 스프린트 2: 핵심 게임플레이 (2주)

```
- 이동 (방, 출구, 방향 명령어 — 한국어/영문)
- look (방 묘사, 캐릭터/아이템 표시)
- 위치 기반 명령어 파서 (CMD dict, 마지막 토큰=명령어)
- 301개 명령어 한국어/영문 매핑
- inventory, equipment, score
- get/drop/wear/remove
- 한국어 시스템 메시지 + 받침 조사 출력
```

### 스프린트 3: 전투 + Zone (2주)

```
- THAC0 기본 전투 (명중, 데미지, 사망)
- 54 스킬/스펠 (기본 시전)
- 전투 한국어 메시지 + 자동 조사
- Zone 리셋 (M/O/G/E/P/D/T)
- 몬스터/아이템 스폰
```

### 스프린트 4: 게임 시스템 (2주)

```
- 상점 (buy/sell, 334개 shop)
- 소셜 (104개 감정 표현)
- 도움말 (721개 help 엔트리)
- 퀘스트 (기본 추적/완료)
```

### 스프린트 5: 스크립팅 + 관리 (2주)

```
- lupa 트리거 실행 (1,461개 DG Script 변환본)
- 엔진 → Lua API (30+ 함수)
- FastAPI REST API + WebSocket (단일 포트 8080)
- 인게임 OLC (redit/oedit/medit/zedit)
- watchfiles 자동 리로드 (개발 환경)
- MCCP2/GMCP 지원 (Telnet 옵션 협상)
```

### 스프린트 6: 안정화 + 한글화 완성 (2주)

```
- 전체 시스템 메시지 한글화 (~200종)
- 도움말 한글 번역 (주요 50개)
- 성능 프로파일링 + 최적화
- 통합 테스트 (Docker Compose 풀 부팅 테스트 포함)
- docker compose up -d --build 로 프로덕션 배포 검증
```

---

**문서 버전**: 2.3
**최종 업데이트**: 2026-02-10

**변경 이력**:
- v2.0: Rust→Python 전환, 바텀업 전략, tbaMUD-KR Phase A-1 상세 설계, NLP 제거 → 위치 기반 명령어 파서
- v2.1: 인프라 확정 — Docker Compose (1 postgres + 4 game), DB 분리 (4 DBs in 1 instance), Redis 불필요, GamePlugin 자동 탐색, Boot-time DB 자동 초기화, 4-game 프로젝트 디렉토리 구조
- v2.2: 로그인/캐릭터 생성 플로우 (4게임별 원본 재현), ANSI 컬러 GenOS 공통 포맷 (마이그레이션 시 변환), 이름 규칙 (한글/영문/숫자 15바이트), 비밀번호 bcrypt 현대화, 주민번호 제거, 별도 ANSI 레퍼런스 문서 작성
- v2.3: 전체 문서 검토 및 보완 — 핫 리로드 아키텍처 (importlib.reload + tick 경계 안전 적용 + watchfiles 자동 감지), 명령어 prefix 매칭 + 초성 약칭, alias(줄임말) 시스템, DG Script 엔진 API 매핑 8종, graceful shutdown 6단계, 에러 처리 5계층 정책, rate limiting, WS+REST 단일 포트 통합, Telnet 인코딩 감지, 3eyes 환생 시스템, skills 65→54 수정, 부록A 3eyes-KR 추가
