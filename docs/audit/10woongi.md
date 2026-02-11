# 10woongi (LP-MUD/FluffOS) 데이터 전수조사

> 최종 업데이트: 2026-02-11 | 심층 분석 완료

## 1. 디렉토리 구조

| 디렉토리 | 파일 수 | 용도 | 마이그레이션 대상 |
|----------|---------|------|-------------------|
| 방/ | 20,209 | 방+몹+아이템 (주 데이터) | **YES** (현재 파싱중) |
| 물체/ | 396 | 아이템 (별도 정의) | **YES** (현재 파싱중) |
| 기술/ | 367 | 기술 구현 (공격/방어/특수/필살/문파/몹) | **부분** — 헤더만 파싱 |
| 명령어/ | 256 | 플레이어(101) + 제작자(144) 명령 | **YES** (플레이어만 파싱중) |
| 도움말/ | 72 | .help 파일 | **YES** (현재 파싱중) |
| 관리자/ | 70 | 시스템 (문파, 게시판, 순위, 로그인 등) | **부분** — 미탐색 |
| 구조/ | 51 | Base class 정의 | 파싱 참조용 |
| 문서/ | 29 | 인게임 문서 (길잡이, 줄거리 등) | 선택적 |
| 삽입파일/ | 16 | 헤더 (직업, 기술, 설정 등) | **YES** (현재 파싱중) |
| 작업방/ | 6 | 개발자 작업 공간 | NO |
| 기록/ | 1 | 통계/드라이버 기록 | NO |
| 방0~방5 | 15K~23K | 방/ 의 백업 복사본 | NO (무시) |
| log/ | 1 | 로그 | NO |
| 로긴중/ | 0 | 접속중 플레이어 (런타임) | NO |
| 여론조사/ | 0 | 빈 디렉토리 | NO |
| 유저데이타/ | 0 | 빈 디렉토리 | NO |
| 은퇴백업/ | 0 | 빈 디렉토리 | NO |
| 임시/ | 0 | 빈 디렉토리 | NO |
| 저장/ | 0 | 런타임 저장 (편지, 플레이어) | NO |

**총 LPC 소스 파일**: 약 125,185개, 디렉토리 2,042개

---

## 2. 엔티티 타입별 inherit 분포

