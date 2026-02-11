# Simoon (CircleMUD 3.0 한국어 커스텀) 데이터 전수조사

> 최종 업데이트: 2026-02-11 | 심층 분석 완료

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
