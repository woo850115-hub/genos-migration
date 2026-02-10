# GenOS (제노스) 프로젝트 마스터 플랜
**Universal MUD Migration & Management Platform**

Version: 2.0  
Last Updated: 2026-02-09  
Author: 누렁이

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [핵심 전략: 범용 마이그레이션](#2-핵심-전략-범용-마이그레이션)
3. [기술 아키텍처](#3-기술-아키텍처)
4. [UIR (Universal Intermediate Representation)](#4-uir-universal-intermediate-representation)
5. [구현 로드맵](#5-구현-로드맵)
6. [상세 설계](#6-상세-설계)
7. [위험 요소 및 대응](#7-위험-요소-및-대응)
8. [성공 지표](#8-성공-지표)
9. [부록](#9-부록)

---

## 1. 프로젝트 개요

### 1.1 비전

**"모든 MUD를, 어떤 엔진이든, GenOS로"**

GenOS는 텍스트 기반 MUD 게임의 제작과 운영을 혁신하는 플랫폼입니다. 기존 MUD를 쉽게 마이그레이션하고, 새로운 MUD를 노코드/로우코드로 제작하며, 무중단 실시간 운영 관리를 제공합니다.

### 1.2 핵심 가치 제안

#### 기존 MUD 운영자를 위해
- **5분 마이그레이션**: 기존 MUD를 GenOS로 자동 변환
- **무중단 운영**: 서버 재시작 없이 밸런스 패치
- **90% 시간 절감**: 코드 수정 대신 대시보드 클릭

#### 신규 개발자를 위해
- **빠른 프로토타입**: 30분 안에 플레이 가능한 게임
- **노코드 80% + 로우코드 20%**: 비개발자도 대부분 작업 가능
- **템플릿 기반**: 정통 판타지, 무협 등 장르별 시작점 제공

#### 전체 MUD 커뮤니티를 위해
- **통합 플랫폼**: 모든 MUD 계열이 하나의 생태계에서
- **플러그인 마켓**: 시스템 공유 및 재사용
- **데이터 기반 운영**: A/B 테스트, 실시간 분석

### 1.3 경쟁 우위

| 항목 | Evennia | CircleMUD | RPG Maker | GenOS |
|------|---------|-----------|-----------|-------|
| 마이그레이션 | ❌ | ❌ | ❌ | ✅ 모든 MUD |
| 노코드 | ❌ | ❌ | ✅ | ✅ 80% |
| Live Ops | ❌ | ❌ | ❌ | ✅ Hot-swap |
| 진입장벽 | 높음 | 매우 높음 | 낮음 | 낮음 |
| 멀티플레이어 | ✅ | ✅ | ❌ | ✅ |

---

## 2. 핵심 전략: 범용 마이그레이션

### 2.1 왜 마이그레이션인가?

#### 시장 규모 확대
```
[Before] 특정 MUD 계열만 지원
타겟: CircleMUD 사용자 (~100 서버)

[After] 모든 MUD 계열 지원
타겟: 전 세계 모든 MUD (~1,000+ 서버)
```

#### 네트워크 효과
1. CircleMUD 서버 A 마이그레이션 성공 → 커뮤니티 확산
2. DikuMUD 서버 B 마이그레이션 성공 → 다른 계열 확산
3. 각 계열 성공 사례 축적 → GenOS가 업계 표준으로

#### 즉각적 가치 제공
- 신규 도구: "빈 캔버스 두려움" → 채택률 낮음
- 마이그레이션 도구: "기존 MUD 그대로 이전" → 즉시 체험 가능

### 2.2 지원 대상 MUD 계열

#### Phase 1 (Year 1)
- **CircleMUD/tbaMUD**: 가장 대중적, 문서화 우수
- **DikuMUD/ROM**: CircleMUD 기반, 유사 구조
- **LP-MUD**: 완전히 다른 구조 (UIR 검증용)

#### Phase 2 (Year 2)
- **MUSH/MUX/PennMUSH**: 소셜 중심 MUD
- **MOO**: 교육용으로 많이 사용
- **Evennia**: 현대적 Python 기반

#### Phase 3 (Future)
- **독자 개발 MUD**: AI 기반 Custom Parser
- **상용 MUD**: 한국 상용 MUD 엔진 (별도 계약)

### 2.3 성공 시나리오

```
[2026 Q4] CircleMUD 마이그레이션 완벽 지원
→ CircleMUD 커뮤니티에서 "GenOS 효과" 입소문

[2027 Q2] 3개 주요 계열 지원
→ "어떤 MUD든 GenOS로" 브랜딩 확립

[2027 Q4] 100+ 서버 마이그레이션
→ 커뮤니티 기여 시작 (어댑터 개발)

[2028+] 신규 MUD도 GenOS로 시작
→ 산업 표준 플랫폼
```

---

## 3. 기술 아키텍처

### 3.1 전체 구조

```
┌─────────────────────────────────────────────────────────┐
│                    MUD Source Files                     │
│  CircleMUD  │  DikuMUD  │  LP-MUD  │  MUSH  │  Custom  │
└───────────────────────────┬─────────────────────────────┘
                            │
                ┌───────────▼──────────┐
                │  Source Adapters     │  각 MUD 계열별 파서
                │  (Pluggable)         │
                └───────────┬──────────┘
                            │
        ┌───────────────────▼───────────────────┐
        │   UIR (Universal Intermediate         │
        │   Representation)                     │
        │   - Standard JSON/YAML Format         │
        │   - All MUD concepts normalized       │
        └───────────────────┬───────────────────┘
                            │
                ┌───────────▼──────────┐
                │  GenOS Compiler      │
                │  - DB Schema Gen     │
                │  - Lua Script Gen    │
                │  - Config Gen        │
                └───────────┬──────────┘
                            │
        ┌───────────────────▼───────────────────┐
        │         GenOS Project                 │
        │  ┌────────────┬──────────┬─────────┐  │
        │  │ PostgreSQL │ Lua VM   │ Web UI  │  │
        │  └────────────┴──────────┴─────────┘  │
        └───────────────────────────────────────┘
```

### 3.2 핵심 컴포넌트

#### 3.2.1 Source Adapters (입구)
각 MUD 계열의 데이터를 읽어 UIR로 변환

```python
class BaseAdapter:
    """모든 어댑터의 기본 인터페이스"""
    
    def parse(self, mud_path: str) -> UniversalIR:
        """MUD 파일을 UIR로 변환"""
        pass
    
    def analyze_complexity(self) -> dict:
        """마이그레이션 복잡도 분석"""
        pass
    
    def estimate_success_rate(self) -> float:
        """변환 성공률 예측"""
        pass
```

지원 어댑터:
- `CircleMudAdapter`: CircleMUD/tbaMUD
- `DikuMudAdapter`: DikuMUD/ROM
- `LPMudAdapter`: LP-MUD/MudOS
- `MushAdapter`: MUSH/MUX/Penn
- `CustomAdapter`: AI 기반 범용 파서

#### 3.2.2 UIR (중간 표현)
모든 MUD의 공통 개념을 표준화한 중간 포맷

```yaml
# UIR 예시 구조
uir_version: "1.0"
source_mud:
  type: "circlemud"
  version: "3.1"
  path: "/path/to/mud"

metadata:
  game_id: "fantasy_world_001"
  game_name: "판타지 월드"
  created_at: "2026-02-09T10:00:00Z"

entities:
  rooms: [...] 
  character_classes: [...]
  items: [...]
  monsters: [...]
  combat_system: {...}
```

#### 3.2.3 GenOS Compiler (출구)
UIR을 GenOS 프로젝트로 변환

```python
class GenosCompiler:
    """UIR → GenOS 프로젝트 변환"""
    
    def compile(self, uir: UniversalIR) -> GenosProject:
        """전체 프로젝트 생성"""
        project = GenosProject()
        
        project.db_schema = self.generate_db_schema(uir)
        project.seed_data = self.generate_seed_data(uir)
        project.lua_scripts = self.generate_lua_scripts(uir)
        project.config = self.generate_config(uir)
        project.dashboard = self.generate_dashboard(uir)
        
        return project
```

#### 3.2.4 GenOS Runtime (실행 환경)

**Engine Core**:
- Plugin Loader: Hot-swappable 플러그인 관리
- Event Bus: Pub/Sub 기반 느슨한 결합
- Session Manager: Telnet/WebSocket 통합 관리

**Database**: PostgreSQL
- 하이브리드 스키마: 정적 컬럼 + JSONB
- 게임별 독립 스키마: `game_{id}.*`
- 필드 승격 시스템: JSONB → 정적 컬럼 마이그레이션

**Script Engine**: Lua (Lupa)
- VM 레벨 샌드박싱
- 계층적 제한: Simple/Normal/Heavy
- 디버깅 도구: 에러 메시지 한국어화

**Web Dashboard**: React + Tailwind
- 비주얼 노드 에디터 (React-flow)
- 스프레드시트 UI (데이터 편집)
- 실시간 모니터링

### 3.3 데이터 흐름

#### 마이그레이션 플로우
```
1. 기존 MUD 업로드
   └─> Adapter 자동 감지 (파일 구조 분석)

2. Source Adapter 실행
   ├─> 데이터 파일 파싱 (world, obj, mob)
   ├─> 소스 코드 분석 (C, LPC 등)
   └─> UIR 생성

3. 복잡도 분석 및 리포트
   ├─> 자동 변환 가능: 95%
   ├─> 일부 수정 필요: 3%
   └─> 수동 작업 필요: 2%

4. GenOS Compiler 실행
   ├─> PostgreSQL 스키마 생성
   ├─> 데이터 삽입 SQL 실행
   ├─> Lua 스크립트 생성
   └─> 설정 파일 생성

5. GenOS 프로젝트 생성 완료
   └─> 웹 대시보드로 접속 가능
```

#### 런타임 플로우
```
1. 플레이어 명령어 입력
   └─> Session Manager 수신

2. Command Parser
   └─> Event Bus로 발행

3. 플러그인 처리
   ├─> Trigger 조건 확인
   ├─> Condition 평가
   ├─> Action 실행 (Lua)
   └─> DB 업데이트

4. 결과 전송
   └─> Session Manager → 플레이어
```

---

## 4. UIR (Universal Intermediate Representation)

### 4.1 설계 원칙

1. **최소 공통분모**: 모든 MUD가 공유하는 개념만 포함
2. **확장 가능성**: 계열별 특수 기능은 `extensions` 필드로
3. **원본 보존**: 변환 과정에서 정보 손실 방지
4. **버전 관리**: 스펙 진화를 위한 버전 태깅

### 4.2 UIR 스펙 v1.0

#### 4.2.1 메타데이터

```yaml
uir_version: "1.0"
source_mud:
  type: "circlemud"  # circlemud, dikumud, lpmud, mush, custom
  version: "3.1"
  path: "/original/mud/path"
  detected_features:
    - "classes"
    - "races"
    - "skill_system"
    - "quest_system"

metadata:
  game_id: "fantasy_world_001"
  game_name: "판타지 월드"
  created_at: "2026-02-09T10:00:00Z"
  migration_tool_version: "1.0.0"
  
migration_stats:
  total_entities: 1234
  auto_converted: 1150
  manual_review_needed: 84
  conversion_confidence: 0.93
```

#### 4.2.2 Room (방)

```yaml
rooms:
  - id: "3001"
    name: "숲 속 공터"
    description: |
      햇살이 비치는 작은 공터입니다.
      북쪽으로 마을이, 남쪽으로 어두운 던전이 보입니다.
    
    exits:
      north:
        target_room_id: "3000"
        door: null
        keywords: []
      south:
        target_room_id: "3002"
        door:
          name: "낡은 문"
          key_id: "rusty_key"
          locked: true
    
    sector_type: "forest"  # indoor, city, field, forest, hills, mountain, water...
    
    flags:
      - "peaceful"  # no combat
      - "no_magic"
    
    # 원본 정보 보존
    source_metadata:
      source_file: "30.wld"
      source_format: "circlemud_wld"
      original_vnum: 3001
      conversion_notes: "Standard room, auto-converted"
```

#### 4.2.3 Character Class (직업)

```yaml
character_classes:
  - id: "warrior"
    name: "전사"
    display_name:
      ko: "전사"
      en: "Warrior"
    
    description: "강력한 체력과 물리 공격력을 가진 전투의 달인"
    
    starting_stats:
      hp: 150
      mp: 30
      str: 15
      dex: 8
      int: 5
      wis: 5
      con: 12
      cha: 6
    
    level_up_stats:
      hp_per_level: 15
      mp_per_level: 3
      # 레벨업 시 추가 스탯 포인트
      stat_points_per_level: 1
    
    starting_equipment:
      - item_id: "rusty_sword"
        slot: "weapon"
        auto_equip: true
      - item_id: "leather_armor"
        slot: "body"
        auto_equip: true
    
    starting_skills:
      - skill_id: "bash"
        level: 1
      - skill_id: "rescue"
        level: 3
    
    restrictions:
      allowed_races: ["human", "dwarf", "orc"]
      prohibited_alignments: []
    
    # 복잡한 레벨업 로직은 스크립트로
    custom_levelup_script: |
      -- Lua code
      function on_levelup(character, new_level)
        if new_level % 5 == 0 then
          learn_skill(character, "tier_" .. (new_level // 5) .. "_skill")
        end
      end
    
    source_metadata:
      source_file: "class.c"
      source_function: "init_warrior()"
      conversion_confidence: 0.98
```

#### 4.2.4 Item (아이템)

```yaml
items:
  - id: "rusty_sword"
    name: "녹슨 검"
    aliases: ["sword", "검", "낡은검"]
    
    description:
      short: "녹슨 검"
      long: "오랜 세월 방치되어 녹이 슨 검입니다."
      on_ground: "녹슨 검이 바닥에 놓여있습니다."
    
    item_type: "weapon"
    
    stats:
      damage_dice: "1d6"  # 1d6+2 형식
      damage_bonus: 2
      weight: 3.5  # kg
      value: 10    # gold
    
    flags:
      - "takeable"
      - "wieldable"
    
    wear_slots: ["weapon"]  # weapon, shield, head, body, arms, legs...
    
    # 착용 시 효과
    equip_effects:
      - type: "stat_modifier"
        stat: "str"
        value: 1
      - type: "skill_bonus"
        skill: "sword_fighting"
        value: 5
    
    # 사용 시 효과 (소모품)
    use_effects: []
    
    # 특수 스크립트
    special_script: null
    
    source_metadata:
      source_file: "30.obj"
      original_vnum: 3001
```

#### 4.2.5 Monster/NPC

```yaml
monsters:
  - id: "goblin_scout"
    name: "고블린 정찰병"
    aliases: ["goblin", "scout", "고블린"]
    
    description:
      short: "고블린 정찰병"
      long: "초록색 피부를 가진 작은 인간형 생물입니다."
    
    stats:
      level: 3
      hp: 30
      mp: 10
      str: 8
      dex: 12
      int: 6
      
      armor_class: 15
      hitroll: 2   # 공격 명중률 보너스
      damroll: 1   # 데미지 보너스
    
    combat:
      damage_dice: "1d4"
      attack_type: "pierce"  # slash, pierce, bludgeon...
      
    ai_type: "aggressive"  # passive, aggressive, helper...
    
    # AI 행동 패턴
    behavior:
      aggro_range: 2  # 2칸 이내 플레이어 공격
      flee_hp_percent: 20  # HP 20% 이하 시 도망
      call_for_help: true
    
    # 드랍 아이템
    loot_table:
      - item_id: "gold"
        quantity_min: 1
        quantity_max: 5
        drop_chance: 1.0  # 100%
      - item_id: "goblin_ear"
        quantity_min: 1
        quantity_max: 1
        drop_chance: 0.5  # 50%
    
    # 경험치 보상
    exp_reward: 50
    
    # 스폰 정보
    spawn_locations:
      - room_id: "3010"
        max_count: 3
        respawn_time_minutes: 5
    
    # 대화 (NPC만)
    dialogue: null
    
    source_metadata:
      source_file: "30.mob"
      original_vnum: 3001
```

#### 4.2.6 Combat System

```yaml
combat_system:
  type: "turn_based"  # turn_based, realtime, hybrid
  
  # 선공 판정
  initiative:
    formula: "dex + 1d20"
    surprise_bonus: 5
  
  # 데미지 계산
  damage_calculation:
    base_formula: "weapon_damage + str_bonus - target_ac"
    
    critical:
      chance_formula: "dex / 10"  # %
      multiplier: 2.0
    
    dodge:
      chance_formula: "target_dex / 5"
      result: "miss"
  
  # 속성 시스템
  elements:
    enabled: true
    types: ["fire", "water", "earth", "air"]
    effectiveness:
      fire_vs_water: 0.5
      water_vs_fire: 2.0
  
  # 턴 시스템 (turn_based인 경우)
  turns:
    time_limit_seconds: 30
    actions_per_turn: 1
    
  # 실시간 시스템 (realtime인 경우)
  realtime:
    global_cooldown_ms: 1000
    skill_cooldown_enabled: true
  
  # 복잡한 로직은 스크립트로
  custom_combat_script: |
    -- Lua code
    function calculate_damage(attacker, defender, weapon)
      -- 커스텀 계산 로직
    end
  
  source_metadata:
    extracted_from: ["fight.c", "combat.c"]
    conversion_confidence: 0.85
    notes: "Complex combat logic partially converted"
```

#### 4.2.7 Command System

```yaml
commands:
  # 기본 명령어는 GenOS에서 제공
  # 커스텀 명령어만 UIR에 포함
  
  custom_commands:
    - name: "auction"
      aliases: ["경매", "auc"]
      
      description: "아이템 경매 시스템"
      
      usage: "auction <item> <starting_price>"
      
      permission_level: "player"  # player, immortal, admin
      
      implementation:
        type: "lua_script"
        script: |
          function do_auction(character, args)
            -- 경매 로직
          end
      
      source_metadata:
        source_file: "auction.c"
        function_name: "do_auction"
        complexity: "high"
        manual_conversion_needed: true
```

### 4.3 확장 메커니즘

계열별 특수 기능은 `extensions` 필드로 보존:

```yaml
extensions:
  # LP-MUD의 상속 시스템
  lpmud_inheritance:
    base_objects:
      - "/std/room.c"
      - "/std/weapon.c"
  
  # MUSH의 속성 시스템  
  mush_attributes:
    custom_attributes:
      - name: "@describe"
        value: "..."
  
  # CircleMUD의 특수 프로시저
  circlemud_special_procs:
    - mob_id: "3001"
      proc_name: "guild_guard"
      source_function: "guild_guard()"
```

---

## 5. 구현 로드맵

### 5.1 Phase 1: Foundation (3개월)

**목표**: CircleMUD 완벽 마이그레이션 + GenOS Core

#### Week 1-2: UIR 스펙 확정
- [ ] MUD 계열 조사 (CircleMUD, DikuMUD, LP-MUD...)
- [ ] 공통 개념 추출 및 문서화
- [ ] UIR YAML 스키마 작성
- [ ] 예제 UIR 파일 10개 작성

**산출물**:
- `uir-spec-v1.0.md`: 스펙 문서
- `examples/*.yaml`: 예제 UIR 파일
- `schema/uir.schema.json`: JSON Schema

#### Week 3-6: CircleMUD Adapter

**3주차**: 데이터 파일 파서
- [ ] World 파일 파서 (.wld)
- [ ] Object 파일 파서 (.obj)
- [ ] Mobile 파일 파서 (.mob)
- [ ] Shop 파일 파서 (.shp)
- [ ] Zone 파일 파서 (.zon)

**4주차**: 소스 코드 분석
- [ ] C 파서 통합 (pycparser)
- [ ] class.c 분석 (직업 정의)
- [ ] fight.c 분석 (전투 로직)
- [ ] spec_procs.c 분석 (특수 프로시저)

**5-6주차**: UIR 생성 및 테스트
- [ ] CircleMudAdapter 클래스 완성
- [ ] 실제 CircleMUD로 테스트 (3개 이상)
- [ ] 복잡도 분석 알고리즘
- [ ] 변환 성공률 측정

**산출물**:
- `adapters/circlemud.py`: CircleMUD 어댑터
- `tests/test_circlemud_adapter.py`: 테스트 코드
- `docs/circlemud-migration-guide.md`: 사용자 가이드

#### Week 7-10: GenOS Core

**7주차**: 데이터베이스 설계
- [ ] PostgreSQL 하이브리드 스키마 설계
- [ ] 마이그레이션 스크립트
- [ ] Seed data 생성 로직

**8주차**: GenOS Compiler
- [ ] UIR → DB Schema 변환
- [ ] UIR → Lua Script 생성
- [ ] UIR → Config 파일 생성

**9주차**: GenOS Runtime (최소 기능)
- [ ] Session Manager (Telnet/WebSocket)
- [ ] Command Parser
- [ ] Event Bus
- [ ] Plugin Loader (기본 구조만)

**10주차**: 통합 테스트
- [ ] 전체 파이프라인 테스트
- [ ] CircleMUD → GenOS → 실제 플레이
- [ ] 버그 수정 및 최적화

**산출물**:
- `genos/compiler/`: 컴파일러 코드
- `genos/runtime/`: 런타임 코드
- `database/schema.sql`: DB 스키마
- `docs/architecture.md`: 아키텍처 문서

#### Week 11-12: MVP 완성

**11주차**: CLI 도구
- [ ] `genos migrate` 명령어
- [ ] `genos analyze` 명령어
- [ ] `genos serve` 명령어
- [ ] 진행률 표시 UI

**12주차**: 문서 및 예제
- [ ] 사용자 매뉴얼
- [ ] 개발자 문서
- [ ] 예제 프로젝트 2개
- [ ] 튜토리얼 비디오

**산출물**:
- `cli/genos.py`: CLI 도구
- `docs/user-manual.md`: 사용자 매뉴얼
- `examples/`: 예제 프로젝트
- `README.md`: 프로젝트 소개

**Phase 1 완료 기준**:
- ✅ 실제 CircleMUD 1개 이상 완전 마이그레이션
- ✅ 변환 성공률 90% 이상
- ✅ 마이그레이션 소요 시간 10분 이내
- ✅ 생성된 GenOS 프로젝트가 플레이 가능

### 5.2 Phase 2: Expansion (3개월)

**목표**: 2개 추가 계열 지원 + GenOS 기능 확장

#### Month 4: LP-MUD Adapter

**Week 13-14**: LPC 파서
- [ ] LPC 언어 파서 (ANTLR 사용)
- [ ] 오브젝트 상속 구조 분석
- [ ] 함수 호출 그래프 생성

**Week 15-16**: UIR 변환 및 검증
- [ ] LP-MUD → UIR 변환
- [ ] CircleMUD와 다른 부분 처리
- [ ] UIR 스펙 개선 (v1.1)

**산출물**:
- `adapters/lpmud.py`
- `uir-spec-v1.1.md`: 개선된 스펙

#### Month 5: DikuMUD/ROM Adapter

**Week 17-18**: DikuMUD 파서
- [ ] CircleMUD 어댑터 재사용
- [ ] DikuMUD 특수 기능 처리
- [ ] ROM 확장 기능 지원

**Week 19-20**: 범용성 검증
- [ ] 3개 계열 모두 테스트
- [ ] UIR의 범용성 확인
- [ ] 부족한 부분 보완

**산출물**:
- `adapters/dikumud.py`
- `docs/supported-muds.md`: 지원 MUD 목록

#### Month 6: GenOS 기능 확장

**Week 21**: 웹 대시보드 (Phase 1)
- [ ] 프로젝트 대시보드
- [ ] 방 편집기 (스프레드시트)
- [ ] 아이템 편집기

**Week 22**: 비주얼 노드 에디터 (기본)
- [ ] React-flow 통합
- [ ] T-C-A 노드 15개
- [ ] 퀘스트 빌더

**Week 23**: Hot-swap 시스템
- [ ] Graceful reload 구현
- [ ] 플러그인 버전 관리
- [ ] 롤백 기능

**Week 24**: 모니터링 및 분석
- [ ] 실시간 접속자 수
- [ ] 성능 모니터링
- [ ] 에러 추적

**산출물**:
- `web/`: React 대시보드
- `genos/hotswap/`: Hot-swap 시스템
- `genos/monitoring/`: 모니터링

**Phase 2 완료 기준**:
- ✅ 3개 MUD 계열 지원
- ✅ 웹 대시보드 기본 기능
- ✅ Hot-swap 동작 확인

### 5.3 Phase 3: Polish & Release (2개월)

**목표**: 프로덕션 준비 + 커뮤니티 출시

#### Month 7: 안정화

**Week 25-26**: 성능 최적화
- [ ] DB 쿼리 최적화
- [ ] Lua 스크립트 캐싱
- [ ] WebSocket 성능 개선

**Week 27-28**: 보안 강화
- [ ] Lua 샌드박스 테스트
- [ ] SQL Injection 방지
- [ ] XSS 방어

**산출물**:
- 성능 벤치마크 리포트
- 보안 감사 리포트

#### Month 8: 출시 준비

**Week 29-30**: UX 개선
- [ ] 온보딩 튜토리얼
- [ ] 인앱 가이드
- [ ] 에러 메시지 개선

**Week 31-32**: 마케팅 자료
- [ ] 프로젝트 웹사이트
- [ ] 데모 비디오 (3분)
- [ ] 케이스 스터디 (실제 마이그레이션)
- [ ] 커뮤니티 포스팅 준비

**산출물**:
- 공식 웹사이트
- 홍보 자료
- 오픈소스 릴리스 준비

**Phase 3 완료 기준**:
- ✅ 1000 동접 부하 테스트 통과
- ✅ 보안 취약점 0개
- ✅ 사용자 매뉴얼 완성
- ✅ 오픈소스 라이선스 결정

### 5.4 Long-term Roadmap (Year 2+)

#### Q1 2027: 추가 계열 지원
- MUSH/MUX Adapter
- MOO Adapter
- Evennia Adapter (아이러니하지만 필요)

#### Q2 2027: AI 기반 파서
- GPT-4/Claude 통합
- 알려지지 않은 MUD 형식 자동 분석
- 70% 성공률 목표

#### Q3 2027: 플러그인 마켓플레이스
- 커뮤니티 플러그인 공유
- 리뷰 및 평가 시스템
- 수익 모델 (Premium Plugins)

#### Q4 2027: 모바일 지원
- iOS/Android 네이티브 앱
- 모바일 최적화 UI
- 푸시 알림

---

## 6. 상세 설계

### 6.1 Source Adapter 구현 가이드

#### 6.1.1 BaseAdapter 인터페이스

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    """마이그레이션 분석 결과"""
    total_entities: int
    auto_convertible: int
    manual_review_needed: int
    complexity_score: float  # 0.0 ~ 1.0
    estimated_time_minutes: int
    warnings: List[str]
    errors: List[str]

class BaseAdapter(ABC):
    """모든 MUD 어댑터의 기본 클래스"""
    
    def __init__(self, mud_path: str):
        self.mud_path = mud_path
        self.uir = UniversalIR()
        self.warnings = []
        self.errors = []
    
    @abstractmethod
    def detect_mud_type(self) -> bool:
        """
        해당 경로가 이 어댑터가 지원하는 MUD인지 감지
        
        Returns:
            bool: 지원 가능하면 True
        """
        pass
    
    @abstractmethod
    def analyze(self) -> AnalysisResult:
        """
        마이그레이션 전 분석
        - 변환 가능 여부
        - 복잡도 평가
        - 예상 소요 시간
        """
        pass
    
    @abstractmethod
    def parse(self) -> UniversalIR:
        """
        실제 변환 수행
        
        Returns:
            UniversalIR: 변환된 UIR 객체
        """
        pass
    
    def validate_uir(self, uir: UniversalIR) -> bool:
        """생성된 UIR의 유효성 검증"""
        # UIR 스키마 검증
        # 필수 필드 체크
        # 데이터 무결성 체크
        pass
```

#### 6.1.2 CircleMUD Adapter 상세 구현

```python
import re
import glob
from pathlib import Path

class CircleMudAdapter(BaseAdapter):
    """CircleMUD/tbaMUD 어댑터"""
    
    REQUIRED_DIRS = ['lib/world', 'lib/text', 'src']
    REQUIRED_FILES = ['lib/world/wld/*.wld', 'lib/world/obj/*.obj']
    
    def detect_mud_type(self) -> bool:
        """CircleMUD 구조 감지"""
        path = Path(self.mud_path)
        
        # 필수 디렉토리 확인
        for dir_name in self.REQUIRED_DIRS:
            if not (path / dir_name).exists():
                return False
        
        # 특징적인 파일 확인
        if (path / 'src' / 'structs.h').exists():
            with open(path / 'src' / 'structs.h') as f:
                content = f.read()
                # CircleMUD 특유의 구조체 확인
                if 'struct char_data' in content:
                    return True
        
        return False
    
    def analyze(self) -> AnalysisResult:
        """마이그레이션 분석"""
        result = AnalysisResult(
            total_entities=0,
            auto_convertible=0,
            manual_review_needed=0,
            complexity_score=0.0,
            estimated_time_minutes=0,
            warnings=[],
            errors=[]
        )
        
        # 방 파일 개수
        wld_files = glob.glob(f"{self.mud_path}/lib/world/wld/*.wld")
        room_count = sum(self._count_rooms(f) for f in wld_files)
        result.total_entities += room_count
        result.auto_convertible += room_count
        
        # 아이템 파일 개수
        obj_files = glob.glob(f"{self.mud_path}/lib/world/obj/*.obj")
        obj_count = sum(self._count_objects(f) for f in obj_files)
        result.total_entities += obj_count
        result.auto_convertible += obj_count
        
        # 소스 코드 복잡도 분석
        complexity = self._analyze_source_complexity()
        result.manual_review_needed = complexity['custom_commands']
        
        # 예상 시간 계산 (경험적 공식)
        result.estimated_time_minutes = (
            (room_count + obj_count) * 0.01 +  # 데이터 파일
            complexity['custom_commands'] * 5    # 커스텀 명령어
        )
        
        result.complexity_score = (
            result.manual_review_needed / result.total_entities
        )
        
        return result
    
    def parse(self) -> UniversalIR:
        """전체 파싱"""
        print("CircleMUD 파싱 시작...")
        
        # 1. 메타데이터
        self.uir.metadata = self._parse_metadata()
        
        # 2. 월드 파일 (방)
        print("  방 데이터 파싱 중...")
        self._parse_world_files()
        
        # 3. 오브젝트 파일 (아이템)
        print("  아이템 데이터 파싱 중...")
        self._parse_object_files()
        
        # 4. 모바일 파일 (몬스터)
        print("  몬스터 데이터 파싱 중...")
        self._parse_mobile_files()
        
        # 5. C 소스코드 (클래스, 전투 등)
        print("  소스코드 분석 중...")
        self._parse_source_code()
        
        # 6. 검증
        if not self.validate_uir(self.uir):
            raise ValueError("생성된 UIR이 유효하지 않습니다")
        
        print(f"파싱 완료: {len(self.uir.rooms)}개 방, "
              f"{len(self.uir.items)}개 아이템")
        
        return self.uir
    
    def _parse_world_files(self):
        """
        CircleMUD 월드 파일 형식 파싱
        
        형식:
        #3001
        숲 속 공터~
        햇살이 비치는 작은 공터입니다.
        ~
        0 0 2
        D0
        ~
        ~
        0 0 3002
        """
        wld_files = glob.glob(f"{self.mud_path}/lib/world/wld/*.wld")
        
        for wld_file in wld_files:
            with open(wld_file, encoding='latin-1') as f:
                content = f.read()
            
            # 정규표현식으로 방 블록 분리
            room_pattern = r'#(\d+)\n(.+?)(?=#\d+|\Z)'
            rooms = re.findall(room_pattern, content, re.DOTALL)
            
            for vnum, room_data in rooms:
                try:
                    room = self._parse_room_block(vnum, room_data)
                    self.uir.rooms.append(room)
                except Exception as e:
                    self.warnings.append(
                        f"방 #{vnum} 파싱 실패: {str(e)}"
                    )
    
    def _parse_room_block(self, vnum: str, data: str) -> dict:
        """개별 방 블록 파싱"""
        lines = data.strip().split('\n')
        
        # 첫 줄: 방 이름 (~ 까지)
        name_line = lines[0]
        name = name_line.split('~')[0].strip()
        
        # 설명 (여러 줄, ~ 까지)
        desc_start = 1
        desc_lines = []
        for i, line in enumerate(lines[desc_start:], desc_start):
            if '~' in line:
                desc_lines.append(line.split('~')[0])
                break
            desc_lines.append(line)
        
        description = '\n'.join(desc_lines).strip()
        
        # 다음 줄: zone flags sector
        # 예: 0 0 2 (zone=0, flags=0, sector=2)
        
        # 출구 파싱 (D0, D1...)
        # D0 = 북쪽, D1 = 동쪽, D2 = 남쪽, D3 = 서쪽
        exits = {}
        
        return {
            'id': vnum,
            'name': name,
            'description': description,
            'exits': exits,
            'sector_type': self._map_sector_type(2),  # 예시
            'source_metadata': {
                'source_file': Path(wld_file).name,
                'original_vnum': vnum
            }
        }
    
    def _parse_source_code(self):
        """C 소스코드 분석"""
        # class.c에서 클래스 정의 추출
        class_file = Path(self.mud_path) / 'src' / 'class.c'
        
        if class_file.exists():
            self._parse_class_definitions(class_file)
        
        # fight.c에서 전투 시스템 분석
        fight_file = Path(self.mud_path) / 'src' / 'fight.c'
        
        if fight_file.exists():
            self._parse_combat_system(fight_file)
    
    def _parse_class_definitions(self, class_file: Path):
        """클래스 정의 추출"""
        # 이 부분은 pycparser 등을 사용하여 AST 분석
        # 또는 정규표현식으로 패턴 매칭
        
        with open(class_file) as f:
            content = f.read()
        
        # 예: init_warrior() 함수 찾기
        pattern = r'void\s+init_(\w+)\s*\([^)]*\)\s*{([^}]*)}'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for class_name, func_body in matches:
            stats = self._extract_stat_assignments(func_body)
            
            self.uir.character_classes.append({
                'id': class_name.lower(),
                'name': class_name.capitalize(),
                'starting_stats': stats,
                'source_metadata': {
                    'source_file': 'class.c',
                    'source_function': f'init_{class_name}()'
                }
            })
```

### 6.2 GenOS Compiler 상세 설계

#### 6.2.1 DB Schema Generator

```python
class DbSchemaGenerator:
    """UIR → PostgreSQL 스키마 생성"""
    
    def generate(self, uir: UniversalIR) -> str:
        """전체 스키마 SQL 생성"""
        sql = []
        
        game_id = uir.metadata.game_id
        
        # 1. 게임별 독립 스키마
        sql.append(f"CREATE SCHEMA IF NOT EXISTS game_{game_id};")
        sql.append(f"SET search_path TO game_{game_id};")
        
        # 2. 핵심 테이블
        sql.extend(self._create_core_tables())
        
        # 3. 클래스 시스템
        if uir.character_classes:
            sql.extend(self._create_class_tables(uir))
        
        # 4. 아이템 시스템
        if uir.items:
            sql.extend(self._create_item_tables(uir))
        
        # 5. 데이터 삽입
        sql.extend(self._insert_seed_data(uir))
        
        return '\n'.join(sql)
    
    def _create_core_tables(self) -> List[str]:
        """핵심 테이블 생성"""
        return [
            """
            CREATE TABLE accounts (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE characters (
                id SERIAL PRIMARY KEY,
                account_id INT REFERENCES accounts(id),
                name VARCHAR(50) UNIQUE NOT NULL,
                class_id VARCHAR(50),
                
                -- 기본 스탯 (정적 컬럼)
                level INT DEFAULT 1,
                exp INT DEFAULT 0,
                hp INT NOT NULL,
                max_hp INT NOT NULL,
                mp INT NOT NULL,
                max_mp INT NOT NULL,
                
                -- 커스텀 데이터 (JSONB)
                custom_stats JSONB DEFAULT '{}',
                
                -- 위치
                current_room_id VARCHAR(50),
                
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE rooms (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                sector_type VARCHAR(50),
                exits JSONB DEFAULT '{}',
                flags JSONB DEFAULT '[]'
            );
            """
        ]
    
    def _create_class_tables(self, uir: UniversalIR) -> List[str]:
        """클래스 시스템 테이블"""
        
        # 클래스별 스탯 분석
        all_stats = set()
        for cls in uir.character_classes:
            all_stats.update(cls['starting_stats'].keys())
        
        # 동적으로 컬럼 생성
        stat_columns = [
            f"{stat} INT DEFAULT 0" 
            for stat in all_stats
        ]
        
        return [
            f"""
            CREATE TABLE classes (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                
                -- 시작 스탯
                {', '.join(stat_columns)},
                
                -- 추가 데이터
                starting_items JSONB DEFAULT '[]',
                starting_skills JSONB DEFAULT '[]',
                
                custom_data JSONB DEFAULT '{}'
            );
            """
        ]
```

#### 6.2.2 Lua Script Generator

```python
class LuaScriptGenerator:
    """복잡한 로직을 Lua 스크립트로 변환"""
    
    def generate_combat_script(self, combat_system: dict) -> str:
        """전투 시스템 Lua 코드 생성"""
        
        if combat_system.get('custom_combat_script'):
            # 이미 Lua 코드가 있으면 그대로 사용
            return combat_system['custom_combat_script']
        
        # UIR의 전투 정의를 Lua로 변환
        template = """
-- 자동 생성된 전투 스크립트
-- Generated from UIR combat_system

function calculate_damage(attacker, defender, weapon)
    -- 기본 데미지
    local base = {damage_formula}
    
    -- 크리티컬 판정
    local crit_chance = {crit_chance}
    if math.random(100) < crit_chance then
        base = base * {crit_multiplier}
        send_message(attacker, "치명타!")
    end
    
    -- 회피 판정
    local dodge_chance = {dodge_chance}
    if math.random(100) < dodge_chance then
        send_message(defender, "공격을 회피했다!")
        return 0
    end
    
    return math.max(1, base)  -- 최소 1 데미지
end

function do_combat_round(attacker, defender)
    local weapon = get_equipped_weapon(attacker)
    local damage = calculate_damage(attacker, defender, weapon)
    
    apply_damage(defender, damage)
    
    send_message(attacker, 
        string.format("당신은 %s에게 %d의 데미지를 입혔다!", 
                      defender.name, damage))
    send_message(defender,
        string.format("%s이(가) 당신에게 %d의 데미지를 입혔다!",
                      attacker.name, damage))
    
    if defender.hp <= 0 then
        on_character_death(defender, attacker)
    end
end
        """
        
        # 템플릿에 값 삽입
        return template.format(
            damage_formula=combat_system['damage_calculation']['base_formula'],
            crit_chance=combat_system['damage_calculation']['critical']['chance_formula'],
            crit_multiplier=combat_system['damage_calculation']['critical']['multiplier'],
            dodge_chance=combat_system['damage_calculation']['dodge']['chance_formula']
        )
```

### 6.3 Hot-swap 시스템 설계

```python
class PluginManager:
    """플러그인 Hot-swap 관리"""
    
    def __init__(self):
        self.plugins = {}  # plugin_id → plugin_instance
        self.routing_table = {}  # plugin_id → version
        self.draining_instances = {}  # old instances
    
    def reload_plugin(self, plugin_id: str, new_code: str):
        """플러그인 무중단 재시작"""
        
        # Phase 1: 새 버전 로드
        new_instance = self._load_plugin_code(new_code)
        new_version = f"{plugin_id}_v{int(time.time())}"
        
        # Phase 2: 라우팅 테이블 업데이트 (신규 요청은 새 버전으로)
        old_version = self.routing_table.get(plugin_id)
        self.routing_table[plugin_id] = new_version
        self.plugins[new_version] = new_instance
        
        # Phase 3: 구버전 Draining
        if old_version:
            old_instance = self.plugins[old_version]
            self.draining_instances[old_version] = {
                'instance': old_instance,
                'started_at': time.time(),
                'max_wait_seconds': 30
            }
            
            # 백그라운드에서 대기
            asyncio.create_task(
                self._wait_and_cleanup(old_version)
            )
    
    async def _wait_and_cleanup(self, old_version: str):
        """구버전 정리 대기"""
        drain_info = self.draining_instances[old_version]
        old_instance = drain_info['instance']
        
        # 최대 30초 대기
        for _ in range(30):
            if old_instance.active_requests == 0:
                # 모든 요청 완료
                break
            await asyncio.sleep(1)
        
        # 강제 정리
        if old_instance.active_requests > 0:
            logger.warning(
                f"{old_version} 강제 종료: "
                f"{old_instance.active_requests}개 요청 진행 중"
            )
        
        # 메모리 정리
        old_instance.cleanup()
        del self.plugins[old_version]
        del self.draining_instances[old_version]
        
        logger.info(f"{old_version} 정리 완료")
```

---

## 7. 위험 요소 및 대응

### 7.1 기술적 위험

#### 위험 1: UIR 범용성 부족
**시나리오**: 특정 MUD 계열의 고유 기능을 UIR로 표현 불가

**대응**:
- `extensions` 필드로 계열별 특수 데이터 보존
- UIR 스펙은 지속적 개선 (v1.0 → v1.1 → ...)
- 100% 완벽한 변환보다 80% 실용적 변환 목표

#### 위험 2: 마이그레이션 성공률 저조
**시나리오**: 자동 변환 성공률이 50% 미만

**대응**:
- Phase 1에서 CircleMUD 하나만 완벽히 지원
- 90% 성공률 달성 전까지 다음 계열 확장 안 함
- 실패 시 수동 보완 도구 제공

#### 위험 3: 성능 문제
**시나리오**: JSONB 기반 하이브리드 모델이 느림

**대응**:
- 초기부터 벤치마크 (1000 동접 목표)
- 문제 발견 시 필드 승격 시스템 활용
- 최악의 경우 정적 컬럼 위주로 회귀

### 7.2 프로젝트 관리 위험

#### 위험 4: 개발 범위 폭발
**시나리오**: 모든 MUD 계열 지원하려다 끝나지 않음

**완화**:
- Phase별 명확한 완료 기준
- Phase 1 실패 시 프로젝트 중단 (sunk cost 방지)
- 2-3개 계열만 지원해도 충분한 가치

#### 위험 5: 커뮤니티 반응 부정적
**시나리오**: MUD 운영자들이 GenOS에 관심 없음

**완화**:
- Phase 1 완료 후 즉시 커뮤니티 공개
- 조기 피드백 수집 (Reddit, Discord)
- 방향 전환 옵션 준비 (교육용, 인터랙티브 픽션 등)

### 7.3 시장 위험

#### 위험 6: MUD 시장 너무 작음
**시나리오**: 사용자 100명도 안 모임

**인정 및 대응**:
- 이건 사실일 가능성 높음 (니치 시장)
- 수익화보다 포트폴리오/학습 목적
- 기술은 다른 분야 적용 가능 (챗봇, 게임 에디터 등)

#### 위험 7: 경쟁 프로젝트 등장
**시나리오**: Evennia가 마이그레이션 도구 개발

**대응**:
- 선점 효과 (빠른 출시)
- 차별화된 기능 (웹 대시보드, Hot-swap)
- 오픈소스로 커뮤니티 선점

---

## 8. 성공 지표

### 8.1 Phase 1 성공 기준 (필수)

- ✅ CircleMUD 1개 이상 완전 마이그레이션 성공
- ✅ 변환 성공률 90% 이상
- ✅ 마이그레이션 소요 시간 10분 이내
- ✅ 생성된 GenOS 프로젝트가 실제 플레이 가능
- ✅ 문서화 완료 (사용자 매뉴얼, 개발자 문서)

### 8.2 Phase 2 성공 기준 (목표)

- ✅ 3개 MUD 계열 지원 (CircleMUD, LP-MUD, DikuMUD)
- ✅ 웹 대시보드 기본 기능 동작
- ✅ Hot-swap 시연 가능
- ✅ 각 계열별 성공 사례 1개씩

### 8.3 커뮤니티 성공 지표 (희망)

**6개월 후**:
- GitHub Stars: 100+
- 실제 마이그레이션 완료: 10+ 서버
- 커뮤니티 기여자: 5+ 명

**1년 후**:
- 활성 사용자: 50+ 명
- 지원 MUD 계열: 5+
- 플러그인 마켓플레이스 출시

---

## 9. 부록

### 9.1 참고 자료

#### MUD 엔진
- CircleMUD: https://www.circlemud.org/
- tbaMUD: https://www.tbamud.com/
- Evennia: https://www.evennia.com/
- LP-MUD: http://www.bearnip.com/lars/proj/lpmud.html

#### 기술 스택
- PostgreSQL JSONB: https://www.postgresql.org/docs/current/datatype-json.html
- Lupa (Lua in Python): https://github.com/scoder/lupa
- React-flow: https://reactflow.dev/

#### 관련 커뮤니티
- Reddit r/MUD: https://www.reddit.com/r/MUD/
- MUD Connector: https://www.mudconnect.com/
- TopMUDSites: https://www.topmudsites.com/

### 9.2 용어 정의

- **MUD**: Multi-User Dungeon, 텍스트 기반 멀티플레이어 게임
- **UIR**: Universal Intermediate Representation, 범용 중간 표현
- **Hot-swap**: 서버 재시작 없이 코드 교체
- **Draining**: 구버전 요청을 정상 처리 후 종료하는 방식
- **Live Ops**: 게임 운영 중 실시간 관리 및 수정

### 9.3 연락처

- 프로젝트 리드: 누렁이
- GitHub: (TBD)
- Discord: (TBD)
- Email: (TBD)

---

## 마치며

이 문서는 GenOS 프로젝트의 **마스터 플랜**입니다. 

핵심 전략은 **"범용 MUD 마이그레이션"**이며, 이를 통해:
1. 기존 MUD 운영자에게 즉각적 가치 제공
2. 전체 MUD 커뮤니티를 하나의 플랫폼으로 통합
3. 산업 표준 플랫폼으로 자리매김

**현실적 접근**:
- 완벽한 범용성보다 실용적인 80/20
- 특정 계열 하나씩 완벽히 지원
- 단계적 확장으로 위험 최소화

**장기 비전**:
- "MUD 만들면 GenOS"
- 플러그인 마켓플레이스 생태계
- 텍스트 게임 전반으로 확장

---

**버전 관리**:
- v2.0 (2026-02-09): 범용 마이그레이션 전략 확정
- v1.1 (2026-02-08): 하이브리드 모델, Hot-swap 설계
- v1.0 (2026-02-07): 초기 기획

**다음 액션**:
1. UIR 스펙 v1.0 작성 시작
2. CircleMUD 샘플 다운로드 및 분석
3. BaseAdapter 인터페이스 구현
4. 첫 번째 방 파싱 성공 🎯
