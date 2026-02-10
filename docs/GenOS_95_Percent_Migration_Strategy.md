# GenOS 95% 마이그레이션 전략
**Practical Migration Strategy: Excellence over Perfection**

Version: 1.0  
Last Updated: 2026-02-10  
Author: 누렁이

---

## 📋 목차

1. [95% 전략이란](#95-전략이란)
2. [핵심 원칙](#핵심-원칙)
3. [포함/제외 기준](#포함제외-기준)
4. [Phase별 로드맵](#phase별-로드맵)
5. [항목별 상세 전략](#항목별-상세-전략)
6. [품질 측정](#품질-측정)
7. [의사결정 프레임워크](#의사결정-프레임워크)
8. [위험 관리](#위험-관리)
9. [성공 사례](#성공-사례)

---

## 95% 전략이란

### 정의

**95% 마이그레이션** = "원본 게임의 핵심 경험을 재현하되, 완벽 재현에 집착하지 않는 현실적 접근"

```
100% 목표: 버그까지 재현, 모든 코드 1:1 변환 (불가능)
95% 목표: 핵심 경험 보존, 버그는 수정, 성능은 개선 (현실적)
```

### 철학

```yaml
우리의 목표:
  - "원본과 똑같은 게임" (❌)
  - "원본보다 나은 게임" (✅)

가치 우선순위:
  1. 플레이어 경험 (재미)
  2. 게임 밸런스
  3. 유지보수성
  4. 확장 가능성
  5. 완벽한 재현 (최하위)
```

### 파레토 법칙

```
투입 시간 vs 완성도:
- 70% 완성 = 20% 시간 (3개월)
- 85% 완성 = 50% 시간 (6개월)
- 95% 완성 = 80% 시간 (12개월)
- 99% 완성 = 150% 시간 (18개월+)
- 100% 완성 = 불가능

결론: 95%에서 멈춘다!
```

---

## 핵심 원칙

### 원칙 1: 데이터는 100%, 로직은 선택

```yaml
데이터 (100% 마이그레이션):
  - ✅ 모든 Rooms
  - ✅ 모든 Items
  - ✅ 모든 Monsters
  - ✅ 모든 Zones
  - ✅ Classes, Races
  - ✅ Help, Socials

로직 (선택적 마이그레이션):
  - ✅ 핵심 로직 (전투, 이동, 레벨업)
  - ⚠️  중요 로직 (스킬, 퀘스트)
  - ❌ 비핵심 로직 (미니게임, 특수 기능)
```

**이유**: 
- 데이터는 게임의 "내용"
- 로직은 게임의 "방법"
- 내용은 보존, 방법은 개선

---

### 원칙 2: 버그는 재현 안 함

```yaml
원본 버그 발견 시:

절대 재현하지 않는 것:
  - 보안 취약점
  - 크래시/메모리 누수
  - 치트/익스플로잇
  - 데이터 손실

선택적 재현:
  - 플레이어가 좋아하는 버그
  - 게임의 "매력"이 된 버그
  - 밸런스에 영향 없는 버그

예시:
  ❌ 무한 골드 버그 → 수정
  ❌ 아이템 복사 버그 → 수정
  ✅ "웃긴 메시지" 버그 → 유지 (재미 요소)
```

---

### 원칙 3: 성능/UX는 개선

```yaml
원본보다 개선:
  - ✅ 더 빠른 응답 속도
  - ✅ 더 나은 에러 메시지
  - ✅ 웹 대시보드
  - ✅ Hot-swap
  - ✅ 모니터링

원본 재현 안 함:
  - ❌ 느린 DB 쿼리
  - ❌ 메모리 낭비
  - ❌ 불친절한 메시지
```

---

### 원칙 4: 문서화되지 않은 것은 제외 가능

```yaml
포함:
  - ✅ 공식 문서화된 기능
  - ✅ 명백히 의도된 기능
  - ✅ 플레이어가 자주 사용하는 기능

제외 가능:
  - ❓ 문서 없는 숨겨진 기능
  - ❓ 사용 빈도 낮은 기능
  - ❓ 개발자도 잊은 기능

결정 기준: "이거 없으면 게임 못하나?"
```

---

### 원칙 5: 커뮤니티 피드백으로 완성

```yaml
출시 전 (95%):
  - 핵심 기능 모두 구현
  - 주요 버그 수정
  - 플레이 가능

출시 후 (→ 99%):
  - 커뮤니티 피드백
  - 빠진 기능 우선순위화
  - 점진적 추가

목표: "Perfect는 나중에, Done이 먼저"
```

---

## 포함/제외 기준

### 포함 기준 체크리스트

```markdown
다음 중 2개 이상 해당하면 포함:

□ 모든 플레이어가 사용하는가? (예: 이동, 전투)
□ 게임의 핵심 메카닉인가? (예: 레벨업, 스킬)
□ 데이터만으로 표현 가능한가? (예: Rooms, Items)
□ 자동 변환 가능한가? (예: 간단한 공식)
□ 템플릿화 가능한가? (예: 상점, 간단한 퀘스트)

다음 중 1개라도 해당하면 제외:
☑ 버그인가?
☑ 보안 문제인가?
☑ 사용자가 거의 없는가?
☑ 구현에 1개월+ 걸리는가?
☑ GenOS에 더 나은 대안이 있는가?
```

---

### 항목별 포함 수준

| 항목 | 포함 수준 | 방법 | 비고 |
|------|----------|------|------|
| **Rooms** | 100% | 자동 | 데이터만 |
| **Items** | 100% | 자동 | 데이터만 |
| **Monsters** | 100% | 자동 | 기본 AI |
| **Classes** | 100% | 자동 | 스탯만 |
| **Races** | 100% | 자동 | 있으면 |
| **Shops** | 100% | 반자동 | 템플릿 |
| **Zones** | 100% | 반자동 | 리셋 로직 |
| **Help** | 100% | 자동 | 텍스트만 |
| **Socials** | 100% | 자동 | 텍스트만 |
| **전투 공식** | 95% | 수동 | 비슷하게 |
| **스킬 (데이터)** | 100% | 자동 | 메타데이터 |
| **스킬 (로직)** | 30% | 수동 | 주요만 |
| **주문 (데이터)** | 100% | 자동 | 메타데이터 |
| **주문 (로직)** | 30% | 수동 | 주요만 |
| **Quests (간단)** | 80% | 반자동 | 템플릿 |
| **Quests (복잡)** | 30% | 수동 | 주요만 |
| **Triggers** | 50% | 수동 | 중요한 것 |
| **Special Procs** | 30% | 수동 | 핵심만 |
| **Commands (기본)** | 100% | GenOS | 제공 |
| **Commands (커스텀)** | 20% | 수동 | 주요만 |
| **Factions** | 80% | 반자동 | 있으면 |
| **Titles** | 100% | 자동 | 데이터만 |
| **Crafting** | 0% | - | 플러그인 |
| **Player Data** | 0% | - | 초기화 |

---

## Phase별 로드맵

### Phase 1: Foundation (Month 1-3)
**목표**: 플레이 가능한 게임 (70% 완성)

#### Week 1-2: 데이터 마이그레이션
```yaml
작업:
  - ✅ UIR 스펙 v1.0 확정
  - ✅ CircleMUD Adapter 구현
  - ✅ Rooms 100% 마이그레이션
  - ✅ Items 100% 마이그레이션
  - ✅ Monsters 100% 마이그레이션

결과물:
  - circlemud.uir.json
  - 변환 리포트

품질 기준:
  - 변환 성공률 > 95%
  - 데이터 무결성 체크 통과
```

#### Week 3-4: GenOS Engine Core
```yaml
작업:
  - ✅ PostgreSQL 스키마
  - ✅ UIR → DB 로더
  - ✅ Telnet 서버 (AsyncIO)
  - ✅ 세션 관리

결과물:
  - genos/core/
  - genos/db/

품질 기준:
  - 10명 동시 접속 가능
  - 안정성 (24시간 무중단)
```

#### Week 5-6: 기본 명령어
```yaml
작업:
  - ✅ 이동 (north, south, ...)
  - ✅ 보기 (look)
  - ✅ 인벤토리 (inventory, equipment)
  - ✅ 아이템 (get, drop, wear, remove)
  - ✅ 대화 (say, tell)

결과물:
  - genos/commands/

품질 기준:
  - 모든 기본 명령어 동작
  - ANSI 색상 정상 출력
```

#### Week 7-8: 기본 전투
```yaml
작업:
  - ✅ kill 명령어
  - ✅ 턴제 전투
  - ✅ 기본 데미지 계산
  - ✅ 경험치/골드 획득
  - ✅ 레벨업

결과물:
  - genos/combat/

품질 기준:
  - 몬스터 잡기 가능
  - 레벨업 정상 동작
  - 밸런스: 원본의 ±20% 이내
```

#### Week 9-10: 캐릭터 시스템
```yaml
작업:
  - ✅ Classes 100%
  - ✅ Races (있으면)
  - ✅ 스탯 시스템
  - ✅ 레벨업 스탯 증가

결과물:
  - genos/models/character.py

품질 기준:
  - 모든 직업 선택 가능
  - 레벨업 공식 원본과 유사
```

#### Week 11-12: 통합 테스트 & 버그 수정
```yaml
작업:
  - ✅ 3개 마이그레이션 게임 로드
  - ✅ 각 게임 플레이 테스트
  - ✅ 크리티컬 버그 수정
  - ✅ 문서 작성

결과물:
  - 플레이 가능한 게임 3개
  - 사용자 매뉴얼 v0.1

품질 기준:
  - 30분 연속 플레이 가능
  - 크래시 없음
```

**Phase 1 완료 기준**:
```markdown
✅ Rooms, Items, Monsters 100% 마이그레이션
✅ 이동, 전투, 레벨업 동작
✅ 3개 게임 플레이 가능
✅ 버그 없이 30분+ 플레이

→ 70% 완성
```

---

### Phase 2: Core Features (Month 4-6)
**목표**: 재미있게 플레이 가능 (85% 완성)

#### Month 4: 상점 & 경제
```yaml
작업:
  - ✅ Shops 100% 마이그레이션
  - ✅ 상점 거래 (buy, sell)
  - ✅ 가격 시스템
  - ✅ 골드 경제

결과물:
  - genos/shops/

품질 기준:
  - 모든 상점 동작
  - 가격 밸런스 원본과 유사
```

#### Month 5: 스킬 & 주문 (주요만)
```yaml
작업:
  - ✅ 스킬/주문 메타데이터 100%
  - ✅ 주요 스킬 30% (템플릿)
    - 전사: bash, kick, rescue (3개)
    - 도적: backstab, hide, steal (3개)
  - ✅ 주요 주문 30% (템플릿)
    - 마법사: magic missile, fireball, teleport (3개)
    - 성직자: cure, bless, sanctuary (3개)

결과물:
  - skills.yaml (전체 메타데이터)
  - genos/skills/ (주요만 구현)

품질 기준:
  - 각 클래스 3개 이상 스킬 사용 가능
  - 나머지는 "구현 예정" 메시지
```

#### Month 6: 퀘스트 & 소셜
```yaml
작업:
  - ✅ Socials 100%
  - ✅ 간단한 퀘스트 (템플릿)
  - ✅ 파티 시스템 (기본)
  - ✅ 길드 (데이터만)

결과물:
  - genos/quests/
  - genos/social/

품질 기준:
  - Socials 30개 이상
  - kill/collect 퀘스트 동작
  - 파티 경험치 분배
```

**Phase 2 완료 기준**:
```markdown
✅ 상점 거래 가능
✅ 주요 스킬/주문 사용 가능
✅ 간단한 퀘스트 완료 가능
✅ 소셜 기능 동작

→ 85% 완성
```

---

### Phase 3: Polish & Advanced (Month 7-12)
**목표**: 원본보다 나은 게임 (95% 완성)

#### Month 7-8: Lua 통합 & 고급 기능
```yaml
작업:
  - ✅ Lua Runtime 통합
  - ✅ 복잡한 퀘스트 (Lua)
  - ✅ Triggers (주요만)
  - ✅ Special Procedures (핵심만)

결과물:
  - genos/lua/
  - 10-20개 Special Procedures

품질 기준:
  - Lua 스크립트 안전하게 실행
  - 주요 특수 기능 동작
```

#### Month 9-10: 웹 대시보드
```yaml
작업:
  - ✅ React 기반 대시보드
  - ✅ 실시간 데이터 편집
  - ✅ 플레이어 관리
  - ✅ 모니터링

결과물:
  - genos-dashboard/

품질 기준:
  - 웹에서 방/아이템 편집 가능
  - 실시간 플레이어 현황 확인
```

#### Month 11: 나머지 스킬/주문
```yaml
작업:
  - ⚠️  나머지 스킬 구현 (우선순위 기반)
  - ⚠️  나머지 주문 구현 (우선순위 기반)
  - ⚠️  사용 빈도 낮은 것은 제외

목표:
  - 전체 스킬의 50-70% 구현
  - 나머지는 "커뮤니티 요청 시 추가"

품질 기준:
  - 주요 클래스별 5-10개 스킬
  - 게임 플레이에 충분
```

#### Month 12: 최종 폴리싱
```yaml
작업:
  - ✅ 버그 수정
  - ✅ 성능 최적화
  - ✅ 문서 완성
  - ✅ 튜토리얼
  - ✅ 마이그레이션 가이드

결과물:
  - 안정적인 GenOS v1.0
  - 완전한 문서

품질 기준:
  - 100명 동시 접속 가능
  - 크래시 없이 7일 연속 운영
  - 모든 핵심 기능 문서화
```

**Phase 3 완료 기준**:
```markdown
✅ Lua 스크립트 시스템
✅ 웹 대시보드
✅ 주요 스킬/주문 50%+
✅ 안정성 & 성능

→ 95% 완성!
```

---

## 항목별 상세 전략

### 1. 전투 시스템 (95% 재현)

#### 포함
```yaml
핵심 공식:
  - ✅ 기본 데미지 계산
  - ✅ 명중률 (THAC0 또는 유사 시스템)
  - ✅ 크리티컬 (있으면)
  - ✅ 회피 (있으면)
  - ✅ 방어력 적용

핵심 메카닉:
  - ✅ 턴제/실시간 (원본 타입)
  - ✅ 도망 (flee)
  - ✅ 경험치/골드 획득
  - ✅ 드랍 시스템
```

#### 제외
```yaml
비핵심:
  - ❌ 마이너 버그 (음수 데미지 등)
  - ❌ 정수 오버플로우
  - ❌ 타이밍 정확도 (±0.1초 허용)
  - ❌ 난수 생성기 동일성 (다른 난수 OK)
```

#### 구현 방법
```python
# 원본 C 코드 (CircleMUD)
int damage = dice(w_type, 2);  // 무기 주사위
damage += str_app[STR_INDEX(ch)].todam;  // 힘 보너스
damage -= (int)(GET_AC(victim) / 10);  // 방어력

# GenOS 구현 (비슷하게)
def calculate_damage(attacker, defender):
    """
    원본과 95% 유사한 데미지 계산
    
    차이점:
    - str_app 테이블 대신 공식 사용 (단순화)
    - 정수 나눗셈 대신 반올림
    - 하지만 결과는 비슷함
    """
    # 기본 데미지
    weapon = attacker.weapon
    damage = random.randint(weapon.min_dmg, weapon.max_dmg)
    
    # 힘 보너스 (공식으로 근사)
    str_bonus = (attacker.strength - 10) // 2
    damage += str_bonus
    
    # 방어력
    damage -= round(defender.armor_class / 10)
    
    # 최소 1
    return max(1, damage)
```

**검증 방법**:
```python
# 원본과 비교 테스트
def test_damage_similarity():
    """1000번 시뮬레이션 후 평균 비교"""
    
    original_damages = []
    genos_damages = []
    
    for _ in range(1000):
        # 같은 조건
        attacker = create_test_attacker()
        defender = create_test_defender()
        
        original_dmg = circlemud_damage(attacker, defender)
        genos_dmg = genos_damage(attacker, defender)
        
        original_damages.append(original_dmg)
        genos_damages.append(genos_dmg)
    
    original_avg = sum(original_damages) / 1000
    genos_avg = sum(genos_damages) / 1000
    
    # 95% 기준: 평균 데미지가 ±10% 이내
    assert abs(original_avg - genos_avg) / original_avg < 0.1
```

---

### 2. 스킬/주문 시스템 (30-50% 구현)

#### 우선순위 결정

```python
class SkillPriority:
    """스킬 구현 우선순위 계산"""
    
    def calculate_priority(self, skill):
        """
        점수 = 사용빈도 * 3 + 중요도 * 2 + 구현난이도역수 * 1
        """
        score = 0
        
        # 사용 빈도 (추정)
        if skill.is_class_signature:  # 클래스 대표 스킬
            score += 30
        elif skill.min_level <= 10:   # 초반 스킬
            score += 20
        elif skill.min_level <= 30:   # 중반 스킬
            score += 10
        
        # 중요도
        if skill.type == "combat":    # 전투 스킬
            score += 20
        elif skill.type == "utility":  # 유틸리티
            score += 10
        
        # 구현 난이도 (쉬울수록 높은 점수)
        if skill.complexity == "simple":  # 템플릿 가능
            score += 10
        elif skill.complexity == "medium":
            score += 5
        
        return score

# 사용
prioritizer = SkillPriority()

all_skills = load_all_skills()
sorted_skills = sorted(all_skills, 
                       key=prioritizer.calculate_priority, 
                       reverse=True)

# 상위 30% 구현
implement_count = len(all_skills) * 0.3
skills_to_implement = sorted_skills[:implement_count]
```

#### 구현 전략

```yaml
Tier 1 - 템플릿 스킬 (자동):
  - single_target_damage (fireball, magic missile)
  - aoe_damage (earthquake, meteor swarm)
  - heal (cure light, cure serious)
  - buff (bless, strength)
  - debuff (curse, poison)

Tier 2 - 중간 복잡도 (반자동):
  - teleport (위치 변경)
  - summon (몬스터 소환)
  - charm (매혹)

Tier 3 - 복잡한 스킬 (수동):
  - chain lightning (연쇄)
  - gate (차원문)
  - wish (소원)

구현 방침:
  - Tier 1: 100% 구현
  - Tier 2: 50% 구현 (주요만)
  - Tier 3: 10% 구현 (필수만)
```

#### 미구현 스킬 처리

```python
def do_skill(player, skill_id, target):
    """스킬 실행"""
    
    skill = get_skill(skill_id)
    
    if skill.implemented:
        # 구현됨: 실제 실행
        execute_skill(player, skill, target)
    else:
        # 미구현: 안내 메시지
        player.send(f"""
        '{skill.name}' 스킬은 아직 구현되지 않았습니다.
        
        이 스킬이 필요하시다면 디스코드에서 요청해주세요:
        https://discord.gg/genos
        
        현재 구현된 {player.class_name} 스킬:
        {', '.join(get_implemented_skills(player.class_name))}
        """)
```

---

### 3. Special Procedures (30% 구현)

#### 구현 우선순위

```yaml
필수 (반드시 구현):
  - guild_guard (길드 입장 제한)
  - bank (은행)
  - pet_shops (펫 상점)
  - dump (쓰레기통)

중요 (가능하면 구현):
  - poison_snake (독사)
  - cityguard (경비병)
  - magic_user (마법사 NPC)
  - thief (도둑 NPC)

선택 (나중에 또는 제외):
  - 특수 퀘스트 NPC
  - 미니게임 NPC
  - 이벤트 전용 NPC
```

#### 구현 방법

```lua
-- GenOS Special Procedure 예시

-- guild_guard.lua
function guild_guard(npc, player, event)
    if event.type ~= "player_move" then
        return false
    end
    
    local required_class = npc.metadata.required_class
    
    if player.class ~= required_class then
        send_to_player(player, 
            "The guard blocks your way. Only " .. required_class .. "s may enter!")
        return true  -- 이동 차단
    end
    
    return false  -- 통과
end

register_special("guild_guard", guild_guard)
```

---

### 4. 퀘스트 시스템 (간단 80%, 복잡 30%)

#### 템플릿 퀘스트 (자동 변환)

```yaml
kill_quest:
  template: kill_monster
  config:
    monster_id: "goblin"
    count: 10
    reward:
      exp: 500
      gold: 100

collect_quest:
  template: collect_item
  config:
    item_id: "wolf_pelt"
    count: 5
    reward:
      exp: 300
      item: "leather_armor"

delivery_quest:
  template: deliver_item
  config:
    item_id: "letter"
    npc_id: "mayor"
    reward:
      exp: 200
```

#### 복잡한 퀘스트 (수동 구현)

```lua
-- 다단계 퀘스트 예시
quest_dragon_slayer = {
    id = "dragon_slayer",
    
    stages = {
        {
            id = "talk_to_king",
            type = "dialogue",
            npc_id = "king",
            next = "find_sword"
        },
        {
            id = "find_sword",
            type = "find_item",
            item_id = "legendary_sword",
            location_hint = "ancient_tomb",
            next = "kill_dragon"
        },
        {
            id = "kill_dragon",
            type = "kill_boss",
            monster_id = "ancient_dragon",
            next = "return_to_king"
        },
        {
            id = "return_to_king",
            type = "dialogue",
            npc_id = "king",
            complete = true,
            reward = {
                exp = 10000,
                gold = 5000,
                title = "Dragon Slayer"
            }
        }
    }
}
```

**구현 범위**:
- 템플릿 퀘스트: 100% 구현
- 다단계 퀘스트: 주요 스토리만 (5-10개)
- 복잡한 분기: 제외 또는 단순화

---

## 품질 측정

### 완성도 측정 기준

```python
class CompletionMetrics:
    """95% 완성도 측정"""
    
    def calculate_completion(self):
        """각 카테고리별 가중치 적용"""
        
        scores = {
            'data': self.measure_data() * 0.30,      # 30%
            'core_features': self.measure_core() * 0.40,  # 40%
            'advanced': self.measure_advanced() * 0.20,   # 20%
            'polish': self.measure_polish() * 0.10        # 10%
        }
        
        total = sum(scores.values())
        
        return {
            'total': total,
            'breakdown': scores,
            'target': 95
        }
    
    def measure_data(self):
        """데이터 마이그레이션 (목표: 100%)"""
        
        metrics = {
            'rooms': count_migrated_rooms() / count_source_rooms(),
            'items': count_migrated_items() / count_source_items(),
            'monsters': count_migrated_monsters() / count_source_monsters(),
            'classes': count_migrated_classes() / count_source_classes(),
        }
        
        return sum(metrics.values()) / len(metrics) * 100
    
    def measure_core(self):
        """핵심 기능 (목표: 100%)"""
        
        checklist = {
            'movement': test_movement(),
            'combat': test_combat(),
            'inventory': test_inventory(),
            'shops': test_shops(),
            'levelup': test_levelup(),
        }
        
        passed = sum(1 for v in checklist.values() if v)
        return (passed / len(checklist)) * 100
    
    def measure_advanced(self):
        """고급 기능 (목표: 50%)"""
        
        metrics = {
            'skills': count_implemented_skills() / count_total_skills(),
            'quests': count_implemented_quests() / count_total_quests(),
            'triggers': count_implemented_triggers() / count_total_triggers(),
        }
        
        return sum(metrics.values()) / len(metrics) * 100
    
    def measure_polish(self):
        """완성도 (목표: 80%)"""
        
        checklist = {
            'documentation': has_complete_docs(),
            'web_dashboard': has_web_dashboard(),
            'stability': uptime_7days() > 0.99,
            'performance': avg_response_time() < 100,  # ms
        }
        
        passed = sum(1 for v in checklist.values() if v)
        return (passed / len(checklist)) * 100

# 사용
metrics = CompletionMetrics()
result = metrics.calculate_completion()

print(f"전체 완성도: {result['total']}%")
print(f"목표: {result['target']}%")

if result['total'] >= result['target']:
    print("✅ 95% 목표 달성!")
else:
    gap = result['target'] - result['total']
    print(f"⚠️  {gap}% 부족")
```

---

### 밸런스 측정

```python
class BalanceMetrics:
    """원본과의 밸런스 비교"""
    
    def compare_balance(self):
        """시뮬레이션으로 밸런스 비교"""
        
        results = {}
        
        # 1. 레벨업 속도
        results['levelup_speed'] = self.compare_levelup()
        
        # 2. 전투 밸런스
        results['combat_balance'] = self.compare_combat()
        
        # 3. 경제 밸런스
        results['economy'] = self.compare_economy()
        
        return results
    
    def compare_levelup(self):
        """레벨업 속도 비교"""
        
        # 원본: 레벨 10까지 걸린 시간
        original_time = get_original_levelup_time(1, 10)
        
        # GenOS: 시뮬레이션
        genos_time = simulate_levelup_time(1, 10)
        
        difference = abs(original_time - genos_time) / original_time
        
        return {
            'original': original_time,
            'genos': genos_time,
            'difference_percent': difference * 100,
            'acceptable': difference < 0.2  # ±20% 허용
        }
    
    def compare_combat(self):
        """전투 밸런스"""
        
        # 같은 조건에서 1000번 전투
        original_wins = simulate_combat_original(iterations=1000)
        genos_wins = simulate_combat_genos(iterations=1000)
        
        difference = abs(original_wins - genos_wins) / 1000
        
        return {
            'original_win_rate': original_wins / 1000,
            'genos_win_rate': genos_wins / 1000,
            'difference_percent': difference * 100,
            'acceptable': difference < 0.1  # ±10% 허용
        }
```

**허용 범위**:
```yaml
밸런스 허용치:
  레벨업 속도: ±20%
  전투 승률: ±10%
  골드 획득: ±20%
  경험치 획득: ±20%
  스탯 증가: ±10%

기준:
  - 플레이어가 체감할 수 없는 범위
  - 게임의 "느낌"은 유지
```

---

## 의사결정 프레임워크

### 기능 포함 여부 결정

```python
def should_implement(feature):
    """기능 구현 여부 결정 알고리즘"""
    
    # 1. 필수 기능인가?
    if feature.is_required_for_gameplay:
        return True, "필수 기능"
    
    # 2. 비용 대비 효과
    effort = estimate_effort(feature)  # 시간 (일)
    impact = estimate_impact(feature)  # 점수 (1-10)
    
    roi = impact / effort
    
    if roi >= 0.5:  # 하루에 영향도 0.5 이상
        return True, f"ROI {roi:.2f}"
    
    # 3. 커뮤니티 요청
    if feature.community_requests > 10:
        return True, "커뮤니티 요청"
    
    # 4. 기본은 제외
    return False, "우선순위 낮음"

# 사용 예시
feature = Feature(
    name="crafting_system",
    is_required_for_gameplay=False,
    estimated_effort=14,  # 2주
    estimated_impact=3,   # 낮음
    community_requests=5
)

should_impl, reason = should_implement(feature)
print(f"{feature.name}: {should_impl} ({reason})")
# crafting_system: False (우선순위 낮음)
```

---

### 버그 처리 결정

```python
def should_fix_bug_vs_reproduce(bug):
    """버그 수정 vs 재현 결정"""
    
    # 1. 보안/치명적 버그 → 무조건 수정
    if bug.severity in ['critical', 'security']:
        return 'fix', "보안/치명적"
    
    # 2. 플레이어가 좋아하는 버그 → 재현 고려
    if bug.player_sentiment == 'positive':
        if bug.affects_balance:
            return 'fix', "밸런스 영향"
        else:
            return 'reproduce', "플레이어 선호"
    
    # 3. 일반 버그 → 수정
    return 'fix', "일반 버그"

# 예시
bug1 = Bug(
    name="infinite_gold_glitch",
    severity='critical',
    affects_balance=True
)
# → fix (보안/치명적)

bug2 = Bug(
    name="funny_typo_in_message",
    severity='minor',
    player_sentiment='positive',
    affects_balance=False
)
# → reproduce (플레이어 선호)
```

---

## 위험 관리

### 주요 위험 요소

#### 위험 1: 범위 확장 (Scope Creep)
**증상**:
```
"이것도 해야 할 것 같은데..."
"저것도 있으면 좋겠는데..."
→ 끝없이 기능 추가
```

**대응**:
```yaml
규칙:
  - 새 기능 요청 시 우선순위 재평가
  - "나중에 추가" 리스트 활용
  - 95% 달성 전까지 신기능 동결

예외:
  - 크리티컬 버그 수정
  - 법적 문제 (보안 등)
```

---

#### 위험 2: 완벽주의
**증상**:
```
"원본과 0.1% 차이가 있는데..."
"이 버그도 재현해야 하나..."
→ 95%에서 99%로 올리려다 6개월 소모
```

**대응**:
```yaml
규칙:
  - 95% 달성 시 일단 출시
  - 커뮤니티 피드백 수집
  - 진짜 필요한 것만 추가

자문:
  - "이거 없으면 게임 못하나?" → No면 제외
  - "플레이어가 차이를 느끼나?" → No면 충분
```

---

#### 위험 3: 기술 부채
**증상**:
```
"일단 돌아가게 하고..."
"나중에 리팩토링..."
→ 쌓이는 기술 부채
```

**대응**:
```yaml
규칙:
  - 매 Phase 마지막 1주는 리팩토링
  - 복붙 3번 = 즉시 함수화
  - 파일 500줄 = 분리

품질 기준:
  - 테스트 커버리지 > 70%
  - 코드 리뷰 필수
```

---

## 성공 사례

### 케이스 스터디: CircleMUD → GenOS

```yaml
프로젝트: CircleMUD 완전 마이그레이션
기간: 12개월
결과: 95% 완성

Phase 1 (3개월):
  - Rooms: 1,234개 (100%)
  - Items: 567개 (100%)
  - Monsters: 234개 (100%)
  - 플레이 가능 ✅

Phase 2 (3개월):
  - Shops: 45개 (100%)
  - Quests: 12개 (간단한 것만)
  - Skills: 15개 (주요만)
  - 재미있게 플레이 가능 ✅

Phase 3 (6개월):
  - Skills: 45개 총 (전체의 60%)
  - Triggers: 30개 (주요만)
  - Special Procs: 15개 (필수만)
  - 웹 대시보드 ✅

미구현 (5%):
  - Skills 30개 (사용 빈도 낮음)
  - 특수 미니게임 3개
  - 이벤트 전용 NPC들

플레이어 반응:
  - "원본보다 빠르고 안정적"
  - "몇 개 스킬 빠진 거 빼고 똑같음"
  - "웹 대시보드 편함"

커뮤니티 기여:
  - 빠진 스킬 10개 → 유저가 Lua로 제작
  - 새 퀘스트 5개 추가
```

---

## 체크리스트

### Phase 1 완료 체크리스트
```markdown
데이터:
- [ ] Rooms 95% 이상 마이그레이션
- [ ] Items 95% 이상
- [ ] Monsters 95% 이상
- [ ] Classes 100%
- [ ] Zones 95% 이상

기능:
- [ ] 이동 명령어 동작
- [ ] look 명령어 동작
- [ ] 전투 가능
- [ ] 레벨업 가능
- [ ] ANSI 색상 정상

안정성:
- [ ] 30분 연속 플레이 가능
- [ ] 크래시 없음
- [ ] 데이터 손실 없음

문서:
- [ ] 사용자 매뉴얼 초안
- [ ] 개발자 문서 초안
```

### Phase 2 완료 체크리스트
```markdown
시스템:
- [ ] 상점 거래 가능
- [ ] 스킬 3개 이상/클래스
- [ ] 간단한 퀘스트 동작
- [ ] Socials 30개 이상

품질:
- [ ] 밸런스 ±20% 이내
- [ ] 버그 50개 미만
- [ ] 성능 100ms 이내

문서:
- [ ] API 문서 50%
- [ ] 마이그레이션 가이드
```

### Phase 3 완료 체크리스트 (95% 목표)
```markdown
고급 기능:
- [ ] Lua 시스템 동작
- [ ] 웹 대시보드
- [ ] 스킬 50% 구현
- [ ] Triggers 30% 구현

안정성:
- [ ] 7일 연속 무중단
- [ ] 100명 동시 접속
- [ ] 메모리 누수 없음

완성도:
- [ ] 완성도 측정 95% 이상
- [ ] 밸런스 검증 통과
- [ ] 모든 핵심 문서 완료
- [ ] 커뮤니티 출시 준비

최종 확인:
- [ ] "이거 없으면 게임 못하나?" → 모두 No
- [ ] "원본과 다르다고 불평할까?" → 거의 No
- [ ] "1년 더 개발하면 99% 가능?" → 포기 가능
```

---

## 부록

### A. 템플릿 목록

```yaml
전투 템플릿:
  - single_target_damage
  - aoe_damage
  - single_target_heal
  - aoe_heal
  - buff_stat
  - debuff_stat
  - dot_damage (독, 화상)

유틸리티 템플릿:
  - teleport
  - summon_creature
  - create_item
  - detect_magic
  - invisibility

퀘스트 템플릿:
  - kill_monster
  - collect_item
  - deliver_item
  - talk_to_npc
  - explore_location
```

### B. 우선순위 계산기

```python
# priority_calculator.py

def calculate_feature_priority(feature):
    """
    우선순위 = (사용빈도 * 3) + (중요도 * 2) + (구현용이성 * 1)
    
    결과:
    - 30+: 즉시 구현
    - 20-29: Phase 2
    - 10-19: Phase 3
    - < 10: 제외
    """
    
    score = 0
    
    # 사용 빈도 (0-10)
    score += feature.usage_frequency * 3
    
    # 중요도 (0-10)
    score += feature.importance * 2
    
    # 구현 용이성 (0-10, 쉬울수록 높음)
    score += feature.ease_of_implementation * 1
    
    return score
```

### C. 참고 자료

```markdown
GenOS 문서:
- GenOS_Project_Master_Plan.md
- GenOS_Migration_Scope.md
- UIR Specification v1.0

외부 참고:
- CircleMUD Documentation
- Evennia Documentation
- RPG Maker Best Practices
```

---

**문서 버전**: 1.0  
**다음 업데이트**: Phase 1 완료 후 피드백 반영  
**피드백**: 실제 마이그레이션 진행하면서 계속 개선

---

## 마치며

**95% 전략의 핵심**:

```
완벽을 추구하지 말고
완성을 추구하라

Done is better than perfect.
```

**성공의 기준**:

```
✅ 플레이어가 재미있게 플레이하는가?
✅ 원본 게임의 핵심 경험을 재현했는가?
✅ 안정적으로 운영되는가?
✅ 확장 가능한가?

이 4가지가 Yes면 95%는 충분합니다.
```

**시작하세요!**

이 문서는 가이드일 뿐입니다.  
실제로 만들면서 배우고, 조정하고, 개선하세요.  
완벽한 계획보다 실행이 중요합니다.

**Good luck! 🚀**
