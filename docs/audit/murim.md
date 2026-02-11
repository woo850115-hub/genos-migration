# Murim (무림, 확장 Mordor 무협 MUD) 데이터 전수조사

> 최종 업데이트: 2026-02-11 | 심층 분석 완료

## 1. 아키텍처

Mordor 2.0 기반 **무협 확장** MUD. 3eyes/muhan13과 같은 엔진이나
creature struct가 1184B → **3,380B**로 대폭 확장 (무공/내공/무술 시스템).
EUC-KR 인코딩, 바이너리 C struct 포맷.

| 항목 | 3eyes | murim 차이 |
|------|-------|-----------|
| sizeof(creature) | 1184 | **3,380** (+185%) |
| sizeof(object) | 352 | **492** (+40%) |
| sizeof(room) | 480 | ~444 |
| sizeof(exit_) | 44 | ~40 |
| 클래스 | 8 | **21** |
| 종족 | 8 | **4** |
| 스펠 | 63 | **126+** |
| 스탯 | 5 (str~pty) | **18** (5기본+13무술) |
| 착용 슬롯 | 20 | **40** |
| proficiency[] | 5 | **50** |
| realm[] | 4 | **40** |
| art[] 무공 배열 | 없음 | **256 슬롯** |

## 2. 데이터 파일 구조

### objmon/ — 바이너리 데이터

| 파일 패턴 | 수량 | 데이터 | struct 크기 |
|-----------|------|--------|------------|
| m{nn} | 20 | 몬스터 (~683) | 3,380B |
| o{nn} | 14 | 아이템 (~1,077) | 492B |
| 조자건, 혈의노인 | 2 | 텍스트 파일 | - |

### rooms/ — 방 데이터

소스에서 `ROOMPATH="/home/murim/rooms"` 참조하나 현재 스냅샷에 없음.
맵 파일 분석으로 최소 수천 개 방 존재 추정 (낙양성 맵만 ~1,173번 방까지).

### help/ — 도움말 (30 파일)

감정, 고려인, 관리, 광동인, 그룹, 기타, 내공심법, 도우미, 도움말,
동영인, 몹제작, 무공, 새소식, 아이템제작, 안시, 이동, 전투, 정보,
정책, 제작, 존제작, 직업, 천축인, 통신, 투자, 특수기술, 행동, help.1, help.2, help.148

### mukong/ — 무공 데이터 (4 파일)

종족별 무공 커리큘럼 파일:
- 고려인 (Korean) — 검풍/뇌천풍 계열
- 광동인 (Chinese) — 화염검/열염법 계열 + 독 6종
- 동영인 (Japanese) — 탄지법/빙설법 계열 + 분신법술
- 천축인 (Indian) — 지진법/천동법 계열

### map/ — 지도 (11 파일)

감숙성, 고비사막, 낙양성, 사냥터, 산서성, 운남성, 절강성, 호남성, 호북성, 전체지도

### docs/ — 빌더 문서 (18 파일)

DM 매뉴얼, 플래그 레퍼런스, 제작 가이드 등

---

## 3. Creature Struct (3,380B) — 핵심 구조

### 3.1 기본 필드 (offset 0~451)

| 오프셋 | 필드 | 타입 | 크기 |
|--------|------|------|------|
| 0 | name[72] | char | 72 |
| 72 | war_win/war_lose | short×2 | 4 |
| 76 | war_gold | long | 4 |
| 80 | description[78] | char | 78 |
| 158 | back_desc[78] | char | 78 |
| 236 | talk[78] | char | 78 |
| 314 | password[15] | char | 15 |
| 329 | key[3][20] | char | 60 |
| 389 | tname[8] | uchar | 8 |
| 397 | email[40] | uchar | 40 |
| 437 | jumin[14] | uchar | 14 |

### 3.2 핵심 스탯 (offset 452~539)

| 오프셋 | 필드 | 타입 |
|--------|------|------|
| 452 | fd | short |
| 454 | special | short |
| 456 | type/class/race | char×3 |
| 460 | level | long |
| 464 | numwander | long |
| 468 | alignment | long |
| 472 | sunak (평판) | long |
| 476-492 | str/dex/con/int/pty | long×5 |
| 496-508 | hpmax/hpcur/mpmax/mpcur | long×4 |
| 512-516 | armor/thaco | long×2 |
| 520-524 | experience/gold | long×2 |
| 528-536 | ndice/sdice/pdice | long×3 |

### 3.3 확장 배열 (offset 540~915)

| 오프셋 | 필드 | 크기 | 설명 |
|--------|------|------|------|
| 540 | proficiency[50] | 200B | 무기 숙련도 50종 |
| 740 | realm[40] | 160B | 마법 영역 40종 |
| 900 | spells[16] | 16B | 128비트 스펠 비트필드 |
| 916 | flags[80] | 80B | **640비트** 플래그! |
| 996 | quests[16] | 16B | 퀘스트 비트필드 |

