# 3eyes MUD (바이너리 C struct) 데이터 전수조사

> 최종 업데이트: 2026-02-12 | 런타임 메커닉 분석 포함

## 1. 디렉토리 구조

| 디렉토리 | 파일 수 | 용도 | 마이그레이션 대상 |
|----------|---------|------|-------------------|
| rooms/ | 7,513 | 방 (바이너리, 7,439 rooms) | **YES** (현재 파싱중) |
| objmon/ | 135 | 오브젝트(o)+몬스터(m) 바이너리 | **YES** (현재 파싱중) |
| moptalk/ | 161 | NPC 대화 | **YES** (현재 파싱중) |
| help/ | 207 | 도움말 (116개) | **YES** (현재 파싱중) |
| src/ | 92 | C 소스 코드 | **부분** (global.c만) |
| board/ | 6,692 | 게시판 글 | 선택적 |
| docs/ | 4 | 문서/관리 도구 | NO |
| player/ | 417 | 플레이어 세이브 | NO |
| log/ | 66 | 서버 로그 | NO |
| bin/ | 6 | 실행파일 | NO |
| bin2/ | 13 | 실행파일 백업 | NO |
| killer/ | 0 | PK 기록 (빈) | NO |

---

## 2. 바이너리 struct 필드 커버리지

### 2.1 Room (sizeof=480)

| 필드 | Offset | 크기 | 파싱 | 비고 |
|------|--------|------|------|------|
| name (short) | 0 | 80B | **YES** | |
| rom_num | 80 | 2B | **YES** | vnum |
| pad | 82 | 2B | — | |
| long_desc (ptr) | 84 | 4B | **YES** | length-prefixed |
| short_desc (ptr) | 88 | 4B | **YES** | length-prefixed |
| obj_desc (ptr) | 92 | 4B | **YES** | length-prefixed |
| special | 96 | 2B | **YES** | |
| trap | 98 | 1B | **YES** | |
| trapexit | 100 | 2B | **YES** | |
| track | 102 | 80B | **YES** | |
| flags | 182 | 8B | **YES** | F_ISSET 비트맵 |
| random[10] | 190 | 20B | **YES** | 랜덤 몬스터 배치 |
| traffic | 210 | 1B | **YES** | |
| perm_mon[10] | 212 | 120B | **YES** | 상주 몬스터 |
| perm_obj[10] | 332 | 120B | **YES** | 상주 아이템 |
| lVisitedTime | 452 | 4B | **YES** | |
| established | 456 | 4B | **YES** | |
| lolevel/hilevel | 460 | 2B | **YES** | 레벨 제한 |
| exits (6+custom) | 44B each | var | **YES** | |
| recursive mobs/objs | var | var | **YES** | |

### 2.2 Creature (sizeof=1184)

| 필드 | Offset | 크기 | 파싱 | 비고 |
|------|--------|------|------|------|
| fd | 0 | 2B | — | 소켓 (무시) |
| level | 2 | 1B | **YES** | |
| type | 3 | 1B | **YES** | 0=PLAYER, 1=MONSTER |
| class | 4 | 1B | **YES** | 직업 1-8 |
| race | 5 | 1B | **YES** | 종족 1-8 |
| numwander | 6 | 1B | **YES** | 배회 범위 |
| alignment | 8 | 2B | **YES** | 성향 |
| str/dex/con/int/pie | 10-14 | 5B | **YES** | 스탯 5종 |
| hpmax/hpcur | 16-19 | 4B | **YES** | HP |
| mpmax/mpcur | 20-23 | 4B | **YES** | MP |
| armor | 24 | 1B | **YES** | AC |
| thaco | 25 | 1B | **YES** | THAC0 |
| experience | 28 | 4B | **YES** | |
| gold | 32 | 4B | **YES** | |
| ndice/sdice/pdice | 36-41 | 6B | **YES** | 공격 주사위 |
| special | 42 | 2B | **YES** | |
| name | 44 | 80B | **YES** | EUC-KR |
| description | 124 | 80B | **YES** | |
| talk | 204 | 80B | **YES** | 대화파일명 |
| etc | 284 | 15B | **YES** | 기타정보 |
| key[3] | 299 | 60B | **YES** | 검색키워드 |
| proficiency[5] | 360 | 20B | **부분** | 아래 상세 |
| realm[4] | 380 | 16B | **부분** | 아래 상세 |
| spells[16] | 396 | 16B | **부분** | 128비트 비트필드 |
| flags[8] | 412 | 8B | **YES** | 64비트 플래그 |
| quests[16] | 420 | 16B | **부분** | 128비트 비트필드 |
| questnum | 436 | 1B | **YES** | |
| carry[10] | 438 | 20B | **부분** | 소지 아이템 VNUM |
| rom_num | 458 | 2B | **YES** | |

