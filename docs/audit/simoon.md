# Simoon (CircleMUD 3.0 한국어 커스텀) 데이터 전수조사

> 최종 업데이트: 2026-02-12 | 심층 분석 + 런타임 차이점 분석 완료

## 1. 아키텍처

Simoon은 CircleMUD 3.0을 기반으로 한국어 커스텀한 MUD.
SimoonAdapter는 CircleMudAdapter를 상속하여 EUC-KR 인코딩과 포맷 차이를 처리.

| 항목 | CircleMUD 기본 | Simoon 차이 |
|------|---------------|-------------|
| 인코딩 | ASCII | EUC-KR |
| WLD stats | 4-field | 3-field |
| OBJ stats | 4-field | 3-field |
| ZON params | 4-field | 3-field |
| MOB format | standard | 커스텀 named attrs → extensions |
| Flags | asciiflag | 대부분 plain int (일부 asciiflag) |

## 2. 데이터 파일 구조

### lib/world/ — 128개 존

| 확장자 | 수량 | 데이터 | 현재 파싱 |
|--------|------|--------|-----------|
| .wld | 128 | 방 (6,508) | **YES** |
| .mob | 128 | 몬스터 (1,374) | **YES** |
| .obj | 128 | 아이템 (1,753) | **YES** |
| .zon | 128 | 존 리셋 | **YES** |
| .shp | 128 | 상점 (103) | **YES** |
| .trg | - | 트리거 (Simoon에 없음) | N/A |

### lib/misc/

| 파일 | 용도 | 현재 파싱 |
|------|------|-----------|
| socials | 소셜 (104개) | **YES** |
| messages | 전투 메시지 | **NO** |

### lib/text/

| 파일 | 용도 | 현재 파싱 |
|------|------|-----------|
| help/ | 도움말 (2,220개) | **YES** |
| greetings | 로그인 화면 | **NO** |
| motd | 오늘의 메시지 | **NO** |
| imotd | 관리자 메시지 | **NO** |
| news | 뉴스 | **NO** |
| policies | 정책 | **NO** |
| handbook | 관리자 핸드북 | **NO** |
| background | 배경 스토리 | **NO** |
| credits | 크레딧 | **NO** |
| clan/clan.bak | 클랜 데이터 | **NO** |

### src/ — 소스 코드

| 파일 | 추출 데이터 | 현재 파싱 |
|------|-------------|-----------|
| interpreter.c | 명령어 (546개) | **YES** |
| spells.h + spell_parser.c | 스킬 (79개) | **YES** |
| config.c | 게임 설정 | **YES** |
| class.c | 직업 테이블 (7 classes) | **YES** |
| constants.c | 상수 | **YES** |

---

## 3. Simoon 전용 확장

### MOB 커스텀 필드

Simoon 몬스터는 표준 CircleMUD 필드 + named attributes 사용:

| 필드 | 파싱 | 비고 |
|------|------|------|
| 표준 CircleMUD 필드 전부 | **YES** | |
| 커스텀 named attrs | **YES** | extensions에 저장 |

### 퀘스트 시스템

| 항목 | 수량 | 파싱 |
|------|------|------|
| 퀘스트 정의 | 16개 | **YES** |
| 퀘스트 보상/조건 | - | **YES** |

### 직업/종족

| 항목 | 수량 | 파싱 |
|------|------|------|
| 직업 (Classes) | 7 | **YES** |
| 종족 (Races) | 5 | **YES** |

---

## 4. 전투 메시지 (lib/misc/messages)

### 4.1 포맷

tbaMUD와 동일 M블록 포맷, **EUC-KR 인코딩**.

### 4.2 한국어 조사 변수 (Simoon 전용)