### 3.4 전투/이동 스탯 (offset ~1980~2148)

fame, killmark, artattck, artarmor, destructive, pk, repower,
hungry, movecur, movemax, thirsty, swim, fixed, avoid, legpower,
scount, tnamecnt, penalty

### 3.5 개별 무술 스킬 (24종, offset ~2052~2144)

ablowshoot(활연사격), alegattck(다리공격), amanyattck(연타),
akick(발차기), aconcentration(정신집중), adoorpick(문따기),
asurprise(기습), athrow(암기날리기), ainvi(은신), abackhash(뒤치기),
aincarnation(분신술), ablow(일격필살), ajoint(급소찌르기),
aswordsafe(칼기막), acrossattck(십자공격), ashdow(그림자),
amagicsafe(마법방어), amagicfire(매직파이어), amagicice(매직아이스),
amagicsword(매직소드), amagicheal(회복), amagicallheal(전체회복),
amagiccrazy(광환술)

### 3.6 무공 배열 (offset ~2144, 1024B)

**art[256]** — 256개 무공 기술 슬롯 (long × 256)

### 3.7 무술 스탯 (11종, offset ~3168~3224)

| 필드 | 한국어 |
|------|--------|
| outstrength | 외공 |
| instrength | 내공 |
| syoyoul | 소울 |
| stickiness | 점력 |
| kyombub | 검법 |
| dobub | 도법 |
| kyumbub | 권법 |
| jibub | 지법 |
| jinbub | 진법 |
| amki | 암기 |
| shinbub | 신법 |
| jobki | 장기 |
| sasyul | 사술 |
| eusyul | 의술 |
| dokkong | 독공 |

### 3.8 훈련 경험치 (18종, offset ~3228~3296)

str_exp, instr_exp, outstr_exp, dex_exp, int_exp, con_exp, pty_exp,
kyo_exp, dob_exp, kyu_exp, jib_exp, jin_exp, amk_exp, shi_exp,
job_exp, sas_exp, eus_exp, dok_exp

### 3.9 추가 필드

hwansaeng(환생 횟수), naekongsimbub(내공심법 레벨), aa01-aa20(예약 슬롯)

---

## 4. Object Struct (492B)

3eyes(352B) 대비 **140B 확장**:

| 필드 | 타입 | 크기 | 설명 |
|------|------|------|------|
| name~flags | (기본) | 352 | 3eyes와 유사 |
| ownerlev | short | 2 | 소유자 레벨 |
| ownerrace | short | 2 | 소유자 종족 |
| ownerclass | short | 2 | 소유자 클래스 |
| ownerkill | long | 4 | 소유자 킬마크 |
| ownername[42] | char | 42 | 소유자 이름 |
| obj01~obj10 | long×10 | 40 | 인챈트 슬롯 (long) |
| obj11~obj20 | char×10 | 10 | 인챈트 슬롯 (char) |
| (패딩) | | 38 | |

---

## 5. 클래스 시스템 (21개)

### 5.1 진급 경로

```
무직(1) → 삼류무사(2) → 이류무사(3) → 일류무사(4) → 무적무사(5)
→ 초무적무사(6) → 극무적무사(7) → 영웅(8) → 천황(9) → 지존무사(10)
→ 제왕무황(11) → 무신(12) → 무삼황(14) → 선생(15)
```

관리자: 관리(13), 천사(16), 사황무사(17), 부관(18), 관(19), 대관리자(20)

### 5.2 class_stats[21]

| 클래스 | hpstart | mpstart | hp/lv | mp/lv | movestart |
|--------|---------|---------|-------|-------|-----------|
| 무직(1) | 55 | 40 | 5 | 2 | 55 |
| 삼류~극무적(2-7) | 310 | 200 | 4 | 4 | 310 |
| 영웅(8) | 900 | 800 | 5 | 5 | 900 |
| 천황~무신(9-12) | 1600 | 1400 | 5 | 5 | 1600 |
| 무삼황(14) | 3200 | 2400 | 5 | 5 | 3200 |
| 선생(15) | 6400 | 4800 | 5 | 5 | 6400 |

---

## 6. 종족 (4종)

| ID | 한국어 | 영어 | 전용 무공 계열 |
|----|--------|------|---------------|
| 1 | 고려인 | Korean | 검풍/뇌천풍 (WIND) |
| 2 | 동영인 | Japanese | 탄지법/빙설법 (WATER) |
| 3 | 광동인 | Chinese | 화염검/열염법 (FIRE) + 독 |
| 4 | 천축인 | Indian | 지진법/천동법 (EARTH) |

---

## 7. 무공/스펠 시스템 (126+ 스펠)