**speak 필드: 존재하지 않음** — mstruct.h 완전 검증 완료. offset 436 = questnum(1B), 438 = carry[10].

### 2.3 proficiency[5] 상세

| 인덱스 | 의미 | 크기 |
|--------|------|------|
| 0 | SHARP (날붙이/검) | long (4B) |
| 1 | THRUST (찌르기/창) | long (4B) |
| 2 | BLUNT (둔기/곤봉) | long (4B) |
| 3 | POLE (장병기) | long (4B) |
| 4 | MISSILE (원거리/활) | long (4B) |

- `mod_profic()` — 숙련도/20으로 정수 퍼센트 계산
- `add_prof()` — 경험치 획득시 5개 무기+4개 영역에 분산

### 2.4 realm[4] 상세

| 인덱스 | 값 | 의미 |
|--------|-----|------|
| 0 | EARTH | 대지 마법 |
| 1 | WIND | 바람 마법 |
| 2 | FIRE | 화염 마법 |
| 3 | WATER | 물 마법 |

### 2.5 Object (sizeof=352)

| 필드 | Offset | 크기 | 파싱 | 비고 |
|------|--------|------|------|------|
| name | 0 | 70B | **YES** | |
| etc | 70 | 10B | **YES** | |
| description | 80 | 80B | **YES** | |
| key[3] | 160 | 60B | **YES** | 검색키워드 |
| use_output | 220 | 80B | **YES** | |
| value | 300 | 4B | **YES** | |
| weight | 304 | 2B | **YES** | |
| type | 306 | 1B | **YES** | |
| adjustment | 307 | 1B | **YES** | |
| shotsmax/shotscur | 308 | 4B | **YES** | |
| ndice/sdice/pdice | 312 | 6B | **YES** | |
| armor | 318 | 1B | **YES** | |
| wearflag | 319 | 1B | **YES** | |
| **magicpower** | 320 | 1B | **부분** | 마법 강화도 (+1~+3) |
| **magicrealm** | 321 | 1B | **부분** | 마법 영역 (0~4) |
| special | 322 | 2B | **YES** | |
| flags | 324 | 8B | **YES** | |
| questnum | 332 | 1B | **YES** | |

- **magicpower**: 마법 아이템의 +1/+2/+3 보너스 단계
- **magicrealm**: 0=일반, 1=EARTH, 2=WIND, 3=FIRE, 4=WATER

---

## 3. 명령어 시스템 (global.c cmdlist[])

### 3.1 구조체

```c
struct { char *cmdstr; int cmdno; int (*cmdfn)(); }
```

**총 405개 명령어** (마지막: `{ "@", 0, 0 }` 종료 마커)

### 3.2 주요 카테고리

| 카테고리 | 예시 | 수량 (추정) |
|----------|------|------------|
| 이동 | 북/남/동/서/위/아래 | ~10 |
| 조회 | 보기/누구/장비/체력 | ~20 |
| 전투 | 공격/뒤치기/강타 | ~10 |
| 마법 | 주문/수련 | ~5 |
| 상점 | 목록/구매/판매/감정 | ~10 |
| 소통 | 말하기/외침/귓속말 | ~15 |
| 시스템 | 저장/로그아웃/설정 | ~10 |
| 관리자 | `*` 접두사, dm_* 함수 | ~60 |
| 기타 | 잡다한 명령 | ~265 |

### 3.3 명령어 함수 시그니처

```c
int cmd_name(creature *ply_ptr, cmd *cmnd) {
    // cmnd->num = 파라미터 개수
    // cmnd->str[0..4] = 각 파라미터 문자열
    // cmnd->val[0..4] = 각 파라미터 숫자값
}
```

---

## 4. 스펠 시스템