| inherit | 수량 | 현재 파싱 | 설명 |
|---------|------|-----------|------|
| LIB_ROOM | 17,593 | YES | 방 |
| LIB_MONSTER | 1,216 | YES | 몬스터 (방/*/mob/ + 물체/ 일부) |
| LIB_ARMOR | 374 | YES | 방어구 |
| LIB_OBJECT | 366 | **NO** | 일반 오브젝트 (상자, 열쇠 등) |
| LIB_ITEM | 313 | YES | 기타 아이템 |
| LIB_WEAPON | 237 | YES | 무기 |
| LIB_DAEMON | 192 | N/A | 시스템 데몬 (명령어 등) |
| LIB_FOOD | 65 | YES | 음식 |
| LIB_BOARD | 24 | **NO** | 게시판 |
| LIB_AMGI | 11 | YES | 암기 (투척무기) |
| LIB_MAILER | 5 | **NO** | 우편함 |
| LIB_C_BOARD | 3 | **NO** | 커뮤니티 게시판 |
| LIB_STORAGE | 1 | **NO** | 저장소 |
| LIB_PLAYER | 1 | N/A | 플레이어 base |

---

## 3. 몬스터 전체 속성 — 947개 파일

> 소스: `lib/구조/monster.c` (982줄) 심층 분석

### 3.1 현재 파싱 중 (25개)

| set함수 | 사용횟수 | UIR 매핑 |
|---------|----------|----------|
| setName | 997 | keywords (일부) |
| setID | 952 | keywords |
| setShort | 1,218 | short_description |
| setLong | 1,011 | long_description |
| setGender | 931 | sex |
| randomStat | - | level (간접) |
| setStat | 2,401 | extensions.stats |
| setExp | 214 | experience |
| setAdjExp | 458 | extensions.adj_exp |
| setGold | 110 | gold |
| setMaxHp | 683 | extensions.max_hp |
| setMaxSp | 470 | extensions.max_sp |
| setArmorClass | 382 | armor_class |
| setAggresive | 91 | action_flags |
| setAggresiveMunpa | 163 | action_flags |
| setNoAttack | 373 | action_flags |
| setRace | 413 | extensions.race |
| setMunpa | 248 | extensions.munpa |
| setWander | 310 | extensions.wander |
| setChat | 428 | extensions.chat |
| setChatChance | 431 | extensions.chat_chance |
| clone_object (items) | - | extensions.inventory |
| setProp | 723 | extensions.props |
| setBasicAttackMessage | 413 | extensions.attack_message |
| setupBody | 1,137 | (암묵적) |

### 3.2 전투 속성 (monster.c 분석)

```
ArmorClass: setArmorClass(int) - 방어력
WeaponClass: setWeaponClass(int) - 공격력
HP/SP/MP: setupBody() 함수에서 stat 기반 계산
  HP = 80 + 6*(sigma(stat_gigol)/30)  [x2 또는 x4 설정별]
  SP = 80 + sigma(stat_negong*2+stat_jihe)/30
  MP = 50 + sigma(stat_min)/15
```

### 3.3 행동/타겟 속성

| 속성 | 함수 | 의미 |
|------|------|------|
| Aggresive | setAggresive() | 무조건 공격 |
| AggresiveMunpa | setAggresiveMunpa() | 문파 적 공격 |
| UnconditionalAttack | setUnconditionalAttack() | 투명 무시 공격 |
| AggresiveReaction | setAggresiveReaction(int) | 역공격 확률 |
| Wander | setWander(int) | 배회 확률 (0-100) |
| NoAttackWander | setNoAttackWander() | 전투중 배회 금지 |
| TopLevelAttack | setTopLevelAttack() | 가장 높은 레벨 적 자동 타겟 |
| TankerAttack | setTankerAttack() | 그룹 탱커 자동 타겟 |
| HighLevelAttack | setAggHigh(int level) | 특정 레벨 이상만 공격 |
| HighLevelAttackNo | setAggHighAttackNo(int) | 레벨 공격 중 재공격 금지 |

### 3.4 경험치/명성

| 속성 | 함수 | 의미 |
|------|------|------|
| Exp | setExp(int) | 처치시 경험치 |
| ExpType | setExpType(int) | 0=일반(기본60%+보너스), 1=수치형(player_level 기반) |
| Fame | addFame(int) | 명성 (경험치와 별도) |
| setAdjExp | setAdjExp(float) | 스탯 기반 경험치 조정: `((합산스탯/5)^2/12)*adjust` |

### 3.5 6종 스탯

| 스탯 | 변수명 | 용도 |
|------|--------|------|
| 힘 | stat_power | 물리 공격 |
| 내공 | stat_negong | SP 관련, 마법력 |
| 지혜 | stat_jihe | MP 관련 |
| 기골 | stat_gigol | HP 관련 |
| 민첩 | stat_min | 회피, 급진 판정 |
| 투지 | stat_tuji | 전투 의지 |

### 3.6 자동생성 함수

| 함수 | 역할 |
|------|------|
| randomStat(int level) | 레벨 기반 스탯 자동 생성 (level/5 범위 랜덤), Gold=level*2~5, AC/WC=level/4 |
| randomStatDefence() | 방어형 특화 |
| randomStatAttack() | 공격형 특화 (공격 x3, 경험치 x3) |

### 3.7 대사/기타

| 속성 | 함수 | 의미 |
|------|------|------|
| Chat | setChat(string *str) | 무작위 대사 배열 |
| ChatChance | setChatChance(int) | 대사 발동 확률 |
| MobKind | setMobKind(int) | 0=일반, 1=특수 |

### 3.8 누락 — 중요 (게임플레이 영향)

| set함수 | 사용횟수 | 의미 | 권장 UIR 매핑 |
|---------|----------|------|---------------|
| setSkillData | 1,319 | 몬스터 보유 기술 (전투 핵심) | extensions.skill_data |
| setHp | 506 | 현재 HP 설정 (maxHp와 별도) | extensions.hp |
| setSp | 326 | 현재 SP | extensions.sp |
| setMp | 217 | 현재 MP (이동력) | extensions.mp |
| setMaxMp | 330 | 최대 MP | extensions.max_mp |
| setSaveData | 211 | 저장 데이터 (장비/상태 지속) | extensions.save_data |
| setAggHigh | 174 | 높은 레벨 공격성 | extensions.agg_high |
| setNoAttackWander | 162 | 비공격 배회 | extensions.no_attack_wander |
| setAttackFunc | 160 | 특수 공격 함수 | extensions.attack_func |
| setSpecialSkillAI | 136 | 기술 AI (전투 패턴) | extensions.skill_ai |
| setMission | 135 | 퀘스트/임무 NPC | extensions.mission |
| setWeaponClass | 100 | 무기 등급 | extensions.weapon_class |
| setMunpaMsg | 99 | 문파 메시지 | extensions.munpa_msg |
| setSkillDatas | 58 | 복수 기술 데이터 | extensions.skill_datas |
| setTankerAttack | 67 | 탱커 공격 패턴 | extensions.tanker_attack |
| setFame | 78 | 명성 | extensions.fame |
| setAllSay | 63 | 전체 말하기 | extensions.all_say |

### 3.9 누락 — 선택적

| set함수 | 사용횟수 | 의미 |
|---------|----------|------|
| setNoPrompt | 41 | 프롬프트 숨김 |
| setLarge | 33 | 대형 몬스터 |
| setChilboStat | 29 | 칠보 스탯 |
| setDieFunction | 27 | 사망 시 특수 함수 |
| setSmall | 22 | 소형 몬스터 |
| setHair | 21 | 외모 |
| setFirstDieFunction | 17 | 최초 사망 함수 |
| setMove | 15 | 이동 패턴 |

---

## 4. 아이템 전체 속성 — 1,094개 파일

> 소스: `lib/구조/item.c` (518줄), `weapon.c` (227줄), `armor.c` (212줄) 등

### 4.1 현재 파싱 중 (17개)

| set함수 | 사용횟수 | UIR 매핑 |
|---------|----------|----------|
| setName | 1,093 | keywords (일부) |
| setID | 1,086 | keywords |
| setShort | 1,085 | short_description |
| setLong | 1,088 | long_description |
| setMass | 970 | weight |
| setValue | 660 | cost |
| setType | 601 | extensions.type (장착 슬롯) |
| setWeapon | 228 | values[1] (무기 데미지) |
| setSpWeapon | 22 | values[1] (특수무기) |
| setTwoHand | 209 | extensions.two_hand |
| setArmor | 354 | values[0] (방어력) |
| setSpArmor | 31 | extensions.sp_armor |
| setStatUp | 85 | affects |
| setLimitLevel | 200 | extensions.limit_level |
| setMaxLifeCircle | 362 | extensions.max_life |
| setInvis | - | extra_flags |
| setStat (via stat_ups) | 425 | affects |

### 4.2 기본 속성 (item.c 518줄)

| 카테고리 | 속성 | 설명 |
|---------|------|------|
| 핸들링 | setMass(int) | 무게 |
| | setType(string) | 아이템 타입 분류 |
| | setInvis(mixed) | 숨김 (int 또는 함수) |
| | setPreventGet/Drop/Put() | 획득/버림/보관 제약 |
| 가치 | setValue(int) | 판매가 |
| | setRepair(int) | 수리 가능 여부 |
| | setOver(int) | 중복 착용 허용 |
| | setWearNumber(int) | 최대 착용 수량 |
| 내구도 | setMaxLifeCircle(int) | 최대 내구도 |
| | getLifeCircle() | 현재 내구도 |
| | subLifeCircle(int) | 내구도 감소 |
| 스탯보정 | setStatUp(str, a) | 힘/내공/지혜/기골/민첩/투지 보너스 → setProp("X보너스", a) |
| | setArmorPercentUp(int) | 방어율 증가 |
| 제약 | limitStat | 착용 최소 스탯 요구 |
| | LimitGender | 성별 제한 |
| | LimitAge | 나이 제한 |
| 퍼시스턴트 | SaveData | 플레이어별 데이터 ("수리가능횟수", "남은시간" 등) |

### 4.3 무기 속성 (weapon.c 227줄)

| 속성 | 타입 | 설명 |
|------|------|------|
| WeaponSize | int | TINY(1), SMALL(2), MEDIUM(3), LARGE(4), HUGE(5) |
| WeaponType | int | PIECING(1), SLASH(2), BLUDGE(3), SHOOT(4) |
| MinDamage | int | 최소 데미지 |
| DamageRange | int | 데미지 범위 (1-10) |
| SpeedFactor | int | 공격 속도 페널티 |
| TwoHanded | int | 양손 무기 |
| Secondary | int | 보조 무기 가능 |
| NeedArrow | int | 화살 필요 여부 |
| HitMessage | string* | 공격 메시지 배열 |
| RequireLevel | int | 최소 레벨 |
| RequireWeaponSkill | int | 필요 무기 스킬 |
| RequireRace | string* | 종족 제약 |
| RequireClass | string* | 직업 제약 |
| upgrade | string | 업그레이드 상태 |
| sp_upgrade | string | SP 업그레이드 상태 |

### 4.4 방어구 속성 (armor.c 212줄)

| 속성 | 타입 | 설명 |
|------|------|------|
| ArmorClass | int | AC 값 |
| Royal | int | 로얄 방어구 표시 |
| LimitLevel | int | 최소/최대 레벨 |
| LimitAge | int | 나이 제약 |
| LimitGender | string | 성별 제약 |
| upgradeArmor | string | 업그레이드 상태 |
| upgradeSpArmor | string | SP 방어 업그레이드 |
| EquipMessage | function | 착용 메시지 콜백 |
| UnequipMessage | function | 해제 메시지 콜백 |

### 4.5 특수 아이템 타입

| 타입 | 소스 파일 | 줄 수 | 고유 속성 |
|------|----------|-------|----------|
| 음식 | food.c | 133 | food_space(포만도), food_type(1=음식/2=음료/3=냄새), foodFunction(효과 콜백) |
| 음료 | drink.c | 92 | HPup(HP회복, -1=완전), SPup(SP회복), EatMessage(음용 메시지) |
| 활 | bow.c | 501 | WeaponSize/MinDamage/DamageRange/SpeedFactor/Magazine/eventShoot |
| 방패 | shield.c | 264 | 방패 전용 AC, 불균형 유형 |
| 횃불 | torch.c | 202 | 밝기, 지속시간 |
| 암기 | amgi.c | 96 | 투척 무기 |
| 문 | door.c | 186 | 잠금/열기/닫기 매핑 |

### 4.6 누락 — 중요

| set함수 | 사용횟수 | 의미 | 권장 UIR 매핑 |
|---------|----------|------|---------------|
| setPreventDrop | 533 | 드롭 방지 (귀속 장비) | extensions.prevent_drop |
| setAttackMessage | 233 | 공격 메시지 (무기) | extensions.attack_message |
| setRealState | 171 | 실제 상태 | extensions.real_state |
| setSaveData | 145 | 저장 데이터 | extensions.save_data |
| setUpgradeWeapon | 104 | 무기 강화 데이터 | extensions.upgrade_weapon |
| setFood | 100 | 음식 데이터 (포만/회복) | extensions.food |
| setDrink | 96 | 음료 데이터 | extensions.drink |
| setPreventGet | 73 | 획득 방지 | extensions.prevent_get |
| setEquipMessage | 70 | 장착 메시지 | extensions.equip_message |
| setWieldMessage | 65 | 착용 메시지 | extensions.wield_message |
| setFoodFunction | 63 | 음식 특수 효과 | extensions.food_func |
| setUnwieldMessage | 44 | 해제 메시지 | extensions.unwield_message |
| setFoodSpace | 43 | 음식 용량 | extensions.food_space |
| setLimitGender | 28 | 성별 제한 | extensions.limit_gender |
| setMaxMass | 21 | 최대 무게 (용기) | extensions.max_mass |

### 4.7 LIB_OBJECT 누락 (366개)

현재 obj_parser의 `ITEM_INHERITS`에 `LIB_OBJECT`가 없어 366개 아이템이 완전히 무시됨.
상자, 열쇠, 기타 비장비 오브젝트 해당.

---

## 5. 기술 시스템 — 367개 LPC 파일

> 소스: `lib/기술/` 하위 디렉토리 심층 분석

### 5.1 기술 파일 분포

| 하위 | 수량 | 설명 |
|------|------|------|
| 공격/ | 21 | 공격 기술 (육합권, 비도련 등) |
| 방어/ | 13 | 방어 기술 |
| 특수/ | 34 | 특수 기술 |
| 필살기/ | 4 | 필살기 |
| 문파/ | 25 | 문파 전용 기술 (자하신공, 천풍광세검 등) |
| 몹/ | 260 | NPC 전용 기술 |

### 5.2 기술 파일 표준 구조

```c
// 상수 정의
#define SKILL_NAME    "육합권"     // 기술 이름
#define SKILL_MASTER  100          // 마스터 레벨
#define TURN          4            // 총 턴 수
#define ATTACK_TURN   3            // 공격 발동 턴
#define ATTR          0            // 0=물리, 1+=마법
#define TYPE_NUM      2            // 데미지 타입 수
#define EXP_COUNT     10           // 숙련도 획득 확률

// 핵심 함수
startSkill(source, str)            // 기술 개시 (HP/SP/MP 소비 검사)
skillMain(source, now_turn)        // 심박마다 호출, 턴 진행
endSkill(source)                   // 기술 완료
damageRoutine(source, type)        // 데미지 공식 계산
messageRoutine(source, target, damage, type)  // 3단계 메시지 출력
```

### 5.3 데미지 공식

```
기본 공식: (스탯1*계수 + 스탯2*계수 + skill*4~5 + 내공*8~10) / 분모
데미지 배분: 스탯 40% + 기술 40% + 내공 20%

급진(크리티컬): 민첩 >= random(200)일 때
  → damage += (damage/10)*14 + random(damage/5)  [약 14배 추가]
  일반: damage += random(damage/5)
```

### 5.4 숙련도 시스템

```
getSkillData(SKILL_NAME)    → 현재 숙련도 (0-100)
addSkillData(SKILL_NAME, 1) → 1 증가
getSkillUpExp(a) = ((a+9)^2/10)^2 + 2000
SKILL_MASTER(100) 도달시 전체 공지

getStatStatus("힘") → 1(주요)/2(보조)/0(미사용)
```

### 5.5 현재 파서 상태

- `삽입파일/기술.h`에서 51개 기술 **이름/레벨/직업만** 추출
- 실제 구현 파일 367개는 **완전 미파싱**
- 상수(TURN/ATTACK_TURN/ATTR/TYPE_NUM 등), 데미지 공식, SP/MP 소비 미추출

---

## 6. 문파(길드) 시스템 — 7개 문파

> 소스: `lib/관리자/문파/` 심층 분석

### 6.1 문파 목록

| 문파 | 성향 | 파일 크기 |
|------|------|----------|
| 곤륜파 | 정파 | 일반 |
| 명교 | 사파 (최대 규모) | 30KB |
| 무당파 | 중립 | 일반 |
| 신선궁 | 정파 | 일반 |
| 일월신교 | 사파 | 일반 |
| 개방 | 매핑/동맹 중개 | 일반 |
| 동맹 | 동맹 관계 관리 | 일반 |

### 6.2 문파 구조 (명교.c 분석)

```c
#define MUNPA         "명교"
#define LEADER        "호장"         // 리더 NPC 이름
#define LEADER_LEVEL  "장주"         // 리더 직위
#define SUBLEADER_LEVEL "부장주"     // 부리더 직위
#define DATA_PATH     "/관/명교/명교/data"
#define MAX_MUD       MAX_DRIVER     // 최대 100명

int jejaLevel = 100                  // 제자 레벨 기본값
int boardHp = 10000                  // 게시판 HP (안전지역)
int shopLevel = 1                    // 상점 레벨
```

### 6.3 문파 메커니즘

| 기능 | 설명 |
|------|------|
| 리더/부리더 | 리더 1명 + 부리더 최대 4명, save_object()로 퍼시스턴트 |
| 제자 시스템 | jejaLevel 기반 가입 조건 |
| 경제 | 문파경제.c — 상점/몹소환/자금 |
| 게시판 | 문파 전용 게시판 (boardHp=10000 안전지역) |
| 공략 | 소공략/대공략 타이머, attackRoom 매핑 |

**현재 파싱: NO** — 문파 시스템 데이터는 완전 미추출

---

## 7. NPC 특수유형

> 소스: `lib/구조/merchant.c`(408줄), `dealer.c`(162줄), `banker.c`(126줄), `healer.c`(111줄)

### 7.1 상인 (Merchant) — 408줄

```
addBuyItemList(name, file, cost%)   // 구매 상품 추가
addSellItemList(name, file, cost%)  // 판매 상품 추가
cmdBUY(str) / cmdSELL(str) / cmdLIST() / cmdINFO()
```

- 구매: 정가의 100~50% (cost 파라미터)
- 판매: 정가의 75% 회수
- 무기/방어구/방패/음식류 타입 분류

### 7.2 거간꾼 (Dealer) — 162줄

- 위탁 판매 시스템 (100개 제한)
- 구매가: 정가의 75%, 판매비: 정가의 25%

### 7.3 은행원 (Banker) — 126줄

- cmdDEPOSIT/cmdWITHDRAW/cmdBALANCE
- 최대 입금: 100,000,000 골드

### 7.4 치료사 (Healer) — 111줄

- HP_HEAL_FEE=3, SP_HEAL_FEE=5
- canHealHP/canHealSP 플래그

**현재 파싱: NO** — 전부 미파싱

---

## 8. 플레이어 구조 — player.c (2,529줄)

### 8.1 인적 정보

| 속성 | 타입 | 설명 |
|------|------|------|
| Password | string | bcrypt 해시 |
| RealName | string | 실명 (선택) |
| Gender | string | 성별 |
| Race | string | 종족 |
| Spouse | string | 배우자 |
| Position | string | 직책 (기본: "일반") |

### 8.2 게임 상태

| 속성 | 타입 | 설명 |
|------|------|------|
| Age | int | 게임 나이 (초 단위) |
| LastAge/Start/LastSave | int | 시간 기록 |
| lastConnect/lastDeConnect | int | 접속 기록 |
| munpa/job_level/munpaNumber | mixed | 문파 소속 |

### 8.3 무기/인벤토리

| 속성 | 타입 | 설명 |
|------|------|------|
| right_hand/left_hand | object | 양손 무기 |
| TwoHandItem | object | 양손 무기 참조 |
| MaxCarriedMass | int | 최대 무게 (기본 1000) |
| CarriedMass | int | 현재 무게 |
| AutoLoad | mixed* | 부팅시 자동로드 목록 |

### 8.4 UI/채팅

| 속성 | 타입 | 설명 |
|------|------|------|
| ChatChannel | int | 채팅채널 (1/0) |
| StatusChannel | int | 상태채널 |
| ExitDescription | int | 출구 설명 모드 (0-4) |
| Brief | int | 간단한 설명 모드 |
| StatusMode | int | 상태 표시 모드 |
| no_prompt | int | 프롬프트 숨김 |

### 8.5 금융/시스템

| 속성 | 타입 | 설명 |
|------|------|------|
| Bank | int | 은행 잔액 |
| RefuseTalk | string* | 거부 목록 |
| Beacon | string | 비콘 마크 |
| Quest/Event | string | 퀘스트/이벤트 진행 |
| pk_mark/die_mark | int | PK/사망 마크 |
| Fishing | int | 낚시 상태 |
| real_hungry/max_hungry | int | 배고픔 시스템 |
| KillCount | int | 킬 카운트 |

### 8.6 모듈 파일

```c
#include "./savedata.c"              // SaveData 맵
#include "./gold.c"                  // 골드 관리
#include "./marry.c"                 // 결혼 시스템
#include "./mission.c"              // 미션 시스템
#include "./플레이어/칠보.c"        // 칠보갑주
#include "./플레이어/플레이어바디.c" // 신체 시스템
```

---

## 9. 방 추가 속성 — room.c (1,036줄)

### 9.1 랜덤 생성

| 속성 | 타입 | 설명 |
|------|------|------|
| RandomMonster | string* | 랜덤 몬스터 경로 배열 |
| RandomItem | string* | 랜덤 아이템 경로 배열 |
| MonsterRate | int* | 각 몬스터 출현율 |
| ItemRate | int* | 각 아이템 출현율 |

### 9.2 방 플래그

| 속성 | 기본값 | 설명 |
|------|--------|------|
| stat_no_sky | 0 | 하늘 금지 (비행술 불가) |
| stat_no_under | 0 | 지하 금지 |
| stat_sea | 0 | 물속 (수중전) |
| stat_no_hourse | 0 | 말 탑승 금지 |
| stat_mp | 1 | MP 소비 (이동 비용) |
| stat_no_drop | 0 | 아이템 버림 금지 |
| long_type | 0 | getLong 타입 |
| fast_heal | 0 | 빠른 치유 |
| limitMob | 0 | 몬스터 상한선 |

### 9.3 문(Doors) 시스템

```c
mapping Doors       // 잠금/열기/닫기 매핑
cmdLOCK(str)        // 잠금
cmdUNLOCK(str)      // 풀기
cmdOPEN(str)        // 열기
cmdCLOSE(str)       // 닫기
```

---

## 10. 전투 시스템 상수 (전투.h)

### 10.1 무기 크기

| 상수 | 값 | 설명 |
|------|-----|------|
| TINY | 1 | 작은 |
| SMALL | 2 | 소형 |
| MEDIUM | 3 | 중형 |
| LARGE | 4 | 대형 |
| HUGE | 5 | 거대 |

### 10.2 공격 타입 (데미지 속성)

| 상수 | 값 | 설명 |
|------|-----|------|
| NONE | 0 | 마법/특수 |
| PIECING | 1 | 찌르기 (검, 창) |
| SLASH | 2 | 베기 (검, 도끼) |
| BLUDGE | 3 | 둔기 (망치, 봉) |
| SHOOT | 4 | 사격 (활, 석궁) |

### 10.3 방어구 슬롯 (22개)

| 상수 | 값 | 설명 |
|------|-----|------|
| HELMET | 1 | 투구 |
| EARRING | 2 | 귀고리 |
| PENDANT | 3 | 목걸이 |
| BODY_ARMOR | 4 | 가슴 |
| BELT | 5 | 띠/허리 |
| ARM_ARMOR | 6 | 팔 |
| GAUNTLET | 7 | 장갑 |
| ARMLET | 8 | 팔찌 |
| RING (1~10) | 9~21 | 반지 10개 |
| EARRING2 | 12 | 귀고리 2 |
| ARMLET2 | 22 | 팔찌 2 |

### 10.4 치명타 효과 (8종)

| 상수 | 값 | 설명 |
|------|-----|------|
| HIT_SELF | 1 | 자신에게 데미지 |
| HIT_GROUP | 2 | 그룹에 데미지 |
| DROP_WEAPON | 3 | 무기 떨어뜨림 |
| BREAK_WEAPON | 4 | 무기 파괴 |
| BREAK_ARMOR | 5 | 방어구 파괴 |
| STUN | 6 | 스턴 |
| DAMAGE_X | 7 | N배 데미지 |
| KILL | 8 | 즉사 |

### 10.5 불균형 유형 (3종)

| 상수 | 값 | 설명 |
|------|-----|------|
| SHIELD_UNBALANCED | 1 | 방패 불균형 |
| PARRY_UNBALANCED | 2 | 회피 불균형 |
| TWO_HAND_UNBALANCED | 3 | 양손 무기 불균형 |

---

## 11. 인게임 문서 (문서/)

| 파일 | 설명 | 마이그레이션 |
|------|------|-------------|
| 길잡이 | 초보자 가이드 | 도움말 변환 |
| 줄거리 | 게임 스토리 | 도움말 변환 |
| 무림첩 | 무림 백과사전 | 도움말 변환 |
| 메뉴얼 | 게임 매뉴얼 | 도움말 변환 |
| 업데이트이력 | 패치노트 | 도움말 변환 |
| 탄생기1~10 | 세계관 스토리 | 도움말 변환 |
| 기능설명 | 기능 설명서 | 도움말 변환 |
| 처벌에관한규정 | 규정 | 도움말 변환 |
| 무공제한 | 무공 제한 규칙 | 도움말 변환 |

---

## 12. 관리자 시스템

| 파일 | 의미 | 마이그레이션 대상 |
|------|------|-------------------|
| 로긴.c | 로그인 시스템 | 엔진에서 재구현 |
| 게시판.c | 게시판 시스템 | 선택적 |
| 편지.c | 우편 시스템 | 선택적 |
| 무리.c | 파티 시스템 | 선택적 |
| 날씨.c | 날씨 시스템 | 선택적 |
| 배율이벤트.c | 이벤트 배율 | 선택적 |
| 퀴즈.c | 퀴즈 이벤트 | 선택적 |
| 말.c | 기마 시스템 | 선택적 |
| 독문무기.c | 독문무기 제작 | 선택적 |
| 명예의전당.c | 명예의 전당 | 선택적 |

---

## 13. 커버리지 요약

### 현재 (재평가: ~55%)

| 카테고리 | 파싱 비율 | 비고 |
|----------|-----------|------|
| 방 속성 | **95%** | setNoSky/Under/Hourse 추가 완료, RandomMonster/Door 미지원 |
| 방 스폰 | **95%** | room_inventory → reset_commands 변환 완료 |
| 몬스터 기본 | **65%** | 이름/레벨/스탯 OK, 전투 관련 17개 누락 |
| 아이템 기본 | **50%** | 장비 핵심 OK, LIB_OBJECT 366개 누락, 속성 다수 누락 |
| 무기/방어구 | **60%** | RequireRace/Class, upgrade 계열 미지원 |
| 직업 | **90%** | 기술.h에서 추출, 구현체 미파싱 |
| 기술 | **15%** | 이름 51개만 추출, 367개 구현 파일 전무 |
| 도움말 | **70%** | .help OK, 문서/ 미포함 |
| 명령어 | **50%** | 플레이어 명령만, 제작자 명령 미포함 |
| 설정 | **85%** | 세팅/전투/드라이버/공식 파싱 완료 |
| NPC 특수유형 | **0%** | 상인/은행/힐러/임무 미파싱 |
| 문파 | **0%** | 완전 미파싱 |
| 기술 구현 | **0%** | 367개 기술 파일 미파싱 |
| 플레이어 구조 | **0%** | 참조용 (엔진에서 재구현) |

### 95% 달성 필요 작업

1. **기술 구현 파서** — 367개 기술 파일에서 상수/데미지/비용 추출 (최대 작업)
2. **몬스터 속성 확장** — 17개 중요 누락 set함수 추가
3. **아이템 속성 확장** — 17개 중요 누락 set함수 + LIB_OBJECT 지원
4. **NPC 특수유형 파서** — merchant/dealer/healer/banker 인식
5. **문파 데이터 파서** — 7개 문파 설정 추출
6. **문서 → 도움말 변환** — 29개 문서 파일을 help_entries에 추가