### 7.1 기본 스펠 (0-45): 유틸리티/치유/버프/감지/디버프

### 7.2 전투 마법 8계파 (46-125, 80기술)

| 계파 | 영역 | 종족 | 기술수 |
|------|------|------|--------|
| 검풍 | WIND | 고려인 | 10 |
| 뇌천풍 | WIND | 고려인 | 10 |
| 지진법 | EARTH | 천축인 | 10 |
| 천동법 | EARTH | 천축인 | 10 |
| 화염법 | FIRE | 광동인 | 10 |
| 열염법 | FIRE | 광동인 | 10 |
| 탄지법 | WATER | 동영인 | 10 |
| 빙설법 | WATER | 동영인 | 10 |

### 7.3 전투 데미지 공식

```
damage = dice(ndice, sdice, pdice) + dice(player_dice)
       + strength × mrand(1,8) + instrength × mrand(1,5)
```
저항 감소: PRMAGI/MRMAGI 플래그 시 감소. 티어별 2~7회 타격.

---

## 8. 명령어 시스템 (~300 엔트리)

- 이동: 66개 (한국어 방향 + 지명 + 숫자 단축키)
- 전투: 공격/때/쳐/때려
- 마법: 시전/전체
- 거래: 품목/사/팔아/가치
- 문중: 17개 문중 관련 명령
- DM: 70+ 관리자 명령 (`*` 접두사)
- 소셜: 100+ 행동 명령
- 특수: 비무신청(222), 결혼(150), 환생(173), 분신법술(420), 투자(21)

---

## 9. 플래그 시스템

| 유형 | 플래그 수 | 특이사항 |
|------|----------|---------|
| 방 | 65 | RSUVIV(36), RFAMIL(37), RBANK(39), RMARRI(41), RPGAME(44), RPFISH(51), RBETTING(52) |
| 플레이어 | 89 | PFAMIL(55), PFMBOS(57), PMARRI(60), PPRISON(76), PFREEZE(78), PBIMUA(84) |
| 몬스터 | 72 | MMBOSS(71) 보스 몬스터 |
| 오브젝트 | 58 | OGROUP(52), OJIGU(53), OBOCK(54) |
| 출구 | 23 | |

---

## 10. 고유 시스템

### 10.1 무술 훈련 시스템

- RTRAIN 플래그 방에서 훈련
- killmark(킬마크) + 골드로 무술 스킬 구매
- 단계별 비용 증가: `needmark = skill/N + skill*M`

### 10.2 분신법술 (동영인 전용)

- 환생 필수 (hwansaeng >= 1)
- 요구: sasyul>1000, str>1000, pty>1000, dex>1000
- 분신 몹 생성: 캐스터 2배 스탯 (HP/MP/이동/주사위, 최대 1억)

### 10.3 환생 시스템

- hwansaeng 필드로 환생 횟수 추적
- 환생 시 크로스종족 마법 사용 가능

### 10.4 내공심법 (naekongsimbub)

내공 수련 레벨 시스템

### 10.5 은행/결혼/게시판/문중

muhan13과 동일한 시스템 탑재

---

## 11. 데이터 규모 요약

| 엔티티 | 수량 |
|--------|------|
| 방 | 미포함 (rooms/ 누락) |
| 몬스터 | ~683 |
| 아이템 | ~1,077 |
| 클래스 | 21 |
| 종족 | 4 |
| 스펠 | 126+ |
| 명령어 | ~300 |
| 도움말 | 30 |
| 무공 계파 | 8 (종족당 2) |
| 무술 스킬 | 24 (개별 필드) |
| 무공 슬롯 | 256 (art[] 배열) |
| 스탯 종류 | 18 (5기본+13무술) |
| 착용 슬롯 | 40 |
| 플래그 (creature) | 640비트 (80B) |
| 문중 슬롯 | 16 |
| 맵 파일 | 11 |
| 문서 파일 | 18 |
| 소스 파일 | ~76 |

---

## 12. 마이그레이션 고려사항

### 12.1 새로운 파서 필요

- creature 3,380B: 3eyes/muhan13 어느 것과도 호환 불가
- object 492B: 3eyes(352B) 대비 140B 확장 (소유자/인챈트)
- 무공 데이터: mukong/ 4파일 별도 파서 필요

### 12.2 rooms/ 디렉토리 누락

현재 스냅샷에 rooms/ 없음. 맵 파일로 방 구조 추정 가능하나 실제 데이터 미포함.

### 12.3 UIR 확장 필요

- 18종 스탯 (기존 5종 대비 13종 추가)
- 무술 스킬 24종 → extensions JSONB
- art[256] 무공 배열 → 별도 테이블 또는 JSONB
- 인챈트 슬롯 20개 → extensions JSONB
- 640비트 플래그 → extensions JSONB