### 4.1 spllist[] — 63개 스펠

```c
struct { char *splstr; int splno; int (*splfn)(); int spllv; }
```

- SVIGOR(0) ~ SUPGRADE(62), 한글 이름
- spllv: 스펠 사용 레벨 제한
- 구현 함수: offensive_spell, restore, teleport, bless 등

### 4.2 ospell[] — 26개 공격 스펠

```c
struct { int splno; char realm; int mp; int ndice; int sdice; int pdice; char bonus_type; }
```

- realm: EARTH(1)/WIND(2)/FIRE(3)/WATER(4)
- 데미지 공식: `ndice * D(sdice) + pdice`
- 마나 소비: ospell.mp
- 예: `{ SHURTS, WIND, 3, 1, 8, 0, 1 }` → 상처: 바람영역, MP3, 1d8

### 4.3 비공격 스펠

| 유형 | 예시 | 설명 |
|------|------|------|
| 회복 | restore | HP/MP 회복 |
| 이동 | teleport | 텔레포트 |
| 버프 | bless, protection | 보호/축복 |
| 상태 | detect, invisibility | 감지/투명 |

---

## 5. 추가 데이터 테이블 (global.c)

### 5.1 class_stats[13] — 직업별 스탯

| 인덱스 | 직업 | hpstart | mpstart | hp/lv | mp/lv | ndice | sdice | pdice |
|--------|------|---------|---------|-------|-------|-------|-------|-------|
| 1 | 암살자 | 55 | 50 | 6 | 2 | 1 | 6 | 0 |
| 2 | 야만인 | 60 | 40 | 7 | 1 | 1 | 8 | 0 |
| 3 | 성직자 | 50 | 55 | 5 | 3 | 1 | 4 | 0 |
| 4 | 전사 | 65 | 35 | 8 | 1 | 1 | 10 | 0 |
| 5 | 마법사 | 45 | 60 | 4 | 4 | 1 | 3 | 0 |
| 6 | 팔라딘 | 60 | 45 | 7 | 2 | 1 | 7 | 0 |
| 7 | 광전사 | 70 | 30 | 9 | 1 | 1 | 12 | 0 |
| 8 | 도적 | 50 | 45 | 5 | 2 | 1 | 5 | 0 |
| 9~12 | 관리자 | - | - | - | - | - | - | - |

### 5.2 level_cycle[14][10] — 레벨업 스탯 순환표

- 10단계 주기로 STR(1)/DEX(2)/CON(3)/INT(4)/PTY(5) 중 어떤 스탯을 올릴지 결정
- 예: Assassin = `{ CON, PTY, STR, INT, DEX, INT, DEX, PTY, STR, DEX }`

### 5.3 thaco_list[18][20] — THAC0 표

- 행: 직업별, 열: 레벨별 (1~20)
- 값: 낮을수록 명중률 좋음, 20=불가
- 관리자 직업 = 모두 -5 (무적)

### 5.4 level_exp[202] — 경험치 테이블

- 레벨 1~201 누적 경험치
- 범위: 132 (lv1) ~ 16,000,000 (lv201)

### 5.5 bonus[35] — 스탯 보정치

- STR 0~34 → 보정 -4~+7

### 5.6 클랜 데이터

| 배열 | 크기 | 용도 |
|------|------|------|
| family_str[16] | 16 | 클랜명 (한글) |
| fmboss_str[16] | 16 | 클랜장명 |
| family_num[16] | 16 | 클랜원 수 |
| family_gold[16] | 16 | 클랜 자금 |
| fam_win[17]/fam_lost[17] | 17 | 클랜전 승패 |

### 5.7 런타임 로드 데이터

| 데이터 | 소스 | 상태 |
|--------|------|------|
| quest_exp[101] | LOGPATH/quests 파일 | 런타임 로드, 파서 미지원 |
| race_adj[] | extern 선언만 | 정의 미발견 (컴파일 바이너리?) |
| lev_title[][] | extern 선언만 | 정의 미발견 |
| article[]/number[] | extern 선언만 | 정의 미발견 |

---

## 6. 텍스트 데이터

### 6.1 moptalk/ — NPC 대화 (161 files)

- talk/{name}-{level} 포맷 — 키워드/응답 번갈아 저장
- **파싱 완료**: talk_parser.py로 extensions에 저장