| 변수 | 의미 | 예시 |
|------|------|------|
| $j | 이/가 (시전자) | "$n$j 공격한다" |
| $g | 이/가 (피해자) | "$N$g 쓰러진다" |
| $d | 을/를 | "$N$d 베었다" |
| $C | 에게 | "$N$C 화살을 쏜다" |
| $v | 로/으로 | "검$v 베었다" |
| $D | 는/은 | "$n$D" |

표준 tbaMUD 변수($n/$N/$s/$S/$m/$M/$e/$E)도 동일 사용.

### 4.3 특이사항

- 받침 기반 조사 자동 선택이 메시지 레벨에서 처리됨
- tbaMUD 파서 재사용 가능 (encoding="euc-kr" 옵션만 추가)

---

## 5. 텍스트 파일

| 파일 | 인코딩 | 설명 |
|------|--------|------|
| greetings | EUC-KR | 로그인 화면 |
| motd | EUC-KR | 오늘의 메시지 |
| imotd | EUC-KR | 관리자 메시지 |
| news | EUC-KR | 뉴스/패치노트 |
| policies | EUC-KR | 정책 |
| handbook | EUC-KR | 관리자 핸드북 |
| background | EUC-KR | 배경 스토리 |
| credits | EUC-KR | 크레딧 |
| clan | EUC-KR | 클랜 데이터 (Simoon 전용) |

---

## 6. 커버리지 요약

### 현재 (재평가: ~90%)

Simoon은 CircleMUD 기반이라 tbaMUD와 구조가 거의 동일.

| 카테고리 | 파싱 비율 | 비고 |
|----------|-----------|------|
| 방 | **100%** | 3-field stats 처리 |
| 몬스터 | **100%** | 커스텀 attrs 포함 |
| 아이템 | **100%** | 3-field stats 처리 |
| 존 리셋 | **100%** | 3-field params 처리 |
| 상점 | **100%** | |
| 소셜 | **100%** | |
| 도움말 | **100%** | 2,220개 |
| 명령어 | **100%** | 546개 |
| 스킬 | **100%** | 79개 |
| 퀘스트 | **100%** | 16개 |
| 직업/종족 | **100%** | |
| 게임 설정 | **100%** | |
| **전투 메시지** | **0%** | messages 파일 (EUC-KR, 한국어 조사 변수) |
| **텍스트 파일** | **0%** | greetings/motd/news 등 9개 (EUC-KR) |

### 95% 달성 필요 작업

1. **전투 메시지 파서** — tbaMUD 파서 재사용 (encoding="euc-kr"), 한국어 조사 변수($j/$g/$d/$C/$v/$D) 인식
2. **텍스트 파일 추출** — 9개 파일 (EUC-KR → UTF-8 변환)
3. (선택) clan 데이터 — 클랜 시스템 정보

---

## 7. 런타임 메커닉 — tbaMUD 대비 차이점

> 소스: `src/fight.c`, `src/limits.c`, `src/class.c` 분석

### 7.1 tbaMUD와 동일한 부분

- 기본 전투 흐름: violence_update → multi_hit → hit → damage
- 사망 상태 임계값: HP -11 이하 DEAD, -6~-10 MORTAL, -3~-5 INCAP
- HP/MANA/MOVE 회복: graf() 연령 기반, 위치별 배수 (sleeping/resting/sitting)
- Sanctuary: 데미지 1/2 감소
- backstab_mult(level) 배수 함수

### 7.2 THAC0 계산 — 대폭 간소화

```
tbaMUD: THAC0 = class_table[class][level] (클래스별 레벨 테이블)
Simoon: PC → THAC0 = 1 (고정!)
        NPC → THAC0 = 20
        레벨 30 미만: += (20 - level) 페널티
        지능 보정: -= (INT - 13) / 1.5
        지혜 보정: -= (WIS - 13) / 1.5
```

**핵심 차이**: PC는 THAC0 1 고정 → 30레벨 이후 거의 100% 명중. INT/WIS가 명중에 영향.

### 7.3 다타공격 — 레벨 기반 + 랜덤

