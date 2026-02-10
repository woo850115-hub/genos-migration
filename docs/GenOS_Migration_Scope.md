# GenOS 마이그레이션 범위 및 전략
**Universal MUD Migration Scope Definition**

Version: 1.0  
Last Updated: 2026-02-10  
Author: 누렁이

---

## 📋 목차

1. [개요](#개요)
2. [마이그레이션 범위 전체 목록](#마이그레이션-범위-전체-목록)
3. [우선순위별 분류](#우선순위별-분류)
4. [항목별 상세 가이드](#항목별-상세-가이드)
5. [특수 항목 처리 전략](#특수-항목-처리-전략)
6. [Phase별 구현 계획](#phase별-구현-계획)
7. [제외 항목 및 이유](#제외-항목-및-이유)

---

## 개요

### 기본 원칙

**포함 기준**:
1. ✅ 모든 MUD에 공통적으로 존재
2. ✅ 데이터 중심 (로직이 단순)
3. ✅ 자동/반자동 변환 가능
4. ✅ 게임 플레이에 필수

**제외 기준**:
1. ❌ MUD별로 너무 다름
2. ❌ 복잡한 로직 (재구현 필요)
3. ❌ 실시간 데이터 (초기화 가능)
4. ❌ 관리자 전용 기능

### 마이그레이션 타입

```
[자동] Auto Migration
- 100% 자동 변환
- 데이터 추출 → UIR 변환
- 예: Rooms, Items (기본 속성)

[반자동] Semi-Auto Migration
- 데이터 추출은 자동
- 로직은 템플릿 적용
- 예: Shops, Simple Quests

[수동] Manual Migration
- 데이터만 추출
- 로직은 재구현 필요
- 예: Complex Triggers, Special Procedures

[제외] Not Migrated
- 마이그레이션 안 함
- GenOS에서 새로 시작
- 예: Player Data, Admin Tools
```

---

## 마이그레이션 범위 전체 목록

### 1. 월드 구조 (World Structure)

#### 1.1 Rooms (방/지역)
**우선순위**: P0 (필수)  
**복잡도**: ⭐⭐ (중간)  
**마이그레이션 타입**: 자동

**포함 데이터**:
- 방 ID, 이름, 설명
- 출구 정보 (방향, 문, 열쇠)
- 지형 타입 (실내, 숲, 물 등)
- 플래그 (평화 지역, 마법 금지 등)
- ANSI 색상 코드

**UIR 구조**:
```yaml
rooms:
  - id: "3001"
    name: "숲 속 공터"
    description: "햇살이 비치는..."
    exits:
      north: 
        target_room_id: "3000"
        door: null
      south:
        target_room_id: "3002"
        door:
          name: "낡은 문"
          key_id: "rusty_key"
          locked: true
    sector_type: "forest"
    flags: ["peaceful", "no_magic"]
```

**변환 난이도**:
- CircleMUD: ⭐ (쉬움) - 정규표현식
- LP-MUD: ⭐⭐ (중간) - LPC 파서
- MUSH: ⭐⭐⭐ (어려움) - 복잡한 속성 시스템

---

#### 1.2 Zones (지역/구역)
**우선순위**: P0 (필수)  
**복잡도**: ⭐⭐ (중간)  
**마이그레이션 타입**: 자동

**포함 데이터**:
- Zone ID, 이름
- 방 범위 (예: 3000-3099)
- 리셋 시간 (몬스터/아이템 재생성)
- Zone 명령어 (문 열기, 몬스터 스폰 등)

**UIR 구조**:
```yaml
zones:
  - id: "30"
    name: "초보자 숲"
    room_range: [3000, 3099]
    reset_interval_minutes: 5
    
    reset_commands:
      - type: "spawn_mobile"
        mobile_id: "goblin_scout"
        room_id: "3010"
        max_count: 3
      
      - type: "load_object"
        object_id: "rusty_sword"
        room_id: "3001"
        max_count: 1
      
      - type: "equip_mobile"
        mobile_id: "goblin_chief"
        object_id: "iron_helmet"
        wear_slot: "head"
```

**특수 처리**:
- Zone 명령어는 GenOS 스크립트로 변환
- 복잡한 리셋 로직은 Lua로

---

#### 1.3 Items (아이템/오브젝트)
**우선순위**: P0 (필수)  
**복잡도**: ⭐⭐ (중간)  
**마이그레이션 타입**: 자동

**포함 데이터**:
- 아이템 ID, 이름, 별칭
- 설명 (짧은/긴/바닥)
- 타입 (무기, 방어구, 소모품 등)
- 스탯 (데미지, 방어력, 무게 등)
- 플래그 (주울 수 있음, 착용 가능 등)
- 특수 효과 (스탯 보너스, 버프 등)

**UIR 구조**:
```yaml
items:
  - id: "rusty_sword"
    name: "녹슨 검"
    aliases: ["sword", "검"]
    
    description:
      short: "녹슨 검"
      long: "오랜 세월 방치되어 녹이 슨 검입니다."
      on_ground: "녹슨 검이 바닥에 놓여있습니다."
    
    item_type: "weapon"
    
    stats:
      damage_dice: "1d6+2"
      weight: 3.5
      value: 10
    
    flags: ["takeable", "wieldable"]
    wear_slots: ["weapon"]
    
    equip_effects:
      - type: "stat_modifier"
        stat: "str"
        value: 1
```

**아이템 타입별 복잡도**:
- 일반 아이템: ⭐ (쉬움)
- 무기/방어구: ⭐⭐ (중간)
- 컨테이너: ⭐⭐ (중간)
- 소모품/포션: ⭐⭐⭐ (어려움 - 효과 로직)
- 특수 아이템: ⭐⭐⭐⭐ (매우 어려움 - 커스텀 로직)

---

#### 1.4 Monsters/NPCs (몬스터/NPC)
**우선순위**: P0 (필수)  
**복잡도**: ⭐⭐⭐ (어려움)  
**마이그레이션 타입**: 반자동

**포함 데이터**:
- 몬스터 ID, 이름, 별칭
- 설명
- 스탯 (레벨, HP, 공격력 등)
- AI 타입 (공격적, 수동적 등)
- 전투 정보
- 드랍 테이블
- 대화 (NPC)

**UIR 구조**:
```yaml
monsters:
  - id: "goblin_scout"
    name: "고블린 정찰병"
    
    stats:
      level: 3
      hp: 30
      ac: 15
      damage_dice: "1d4+1"
    
    ai_type: "aggressive"
    behavior:
      aggro_range: 2
      flee_hp_percent: 20
      call_for_help: true
    
    loot_table:
      - item_id: "gold"
        quantity_range: [1, 5]
        drop_chance: 1.0
      - item_id: "goblin_ear"
        quantity_range: [1, 1]
        drop_chance: 0.5
    
    exp_reward: 50
```

**복잡도 증가 요인**:
- 기본 몬스터: ⭐⭐
- AI 행동 패턴: ⭐⭐⭐
- 특수 능력: ⭐⭐⭐⭐
- 대화/퀘스트 NPC: ⭐⭐⭐⭐⭐

---

### 2. 캐릭터 시스템 (Character System)

#### 2.1 Character Classes (직업)
**우선순위**: P0 (필수!)  
**복잡도**: ⭐⭐⭐ (어려움)  
**마이그레이션 타입**: 반자동

**포함 데이터**:
- 직업 ID, 이름
- 시작 스탯
- 레벨업 스탯 증가
- 착용 가능 장비
- 사용 가능 스킬
- 제한사항

**UIR 구조**:
```yaml
character_classes:
  - id: "warrior"
    name: "전사"
    description: "강력한 체력과 물리 공격력"
    
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
      stat_points_per_level: 1
    
    starting_equipment:
      - item_id: "rusty_sword"
        slot: "weapon"
        auto_equip: true
    
    starting_skills:
      - skill_id: "bash"
        level: 1
    
    restrictions:
      allowed_races: ["human", "dwarf", "orc"]
```

**주의사항**:
- 레벨업 공식이 복잡하면 Lua 스크립트로
- HP/MP 계산식 검증 필요
- 멀티클래스는 별도 처리

---

#### 2.2 Races (종족)
**우선순위**: P1 (있으면 필수)  
**복잡도**: ⭐ (쉬움)  
**마이그레이션 타입**: 자동

**포함 데이터**:
- 종족 ID, 이름
- 스탯 보너스/페널티
- 크기
- 종족 특수 능력
- 직업 제한

**UIR 구조**:
```yaml
races:
  - id: "human"
    name: "인간"
    
    stat_modifiers:
      str: 0
      int: 0
      # 인간은 보통 보너스 없음
    
    size: "medium"
    
    racial_abilities: []
    
    allowed_classes: ["warrior", "mage", "cleric", "rogue"]
  
  - id: "elf"
    name: "엘프"
    
    stat_modifiers:
      dex: 2
      con: -1
    
    size: "medium"
    
    racial_abilities:
      - "infravision"  # 어둠에서 볼 수 있음
    
    allowed_classes: ["mage", "rogue"]
    prohibited_classes: ["warrior"]
```

**처리 방법**:
- 종족이 없는 MUD는 건너뛰기
- 있으면 필수 마이그레이션

---

### 3. 게임 시스템 (Game Systems)

#### 3.1 Shops (상점)
**우선순위**: P1 (중요)  
**복잡도**: ⭐⭐ (중간)  
**마이그레이션 타입**: 반자동

**포함 데이터**:
- 상점 ID
- 판매 아이템 목록
- 가격 배율
- 거래 가능 아이템 타입
- 영업 시간
- 상점 주인 (NPC)

**UIR 구조**:
```yaml
shops:
  - id: "weapon_shop_midgaard"
    name: "무기 상점"
    shopkeeper_mobile_id: "shopkeeper_3001"
    room_id: "3001"
    
    sells:
      - item_id: "short_sword"
        unlimited: false
        stock: 5
      - item_id: "long_sword"
        unlimited: true
    
    buys_types: ["weapon", "armor"]
    
    price_multipliers:
      sell_to_player: 1.2  # 120% 가격에 판매
      buy_from_player: 0.5 # 50% 가격에 매입
    
    open_hours:
      start: 6  # 오전 6시
      end: 22   # 오후 10시
```

---

#### 3.2 Triggers (트리거)
**우선순위**: P1 (중요)  
**복잡도**: ⭐⭐⭐⭐ (매우 어려움)  
**마이그레이션 타입**: 수동

**포함 데이터**:
- 트리거 조건
- 실행 액션
- 첨부 대상 (방, 몬스터, 아이템)

**UIR 구조**:
```yaml
triggers:
  - id: "trap_trigger_3010"
    name: "함정 방 트리거"
    
    trigger_type: "on_enter_room"
    
    conditions:
      - type: "random_chance"
        chance: 0.3  # 30% 확률
    
    actions:
      - type: "damage_player"
        damage: "2d6"
        message: "바닥의 함정이 작동합니다!"
      
      - type: "broadcast_room"
        message: "{player_name}이(가) 함정을 밟았습니다!"
    
    attached_to:
      type: "room"
      room_id: "3010"
```

**처리 전략**:
- 간단한 트리거: 템플릿 적용
- 복잡한 트리거: Lua 스크립트로
- 매우 복잡한 트리거: 수동 재구현

---

#### 3.3 Quests (퀘스트)
**우선순위**: P1 (중요)  
**복잡도**: ⭐⭐⭐⭐ (매우 어려움)  
**마이그레이션 타입**: 수동

**포함 데이터**:
- 퀘스트 ID, 이름, 설명
- 목표 (몬스터 처치, 아이템 수집 등)
- 보상
- 전제 조건
- 분기

**UIR 구조**:
```yaml
quests:
  - id: "goblin_subjugation"
    name: "고블린 토벌"
    description: "고블린 10마리를 처치하라"
    
    quest_giver_npc: "village_elder"
    
    objectives:
      - type: "kill_monster"
        monster_id: "goblin_scout"
        count: 10
    
    rewards:
      exp: 500
      gold: 100
      items:
        - "iron_sword"
    
    prerequisites:
      min_level: 3
      completed_quests: []
```

**복잡도별 처리**:
- 단순 퀘스트 (kill/collect): 반자동
- 다단계 퀘스트: 수동
- 분기 퀘스트: 수동
- 타이머 퀘스트: 수동

---

#### 3.4 Skills (스킬) - 메타데이터만
**우선순위**: P2 (중요하지만 로직 제외)  
**복잡도**: ⭐⭐ (데이터만)  
**마이그레이션 타입**: 데이터만 자동, 로직 재구현

**포함 데이터**:
- 스킬 ID, 이름, 설명
- 마나/스태미나 소모
- 쿨다운
- 최소 레벨 (직업별)
- 타겟 타입
- 속성

**UIR 구조**:
```yaml
skills:
  - id: "fireball"
    name: "화염구"
    type: "spell"
    
    metadata:
      description: "불타는 화염구를 발사"
      mana_cost: 25
      cooldown_seconds: 3
      
      min_level:
        warrior: null
        mage: 5
        cleric: null
      
      target_type: "single_enemy"
      range: 3
      element: "fire"
    
    # 로직은 재구현
    implementation:
      type: "not_migrated"
      
      # 간단한 경우 템플릿 힌트
      template_hint: "single_target_damage"
      suggested_config:
        base_damage: "2d6"
        damage_stat: "int"
    
    # 원본 보존
    source_metadata:
      source_file: "spell_parser.c"
      function_name: "spell_fireball"
```

---

#### 3.5 Commands (명령어) - 목록만
**우선순위**: P2 (목록만)  
**복잡도**: ⭐⭐⭐ (분석만)  
**마이그레이션 타입**: 목록 추출, 로직 재구현

**포함 데이터**:
- 명령어 이름, 별칭
- 도움말 텍스트
- 필요 레벨
- 카테고리

**UIR 구조**:
```yaml
custom_commands:
  - name: "auction"
    aliases: ["경매", "auc"]
    category: "commerce"
    
    help_text: |
      사용법: auction <아이템> <시작가>
      아이템을 경매에 올립니다.
    
    min_level: 5
    
    # 로직은 보존만
    implementation:
      type: "not_migrated"
      complexity: "high"
      
    source_metadata:
      source_file: "act.item.c"
      function_name: "do_auction"
      lines_of_code: 523
```

---

### 4. 소셜/커뮤니케이션 (Social/Communication)

#### 4.1 Socials (감정 표현)
**우선순위**: P2 (쉽고 가치 높음)  
**복잡도**: ⭐ (매우 쉬움)  
**마이그레이션 타입**: 자동

**포함 데이터**:
- 명령어 이름
- 메시지 (타겟 없음, 타겟 있음, 자신에게)

**UIR 구조**:
```yaml
socials:
  - command: "smile"
    aliases: ["미소"]
    
    messages:
      no_target:
        to_char: "당신은 미소 짓습니다."
        to_room: "{char}이(가) 미소 짓습니다."
      
      with_target:
        to_char: "당신은 {target}에게 미소 짓습니다."
        to_target: "{char}이(가) 당신에게 미소 짓습니다."
        to_room: "{char}이(가) {target}에게 미소 짓습니다."
      
      self_target:
        to_char: "당신은 혼자 히죽거립니다."
        to_room: "{char}이(가) 혼자 히죽거립니다."
```

**변환 방법**:
- CircleMUD: 텍스트 파일 파싱
- 변수 치환 (`$n` → `{char}`, `$N` → `{target}`)

---

#### 4.2 Help System (도움말)
**우선순위**: P2 (필수지만 나중에)  
**복잡도**: ⭐ (쉬움, 하지만 많음)  
**마이그레이션 타입**: 자동

**포함 데이터**:
- 키워드 목록
- 도움말 텍스트
- 최소 레벨

**UIR 구조**:
```yaml
help_entries:
  - keywords: ["look", "l", "보기"]
    level: 0
    text: |
      사용법: look [대상]
      
      주변을 둘러봅니다.
      
      예시:
        look        - 방 전체
        look north  - 북쪽 출구
```

---

### 5. 게임 메카닉스 (Game Mechanics)

#### 5.1 Faction/Alignment System (진영/성향)
**우선순위**: P2 (있으면 중요)  
**복잡도**: ⭐⭐⭐ (복잡함)  
**마이그레이션 타입**: 반자동

**포함 데이터**:
- 진영 정의
- 평판 범위
- NPC 반응 규칙

**UIR 구조**:
```yaml
alignment_system:
  type: "simple"  # simple, faction_based
  
  alignments:
    - id: "good"
      name: "선"
      range: [1000, 350]
    
    - id: "neutral"
      name: "중립"
      range: [349, -349]
    
    - id: "evil"
      name: "악"
      range: [-350, -1000]

# 또는 복잡한 다진영
faction_system:
  factions:
    - id: "townguard"
      name: "마을 수비대"
      
      reputation_levels:
        ally: [1000, 750]
        friendly: [749, 250]
        neutral: [249, -249]
        hostile: [-250, -1000]
```

---

#### 5.2 Combat System (전투 시스템)
**우선순위**: P1 (중요, 하지만 복잡)  
**복잡도**: ⭐⭐⭐⭐⭐ (매우 어려움)  
**마이그레이션 타입**: 수동

**포함 데이터**:
- 전투 타입 (턴제/실시간)
- 데미지 공식
- 크리티컬/회피 규칙
- 속성 시스템

**UIR 구조**:
```yaml
combat_system:
  type: "turn_based"
  
  damage_calculation:
    base_formula: "weapon_damage + str_bonus - target_ac"
    
    critical:
      chance_formula: "dex / 10"
      multiplier: 2.0
    
    dodge:
      chance_formula: "target_dex / 5"
  
  # 복잡한 로직은 스크립트로
  custom_combat_script: |
    function calculate_damage(attacker, defender)
      -- Lua implementation
    end
```

---

### 6. 부가 시스템 (Additional Systems)

#### 6.1 Title System (칭호)
**우선순위**: P3 (Nice to have)  
**복잡도**: ⭐⭐ (중간)  
**마이그레이션 타입**: 자동

```yaml
titles:
  level_titles:
    warrior:
      1: "초보 전사"
      10: "숙련된 전사"
  
  achievement_titles:
    - id: "dragon_slayer"
      name: "용 도살자"
      condition: "killed_dragon >= 1"
```

---

#### 6.2 Weather/Time System (날씨/시간)
**우선순위**: P4 (참고만)  
**복잡도**: ⭐ (쉬움)  
**마이그레이션 타입**: 설정만

```yaml
world_settings:
  time_system:
    hours_per_day: 24
    current_time:
      year: 1234
      month: 5
      day: 15
  
  weather_system:
    enabled: true
```

---

#### 6.3 Special Procedures (특수 프로시저)
**우선순위**: P3 (목록만)  
**복잡도**: ⭐⭐⭐⭐⭐ (매우 어려움)  
**마이그레이션 타입**: 수동

```yaml
special_procedures:
  - id: "guild_guard"
    name: "길드 가드"
    
    # 원본 보존
    source_code: |
      SPECIAL(guild_guard) {
        // C code
      }
    
    # 재구현 가이드
    migration_guide: |
      GenOS 플러그인으로 재구현 권장.
      핵심 로직: 특정 클래스만 통과
```

---

## 우선순위별 분류

### P0 - 필수 (게임 불가능)

| 항목 | 복잡도 | 마이그레이션 타입 |
|------|--------|-------------------|
| Rooms | ⭐⭐ | 자동 |
| Items | ⭐⭐ | 자동 |
| Monsters | ⭐⭐⭐ | 반자동 |
| Zones | ⭐⭐ | 자동 |
| Classes | ⭐⭐⭐ | 반자동 |

**총 예상 시간**: 2-3주

---

### P1 - 중요 (경험 저하)

| 항목 | 복잡도 | 마이그레이션 타입 |
|------|--------|-------------------|
| Races | ⭐ | 자동 |
| Shops | ⭐⭐ | 반자동 |
| Triggers | ⭐⭐⭐⭐ | 수동 |
| Quests | ⭐⭐⭐⭐ | 수동 |
| Combat System | ⭐⭐⭐⭐⭐ | 수동 |

**총 예상 시간**: 3-4주

---

### P2 - 가치 있음

| 항목 | 복잡도 | 마이그레이션 타입 |
|------|--------|-------------------|
| Socials | ⭐ | 자동 |
| Help | ⭐ | 자동 |
| Skills (data) | ⭐⭐ | 데이터만 |
| Commands (list) | ⭐⭐⭐ | 목록만 |
| Factions | ⭐⭐⭐ | 반자동 |

**총 예상 시간**: 1-2주

---

### P3-P4 - 선택/참고

| 항목 | 복잡도 | 마이그레이션 타입 |
|------|--------|-------------------|
| Titles | ⭐⭐ | 자동 |
| Weather/Time | ⭐ | 설정만 |
| Special Procs | ⭐⭐⭐⭐⭐ | 목록만 |
| Crafting | ⭐⭐⭐⭐ | 제외 |

**총 예상 시간**: 1주

---

## 특수 항목 처리 전략

### ANSI 색상 코드

**문제**: 각 MUD마다 다른 색상 코드 형식

**해결책**: UIR Color Markup

```yaml
# 모든 MUD 형식 → UIR
CircleMUD: &r빨강&n
DikuMUD:   {r빨강{x
LP-MUD:    %^RED%^빨강%^RESET%^

↓ 변환 ↓

UIR:       {{color:red}}빨강{{reset}}

↓ 렌더링 ↓

ANSI:      \033[31m빨강\033[0m
HTML:      <span style="color:#ff0000">빨강</span>
```

**구현**: 각 어댑터가 변환 책임

---

### 명령어 (Commands)

**전략**: 3-Tier 접근

```
Tier 1: 기본 명령어 (GenOS 제공)
- look, say, get, drop, kill 등
- 마이그레이션 불필요

Tier 2: 템플릿 명령어 (반자동)
- 패턴 감지 → 템플릿 적용
- time, sell, repair 등

Tier 3: 복잡한 명령어 (수동)
- auction, craft, guild 등
- 목록만 보존, 재구현 필요
```

---

### 스킬 (Skills)

**전략**: 데이터 vs 로직 분리

```yaml
# 데이터: 마이그레이션
- 이름, 마나, 쿨다운, 레벨 제한

# 로직: 재구현
- 간단한 스킬: 템플릿 (데미지, 힐 등)
- 복잡한 스킬: Lua 스크립트
- 매우 복잡: 수동 구현
```

---

## Phase별 구현 계획

### Phase 1: MVP (Week 1-4)

**목표**: 플레이 가능한 최소 게임

```markdown
✅ Rooms (자동)
✅ Items (기본만)
✅ Monsters (기본만)
✅ Zones (리셋 기본만)
✅ Classes (데이터만)

결과: 로그인 → 캐릭터 생성 → 이동 → 전투 가능
```

**완료 기준**:
- CircleMUD 1개 완전 마이그레이션
- 변환 성공률 90% 이상
- 실제 플레이 가능

---

### Phase 2: 확장 (Week 5-8)

**목표**: 주요 게임 시스템

```markdown
✅ Races (있으면)
✅ Shops
✅ Socials
✅ Help (기본)
✅ Skills (메타데이터)
✅ Commands (목록)

결과: 상점, 퀘스트, 소셜 기능 추가
```

---

### Phase 3: 시스템 테이블 (Week 9-12) — 완료

**목표**: 게임 밸런스/설정 데이터 추출

```markdown
✅ Game Config (게임 설정 key-value)
✅ Experience Table (경험치 테이블)
✅ THAC0 Table (명중 판정 테이블)
✅ Saving Throws (세이빙 스로우)
✅ Level Titles (레벨 칭호)
✅ Attribute Modifiers (능력치 보정)
✅ Practice Params (연습 파라미터)

결과: 전투 밸런스, 캐릭터 성장 시스템 완전 마이그레이션
```

---

### Phase 4: 한국어 자연어순 명령어 체계 (Week 13-14) — 완료

**목표**: 한국어 SOV 명령어 파서 Lua 생성

```markdown
✅ korean_nlp.lua (한국어 NLP 유틸 — 받침, 조사, 어간 추출)
✅ korean_commands.lua (SOV 파서 + 동사/방향/스펠 매핑)
✅ Python 참조 구현 (has_batchim, strip_particle, extract_stem, parse)
✅ UIR 스킬 한국어 이름 연동 (extensions["korean_name"] → SPELL_NAMES)
✅ 3개 소스 모두 한국어 Lua 생성 확인 (tbaMUD, Simoon, 3eyes)

결과: 한국어 자연어순 명령어 체계 완성 (69개 테스트)
```

---

### Phase 5: 폴리싱 (향후)

**목표**: 문서화 및 도구 개선

```markdown
⬜ Weather/Time (날씨/시간 설정)
⬜ Special Procedures (가이드)
⬜ 마이그레이션 도구 개선
⬜ 사용자 매뉴얼
⬜ 예제 프로젝트

결과: 커뮤니티 출시 준비
```

---

## 제외 항목 및 이유

### 1. Player Data (플레이어 데이터)
**제외 이유**:
- 엄청나게 복잡 (수천 개 필드)
- 밸런스 재조정 필요
- 마이그레이션 오류 시 플레이어 분노
- **권장**: 초기화 후 새 시작

### 2. Crafting System (제작 시스템)
**제외 이유**:
- MUD마다 완전히 다름
- 복잡한 레시피 트리
- **권장**: GenOS 플러그인으로 재구현

### 3. Mail/Message (편지)
**제외 이유**:
- 실시간 데이터
- 중요도 낮음
- **권장**: 초기화

### 4. Admin Tools (관리자 도구)
**제외 이유**:
- GenOS는 웹 대시보드 사용
- 구 시스템 불필요

### 5. Custom Mini-Games (미니게임)
**제외 이유**:
- 게임마다 완전히 다름
- 재구현 필요

---

## 마이그레이션 체크리스트

### 구현 현황 범례

| 기호 | 의미 |
|------|------|
| [x] | 구현 완료 (UIR + 파서 + 컴파일러 출력) |
| [~] | 부분 구현 (일부만 완료) |
| [ ] | 미구현 |

**어댑터 지원**: C = CircleMudAdapter, S = SimoonAdapter, 3 = ThreeEyesAdapter

---

### P0 - 필수 (게임 불가능)

```markdown
- [x] Rooms (방)              [C,S] UIR + SQL 출력
- [x] Items (아이템)           [C,S] UIR + SQL 출력
- [x] Monsters (몬스터)        [C,S] UIR + SQL 출력, Simoon은 extensions 지원
- [x] Zones (지역)             [C,S] UIR + SQL 출력, 리셋 명령어 포함
- [x] Classes (직업)           [C,S] 기본 4클래스(tbaMUD)/7클래스(Simoon) → SQL + Lua 출력
```

### P1 - 중요 (경험 저하)

```markdown
- [x] Shops (상점)             [C,S] UIR + SQL 출력
- [x] Triggers (트리거)        [C]   DG Script → Lua 변환 (기본), Simoon은 해당 없음
- [x] Quests (퀘스트)          [C,S] UIR + SQL 출력
- [~] Combat System (전투)     [C,S] THAC0 기본 공식만 Lua 출력, 커스텀 전투 미지원
- [x] Races (종족)             [S]   Simoon 5종족 하드코딩 → SQL 출력
```

### P2 - 가치 있음

```markdown
- [x] Socials (감정표현)       [C,S] lib/misc/socials 파싱 → SQL 출력 (tbaMUD 104개, Simoon 104개)
- [x] Help (도움말)            [C,S] lib/text/help/*.hlp 파싱 → SQL 출력 (tbaMUD 721개, Simoon 2,220개)
- [x] Skills (메타데이터)      [C,S] C 소스 3파일 결합 파싱 → SQL 출력 (tbaMUD 54개, Simoon 79개)
- [x] Commands (목록)          [C,S] src/interpreter.c cmd_info[] 파싱 → SQL 출력 (tbaMUD 275개, Simoon 546개)
- [ ] Factions/Alignment       해당 MUD에 존재 시
```

### P3 - 시스템 테이블 (Phase 3 완료)

```markdown
- [x] Game Config (게임설정)   [C,S] config.c 파싱 → SQL+Lua (tbaMUD 54개, Simoon 36개)
- [x] Exp Table (경험치)       [C,S,3] class.c/global.c 파싱 → SQL+Lua (tbaMUD 128, Simoon 314, 3eyes 203)
- [x] THAC0 Table              [C,3] class.c/global.c 파싱 → SQL+Lua (tbaMUD 140, 3eyes 160)
- [x] Saving Throws            [C] class.c 3중 switch 파싱 → SQL+Lua (tbaMUD 870)
- [x] Level Titles (칭호)      [C,S] class.c 파싱 → SQL (tbaMUD 204, Simoon 628)
- [x] Attr Modifiers (능력치)  [C,S,3] constants.c/global.c 파싱 → SQL+Lua (tbaMUD 161, Simoon 168, 3eyes 160)
- [x] Practice Params          [C,S] class.c 파싱 → SQL (tbaMUD 4, Simoon 7)
```

### P4 - 한국어 명령어 체계 (Phase 4 완료)

```markdown
- [x] korean_nlp.lua           [C,S,3,L] 항상 생성 — UTF-8 한글 NLP 유틸리티
- [x] korean_commands.lua      [C,S,3,L] 항상 생성 — SOV 파서 + 동사 60개 + 방향어 + 스펠 매핑
```

### 미구현

```markdown
- [ ] Weather/Time (날씨/시간) 설정값만 추출
- [ ] Special Procedures       C 소스코드 목록 추출 + 가이드
```

### 제외 항목

```markdown
- [x] Player Data → 초기화 (밸런스 재조정 필요)
- [x] Crafting → GenOS 플러그인으로 재구현
- [x] Mail/Message → 초기화
- [x] Admin Tools → GenOS 웹 대시보드 사용
- [x] Custom Mini-Games → 재구현 필요
```

---

## 성공 기준

### Phase 1 (MVP) - 완료

| 기준 | 목표 | tbaMUD | Simoon | 3eyes | 10woongi | 상태 |
|------|------|--------|--------|-------|----------|------|
| 방 마이그레이션 | 100개+ | 12,700 | 6,508 | 7,439 | 17,590 | 달성 |
| 아이템 | 50개+ | 4,765 | 1,753 | 1,362 | 969 | 달성 |
| 몬스터 | 30개+ | 3,705 | 1,374 | 1,394 | 947 | 달성 |
| 직업 | 4개+ | 4 | 7 | 8 | 14 | 달성 |
| 상점 | - | 334 | 103 | — | — | 달성 |
| 트리거 | - | 1,461 | 0 | — | — | 달성 |
| 퀘스트 | - | 1 | 16 | — | — | 달성 |
| 파싱 에러 | 0 | 0 | 0 | 0 | 0 | 달성 |

### Phase 2 (확장) - 완료

| 기준 | 목표 | tbaMUD | Simoon | 3eyes | 10woongi | 상태 |
|------|------|--------|--------|-------|----------|------|
| 소셜 | 30개+ | 104 | 104 | — | — | 달성 |
| 도움말 | 50개+ | 721 | 2,220 | 116 | 72 | 달성 |
| 스킬 목록 | 완성 | 65 | 121 | 63 | 51 | 달성 |
| 커맨드 목록 | 완성 | 301 | 550 | — | 51 | 달성 |
| 종족 (해당 시) | 존재하면 | — | 5 | 8 | — | 달성 |
| 테스트 | 전체 통과 | 144 | 144 | 175 | 354 | 달성 |

### Phase 3 (시스템 테이블) - 완료

| 기준 | 목표 | tbaMUD | Simoon | 3eyes | 10woongi | 상태 |
|------|------|--------|--------|-------|----------|------|
| 게임 설정 | 추출 | 54 | 36 | — | 98 | 달성 |
| 경험치 테이블 | 추출 | 128 | 314 | 203 | — | 달성 |
| THAC0 테이블 | 추출 | 140 | — | 160 | — | 달성 |
| 세이빙 스로우 | 추출 | 870 | — | — | — | 달성 |
| 레벨 칭호 | 추출 | 204 | 628 | — | — | 달성 |
| 능력치 보정 | 추출 | 161 | 168 | 160 | — | 달성 |
| 연습 파라미터 | 추출 | 4 | 7 | — | — | 달성 |
| SQL 테이블 | +7 | 21 total | 21 total | 21 total | 21 total | 달성 |
| Lua 스크립트 | +3 | config+exp+stat | config+exp+stat | exp+stat | config | 달성 |
| 테스트 | 전체 통과 | 191 | 191 | 191 | 354 | 달성 |

### Phase 4 (한국어 명령어 체계) - 완료

| 기준 | 목표 | tbaMUD | Simoon | 3eyes | 10woongi | 상태 |
|------|------|--------|--------|-------|----------|------|
| korean_nlp.lua | 생성 | 생성 | 생성 | 생성 | 생성 | 달성 |
| korean_commands.lua | 생성 | 생성 | 생성 | 생성 | 생성 (51 스펠) | 달성 |
| 표준 동사 | 55개+ | 60개 | 60개 | 60개 | 60개 | 달성 |
| 방향어 | 14개+ | 14개 | 14개 | 14개 | 14개 | 달성 |
| SOV 파서 | 동작 | 동작 | 동작 | 동작 | 동작 | 달성 |
| SVO 폴백 | 동작 | 동작 | 동작 | 동작 | 동작 | 달성 |
| 테스트 | 전체 통과 | 260 | 260 | 260 | 354 | 달성 |

### Phase 5 (폴리싱) - 미착수

- [ ] 수동 작업 가이드 완성
- [ ] 사용자 매뉴얼 완성

---

## 부록: MUD별 특수사항

### CircleMUD/tbaMUD
- 특징: C 언어, 데이터 파일 + 소스코드
- 난이도: ⭐⭐ (중간)
- 주의: Special procedures 많음

### DikuMUD/ROM
- 특징: CircleMUD와 유사
- 난이도: ⭐⭐ (중간)
- 주의: 색상 코드 형식 다름

### LP-MUD/FluffOS (10woongi 구현 완료)
- 특징: LPC 언어, 객체지향, 개별 .c 파일
- 난이도: ⭐⭐⭐⭐ (어려움)
- 주의: VNUM 없음(해시 생성), 2-패스 출구 해결, regex 기반 setXxx() 파싱
- 구현: LPMudAdapter (9 파서), 94 테스트
- 결과: 17,590 rooms, 969 items, 947 mobs, 122 zones, 98 configs

### MUSH/MUX
- 특징: 소셜 중심, 속성 시스템
- 난이도: ⭐⭐⭐ (어려움)
- 주의: 전투보다 롤플레이 중심

### Evennia
- 특징: Python 기반, 현대적
- 난이도: ⭐⭐ (중간)
- 주의: 이미 잘 구조화됨

---

**문서 버전**: 1.5
**최종 업데이트**: 2026-02-10 — LP-MUD/FluffOS (10woongi) 어댑터 완료 반영 (LPMudAdapter 9파서, 94테스트, 4소스 마이그레이션 지원)
**피드백**: 마이그레이션 진행하면서 계속 개선