### 6.2 help/ — 도움말 (207 files → 116 entries)

- help.1, help.2 ... 각 파일 = 1개 도움말
- **파싱 완료**: help_parser.py

### 6.3 objmon/ddesc — 상세 설명

- 몬스터 상세설명 병합 — **파싱 완료**

---

## 7. Board 시스템

```
board/
  board_index      (인덱스 파일, 236KB, 바이너리)
  board_list       (목록 파일, 308B, 텍스트)
  family/          (가족 게시판)
  family1-15/      (클랜 게시판 16개)
```

- board_index: 바이너리 인덱스
- 게시판 17개 (메인 + 클랜 16개)
- **현재 파싱: NO**

---

## 8. 은행(Bank) 시스템

```
player/{id}/bank/{id}     (플레이어 금고)
killer/{id}/bank/{id}     (킬러 금고)
```

- object 구조체 저장 (컨테이너)
- load_bank() / save_bank() 관리

---

## 9. 소스 코드 기반 미파싱 데이터

| 파일 | 크기 | 추출 가능 데이터 | 중요도 |
|------|------|-----------------|--------|
| magic1~8.c | 31~54KB | 스펠 구현 (63개) | 높음 |
| command1~9.c | 21~69KB | 명령어 구현 | 중간 |
| player.c | 54KB | 플레이어 시스템 | 중간 |
| update.c | 45KB | 틱 업데이트 | 중간 |
| creature.c | 24KB | 몬스터 AI | 중간 |
| poker.c/poker2.c | 13~36KB | 포커 게임 | 선택적 |
| map.c | 13KB | 맵 시스템 | 선택적 |
| bank.c | 11KB | 은행 시스템 | 선택적 |
| board.c | 21KB | 게시판 시스템 | 선택적 |

---

## 10. 커버리지 요약

### 현재 (재평가: ~85%)

| 카테고리 | 파싱 비율 | 비고 |
|----------|-----------|------|
| 방 | **98%** | struct 거의 전 필드 |
| 몬스터 | **92%** | 기본 전부, **speak 필드 미존재 확인** |
| 아이템 | **95%** | magicpower/magicrealm 부분 파싱 |
| NPC 대화 | **100%** | moptalk 완전 파싱 |
| 도움말 | **100%** | |
| 존 (room→spawn) | **100%** | room 내 recursive mob/obj |
| 게임 설정 | **100%** | global.c 테이블 (thaco/exp/class/level_cycle) |
| **스펠 시스템** | **30%** | 이름만 추출, ospell[] 데미지/영역 미파싱 |
| **명령어** | **0%** | 405개 cmdlist[] 미추출 |
| **전투 메시지** | **0%** | 소스 내 하드코딩 |
| **게시판** | **0%** | 6,692개 글 |
| **포커/맵** | **0%** | 미니게임 |

### 95% 달성 필요 작업

1. **스펠 데이터 추출** — ospell[26] 데미지/영역/MP + 비공격 스펠 효과
2. **명령어 목록 추출** — cmdlist[405] 이름/번호/카테고리
3. **proficiency/realm 매핑 강화** — 5+4 숙련도 UIR 반영
4. **magicpower/magicrealm** — 아이템 마법 강화 UIR 반영
5. (선택) 게시판 글 변환 — board/ 데이터

---

## 11. 런타임 메커닉

### 11.1 타이밍 시스템 (update.c)

메인 루프 `update_game()` — 매초 호출, 시간 기반 분기:

| 시스템 | 간격 | 함수 | 설명 |
|--------|------|------|------|
| 사용자 업데이트 | 20초 | `update_users()` | HP/MP 회복, 유휴 타임아웃 |
| 랜덤 몬스터 | 20초 | `update_random()` | 방별 랜덤 스폰 |
| 활성 몬스터 AI | 1초 | `update_active()` | 전투/배회/대화 |
| 클래스 경험치 | 60초 | `update_class()` | 클래스별 보너스 |
| 게시판 저장 | 300초 | `save_board()` | 게시판 백업 |

### 11.2 전투 시스템 (command5.c: attack_crt)

**명중 판정**: `thaco - AC/10`