```
tbaMUD: 2nd/3rd attack 스킬 확률 기반
Simoon:
  레벨 150+: 5회
  레벨 100+: 4회
  레벨 50+:  3회
  레벨 30+:  3회
  레벨 20+:  2회
  레벨 5+:   2회

  랜덤 추가: 10% 확률 +1회, 희귀 확률 +2회
```

NPC는 mob_specials의 attack1/attack2/attack3 확률 필드로 다중 공격.

### 7.4 반격 스킬 (SKILL_REATT)

tbaMUD에 없는 Simoon 전용 기능:

```
10% 확률, 피해자 레벨 ≥ 공격자 레벨:
→ 공격자가 자기 데미지를 받음 (반사 피해)
```

### 7.5 활/화살 시스템 (헌터)

```
ITEM_ARROW + ITEM_BOW 장비 조합
화살 무게 -= 1 (소모)
데미지 = (bow.value1 + bow.value2) * 2
```

### 7.6 사망 패널티 — tbaMUD와 크게 다름

```
PvP 사망: 경험치/아이템 손실 없음, HP/MANA/MOVE 완전 복구, 부활 장소 이동
          + 킬마크 지급: (HP+MANA) / 150,000

PvM 사망 (레벨 50+):
  - maxHP -= random(10, 30)  (200 이하 시 미적용)
  - maxMANA -= random(10, 30)
  - maxMOVE -= random(10, 30)
  - 크리스탈 -= random(30, 90)
  - 골드 -= random(30,000 ~ 90,000)
```

**tbaMUD는 경험치 손실만**, Simoon은 **능력치 영구 감소**.

### 7.7 환생 (Remort) 시스템 — 303레벨

```
레벨 303 + 필요 경험치 도달:
  → 경험치 50,100,000 고정
  → 환생 플래그 (RMT_FLAGS) 설정
  → 7 클래스 모두 환생 완료 시: maxHP = maxMANA = 100,000
```

### 7.8 이중 화폐

| 화폐 | 획득 | 용도 |
|------|------|------|
| 골드 | 전투/퀘스트 | 일반 상점 |
| 크리스탈 | 레벨업 자동 지급 | 특수 상점, 환생 비용 |
| 킬마크 | PvP 승리, 퀘스트 | 특수 아이템, 랭킹 |

### 7.9 퀘스트 시스템 (16개, tbaMUD에 없음)

| 타입 | 코드 | 설명 |
|------|------|------|
| AQ_OBJECT | 0 | 아이템 획득 |
| AQ_ROOM | 1 | 특정 방 도달 |
| AQ_MOB_FIND | 2 | 몹 발견 |
| AQ_MOB_KILL | 3 | 몹 처치 |
| AQ_MOB_SAVE | 4 | 몹 구출 |
| AQ_RETURN_OBJ | 5 | 아이템 반납 |

자동 트리거: `autoquest_trigger_check()` — 몹 사망/아이템 획득 시 자동 체크.

### 7.10 회복 차이

```
tbaMUD 기본 + Simoon 추가:
  - ITEM_MANA_REGEN 장비: 착용당 +10 MANA 회복
  - ROOM_GOOD_REGEN 방: HP x4, MANA x2, MOVE x2
  - ADV_FAST_REGEN 장점: HP +2
```

### 7.11 DB 설계 포인트 (tbaMUD 대비 추가)

| 런타임 요소 | DB/엔진 적용 |
|-------------|-------------|
| 크리스탈/킬마크 | players 테이블 추가 컬럼 |
| 환생 플래그 | players.extensions JSONB |
| 퀘스트 시스템 | quests + quest_progress 테이블 |
| PvP 킬마크 | 인메모리 + 주기적 저장 |
| 능력치 사망 패널티 | maxHP/maxMANA/maxMOVE 직접 감소 (players) |
| 한국어 조사 | 엔진 core/korean.py (has_batchim + 조사 선택) |