```
n = thaco - crt_ptr->armor/10
공포 상태: n += 2, 실명 상태: n += 5
판정: mrand(1,30) >= n 이면 명중 (d30 기반, tbaMUD의 d20과 다름)
```

**데미지 공식**:

```
무기 공격: mdice(weapon) + bonus[strength] + profic(ply, weapon_type)/10
맨손(야만인): mdice(player) + bonus[strength] + comp_chance(player)
일반 맨손: mdice(player) + bonus[strength]
마법/성직자: 별도 공식 (무기 있으면 무기 주사위만, 없으면 맨손)
```

- `bonus[]`: 스탯 보정 배열 (global.c, 35개 항목, -4 ~ +7)
- `profic()`: 숙련도/20 정수 퍼센트
- `comp_chance()`: 비무장 전투 보정

**다중 타격**:

```
기본 1회 + 추가 확률:
  - PUPDMG 플래그 + (INVINCIBLE lv100+): 확률적 2타
  - INVINCIBLE 이상: 추가 확률적 3타
  - 랜덤: mrand(0,3)>2 → +1회, 추가로 1/4 확률 +1회
```

**크리티컬**: `mod_profic()` 확률 또는 `OALCRT` 무기 플래그 → 급소 명중 (3~6배 보너스)

**그림자 공격**: `SHADOW_ATTACK` 상태일 때 첫 공격에 그림자 동시 공격 (크리티컬 포함)

**무기 내구도**: 25% 확률로 `shotscur--`, 0이 되면 무기 파손

### 11.3 사망 시스템 (creature.c: die)

**몬스터 사망**:

```
1. 적대 리스트(first_enm) 순회 → 기여도 기반 경험치 분배
   - expdiv = (experience * damage_dealt) / MAX(hpmax, 1)
   - MIN(expdiv, experience), MAX(expdiv, 0)
2. alignment 변동: -victim_alignment/5 (범위 -1000~+1000)
3. 전리품: 보유 아이템 → 방에 드롭
4. 골드: nBombDie==0이면 공격자에게 직접 이전, 아니면 MONEY 오브젝트 생성
5. MPERMT 플래그: die_perm_crt() → 상주 몬스터 리스폰 타이머 갱신
6. 퀘스트: questnum 있으면 순차 퀘스트 완료 처리 (quest_exp[] 보상)
7. 소환: MSUMMO 플래그 → summon_crt() 호출 (보스 사후 소환)
```

**플레이어 사망 (PvE)**:

```
1. 경험치 패널티: -(level_exp[level] - level_exp[level-1]) * 3/4
   - INVINCIBLE: x5 (최소 200,000)
   - CARETAKER: x5 (최소 1,000,000)
   - CARE_II+: hpmax*800 + mpmax*1000
   - 경험치 최소 -1,000,000,000 하한
2. HP/MP 완전 회복 (PvE 사망시 풀회복, PvP는 HP만)
3. 상태이상 해제 (독/질병)
4. AC/THAC0 재계산
5. 영혼방(rom 11971)으로 이동
6. 전역 사망 공지
```

**PvP 추가**:

```
- PK 타이머: mrand(7,14) * 86400L (7~14일 쿨다운)
- RSUVIV 방: 서바이벌 존 → 무술대회 랭킹 시스템 (InsertMusulRank)
- 가문전(클랜전): fam_win/fam_lost 카운트, AT_WAR 상태
```

### 11.4 HP/MP 회복 (update.c: update_users)

```
매 20초:
- bonus_power += 4 (에너지 충전, 최대 100)
- HP 회복: class/level/position 기반
- MP 회복: class/level 기반
- 유휴 타임아웃: 비로그인 30초 / 플레이어 180초
```

### 11.5 랜덤 몬스터 스폰 (update.c: update_random)

```
매 20초, 각 방별:
- 판정: mrand(1,100) > room.traffic → 스폰
- room.random[10]에서 랜덤 선택 (VNUM)
- 확률: 90% 1마리, 6% 2마리, 4% 3마리
- 방 최대 인원 초과 시 스폰 안됨
```

### 11.6 몬스터 AI (update.c: update_active)

```
매 1초 (활성 몬스터만):
1. 공격 간격: DEX < 20 → 3초, DEX ≥ 20 → 2초
2. 대상 선택: first_enm (적대 리스트) 순서
3. 달인/관리자(INVINCIBLE+) 장기 전투 보호: 300초 후 경험치 0
4. 배회: numwander > 0이면 랜덤 출구로 이동
5. 대화: talk 파일 매핑, 동일 이름+레벨 매칭
```

### 11.7 이동 시스템

```
기본 이동: 방향 명령 (북/남/동/서/위/아래) + 커스텀 출구
- XCLOSD: 닫힌 문 (open/close/lock/unlock)
- XLOCKD: 잠긴 문 (key 아이템 필요)
- XSECRT: 숨겨진 문 (detect로 발견)
- 비행: F_ISSET(PLEVIT) 필요한 특수 출구
- DT(Death Trap): 즉사 방
```

### 11.8 마법 시스템 (magic1.c: cast)

```
1. spllist[] 순회 → 스펠 이름 매칭 (prefix 허용, 중복시 실패)
2. RNOMAG 방 플래그: 마법 불가
3. 쿨다운: LT_SPELL
   - 마법사/성직자: 3초
   - 그 외 플레이어: 5초
   - 관리자: 1초
   - 드래곤슬레이브(56): +3초
   - 기가슬레이브(57): +25초
   - 58~61번: +1초
4. offensive_spell: ospell[] 참조 → ndice*D(sdice)+pdice 데미지
5. 비공격: restore/teleport/bless/protect 등 직접 함수 호출
```

### 11.9 세이브/퍼시스턴스

```
- 플레이어 저장: PLAYER_DATA_PATH/{name} (바이너리 creature struct)
- .tmp 파일: 저장 중 크래시 보호 (존재시 복구 시도)
- 은행: player/{id}/bank/{id} (object struct)
- 게시판: board/ 디렉토리
- 퀘스트 경험치: LOGPATH/quests 런타임 로드
```

### 11.10 로그인 플로우 (command1.c: login)

```
case 0: ANSI 선택 (1=NoAnsi) → 로고 출력
case 1: 이름 입력 (한글 1~5자, ishan() 검증)
        → load_ply() 성공: 기존 캐릭터 → 비밀번호
        → load_ply() 실패: .tmp 복구 시도 → 킬러 파일 확인 → 신규 생성
case 2: 신규 캐릭터 확인 (1=예, 2=아니오)
        → create_ply 진행 (성별 선택)
case 3: 비밀번호 확인 (password = creature.talk 필드에 저장!)
        → 마스터 패스워드 존재 ("@rladydrmsWkd@")
```

**특이사항**: 비밀번호가 `creature.talk` 필드에 평문 저장. 마스터 패스워드로 모든 계정 접근 가능.

### 11.11 레벨업

```
- 경험치 테이블: level_exp[202] (global.c)
- 레벨업: experience >= level_exp[level] 충족시
- 스탯 증가: level_cycle[class][level%10] → STR/DEX/CON/INT/PTY 중 1 증가
- HP/MP 증가: class_stats[class].hp/mp per level
- 최대 레벨: 201 (일반), 관리자 급 INVINCIBLE~DM 별도
```

### 11.12 통신 시스템

```
- say (말하기): 같은 방 전달
- broadcast: b_all() → 전체 서버
- whisper: 귓속말
- 외침: shout → 전체
- 클랜 채팅: family 기반
- DM 전용: b_wiz() → 관리자만
```

### 11.13 DB 설계 포인트

| 메커닉 | 필요 테이블/필드 |
|--------|-----------------|
| 기여도 경험치 | `combat_log` (attacker, target, damage) — 실시간 분배 |
| 상주 몬스터 | `room_perm_mobs` (room_vnum, mob_vnum, respawn_interval) |
| 퀘스트 순차 | `quest_progress` (player_id, quest_slot, completed) |
| 랜덤 스폰 | `room_random_mobs` (room_vnum, mob_vnum, traffic_threshold) |
| 클랜전 | `clan_wars` (clan1, clan2, score1, score2, status) |
| 무술대회 | `musul_ranking` (class, rank, player_name) |
| 숙련도 | `player_proficiencies` (player_id, weapon_type, points) |
| 마법 영역 | `player_realms` (player_id, realm_type, points) |
| d30 전투 | 전투 시스템: d30 기반 (tbaMUD d20과 다름) |
