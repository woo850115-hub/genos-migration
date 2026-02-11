# GenOS 범용 데이터 모델 비교 분석서

> 7개 게임(tbaMUD, Simoon, 3eyes, 10woongi, muhan13, murim, 99hunter) 데이터 구조 범용 분석
> 최종 업데이트: 2026-02-12 | 런타임 메커닉 비교 추가

---

## 1. 엔티티 비교표

### 1.1 Room (방)

| 필드 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter | 분류 |
|------|--------|--------|-------|----------|---------|-------|----------|------|
| vnum | int (파일 정의) | int | short (rom_num) | SHA-256 해시 | short (rom_num) | short (rom_num) | int (파일 정의) | 공통 |
| name | text (~) | text (~) | char[80] | setShort() | char[80] | char[~78] | text (~) | 공통 |
| description | text (~) | text (~) | length-prefixed | setLong() | length-prefixed | length-prefixed | text (~) | 공통 |
| zone_number | int | int | vnum/100 | 디렉토리 경로 | vnum/100 | vnum/100 | 에리어 파일 | 공통 |
| exits | 6방향 struct | 6방향 struct | exit_(44B) 연결리스트 | mapping Exits | exit_(44B) | exit_(~40B) | D0-D10 (11방향) | 공통 |
| flags | 128-bit bitvector | int/asciiflag | 8B F_ISSET | stat_* 변수들 | 8B F_ISSET | 65종 비트맵 | 128-bit (4×32) | extensions |
| sector_type | int (0-10) | int (0-10) | — | — | — | — | int (0-21) | extensions |
| extra_desc | keyword/text 쌍 | keyword/text 쌍 | obj_desc (length-prefixed) | — | obj_desc | obj_desc | E keyword/text | extensions |
| triggers | T lines (DG Script) | — | — | — | — | — | mprog | extensions |
| level_range | — | — | lolevel/hilevel | — | lolevel/hilevel | lolevel/hilevel | — | extensions |
| trap | — | — | trap/trapexit | — | trap/trapexit | trap/trapexit | — | extensions |
| random_spawn | reset_commands | reset_commands | random[10] | RandomMonster/Rate | random[10] | random[10] | #RESETS | extensions |
| door_locks | exit door_flags | exit door_flags | exit flags | mapping Doors | exit flags | exit flags | D lock_flags | extensions |
| terrain_flags | — | — | — | no_sky/sea/no_hourse | — | — | — | extensions |
| heal_rate | — | — | — | fast_heal | — | — | — | extensions |
| mob_limit | — | — | — | limitMob | — | — | — | extensions |
| direction_10 | — | — | — | — | — | — | somewhere (포탈) | extensions |
| climate | — | — | — | — | — | — | temp/precip/wind | extensions |
| economy | — | — | — | — | — | — | gold/total | extensions |

### 1.2 Item (아이템)

| 필드 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter | 분류 |
|------|--------|--------|-------|----------|---------|-------|----------|------|
| vnum | int | int | 파일 위치 기반 | SHA-256 해시 | 파일 위치 기반 | 파일 위치 기반 | int | 공통 |
| name/keywords | text (~) | text (~) | char[70]+key[3] | setName()/setID() | char[80] | char[~70] | text (~) | 공통 |
| short_desc | text (~) | text (~) | — | setShort() | — | — | text (~) | 공통 |
| long_desc | text (~) | text (~) | char[80] | setLong() | char[80] | char[80] | text (~) | 공통 |
| type | item_type (17종) | item_type | type (1B, 15종) | inherit 계열 (8종) | type (1B) | type (1B) | item_type | 공통 |
| weight | int | int | short | setMass() | short | short | int | 공통 |
| cost | int | int | long (value) | setValue() | long (value) | long (value) | int | 공통 |
| wear_location | 128-bit flags | int/asciiflag | wearflag (1B, 20슬롯) | setType() (22 슬롯) | wearflag (1B, 20슬롯) | wearflag (40슬롯) | wear_flags | 공통 |
| armor_class | values[0] | values[0] | armor (1B) | setArmor() | armor (1B) | armor (1B) | values[0] | 공통 |
| damage | values[1-2] | values[1-2] | ndice/sdice/pdice | MinDamage/DamageRange | ndice/sdice/pdice | ndice/sdice/pdice | values[1-2] | 공통 |
| extra_flags | 128-bit bitvector | int/asciiflag | 64-bit flags | setPrevent*/setInvis | 64-bit flags | 58종 비트맵 | 128-bit (4×32) | extensions |
| affects | affect_list | affect_list | adjustment (1B) | setStatUp (6종) | adjustment (1B) | adjustment (1B) | A apply_type/value | extensions |
| rent | int | int | — | — | — | — | cost_per_day | extensions |
| shots | — | — | shotsmax/shotscur | — | shotsmax/shotscur | shotsmax/shotscur | — | extensions |
| magic_power | — | — | magicpower (1B) | upgrade/sp_upgrade | magicpower (1B) | magicpower (1B) | — | extensions |
| magic_realm | — | — | magicrealm (1B) | — | magicrealm (1B) | magicrealm (1B) | — | extensions |
| durability | — | — | — | MaxLifeCircle | — | — | — | extensions |
| weapon_size | — | — | — | TINY~HUGE (1-5) | — | — | — | extensions |
| weapon_type | — | — | — | PIECING/SLASH/BLUDGE/SHOOT | — | — | — | extensions |
| speed | — | — | — | SpeedFactor | — | — | — | extensions |
| two_handed | — | — | — | TwoHanded flag | — | — | — | extensions |
| requirements | — | — | min_strength | RequireLevel/Race/Class | — | — | — | extensions |
| messages | — | — | use_output | HitMessage/EquipMessage | use_output | use_output | — | extensions |
| owner_info | — | — | — | — | — | owner+race+class+kill (50B) | — | extensions |
| enchant_slots | — | — | — | — | — | obj01-20 (20슬롯) | — | extensions |
| layers | — | — | — | — | — | — | MAX_LAYERS=8 | extensions |
| action_desc | — | — | — | — | — | — | text (~) | extensions |

### 1.3 Monster (몬스터)

| 필드 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter | 분류 |
|------|--------|--------|-------|----------|---------|-------|----------|------|
| vnum | int | int | 파일 위치 기반 | SHA-256 해시 | 파일 위치 기반 | 파일 위치 기반 | int | 공통 |
| name/keywords | text (~) | text (~) | char[80]+key[3] | setName()/setID() | char[80]+key[3] | char[72]+key[3] | text (~) | 공통 |
| short_desc | text (~) | text (~) | — | setShort() | — | — | text (~) | 공통 |
| long_desc | text (~) | text (~) | char[80] | setLong() | char[80] | char[78] | text (~) | 공통 |
| level | int | int | char (1B) | randomStat(level) | char (1B) | long | int | 공통 |
| hp | XdY+Z 주사위 | XdY+Z 주사위 | hpmax/hpcur (short) | setupBody() 공식 | hpmax/hpcur (short) | hpmax/hpcur (long) | hitdice | 공통 |
| gold | int | int | long | setGold() | long | long | int | 공통 |
| experience | int | int | long | setExp()/setAdjExp() | long | long | int | 공통 |
| sex | int (0-2) | int (0-2) | — | setGender() | — | — | int (0-2) | 공통 |
| armor_class | int | int | char (1B) | setArmorClass() | char (1B) | long | int | 공통 |
| alignment | int | int | short | — | short | long | int | 공통 |
| action_flags | 128-bit bitvector | int/asciiflag | 64-bit flags | setAggresive 등 | 64-bit flags | 640-bit (80B) | 128-bit (4×32) | extensions |
| affect_flags | 128-bit bitvector | int/asciiflag | — | — | — | — | 128-bit (4×32) | extensions |
| class | — | — | char (1B, 1-8) | — | char (1B, 1-8) | char (1B, 1-21) | int (0-29) | extensions |
| race | — | — | char (1B, 1-8) | setRace() | char (1B, 1-8) | char (1B, 1-4) | int (0-98) | extensions |
| stats_standard | — | — | str/dex/con/int/pie (5종) | — | str/dex/con/int/pie (5종) | str/dex/con/int/pie (5종) | str/int/wis/dex/con/cha/lck (7종) | extensions |
| stats_custom | — | — | — | 힘/내공/지혜/기골/민첩/투지 (6종) | — | 13종 무술 스탯 | — | extensions |
| mp | — | — | mpmax/mpcur | setupBody() | mpmax/mpcur | mpmax/mpcur (long) | mana | extensions |
| thaco | — | — | char (1B) | — | char (1B) | long | hitroll | extensions |
| attack_dice | XdY+Z | XdY+Z | ndice/sdice/pdice | — (기술 기반) | ndice/sdice/pdice | ndice/sdice/pdice (long) | damdice | extensions |
| spells | — | — | spells[16] 비트필드 | setSkillData() | spells[16] | spells[16] | — | extensions |
| proficiency | — | — | proficiency[5] | — | proficiency[5] | proficiency[50] | — | extensions |
| magic_realm | — | — | realm[4] | — | realm[4] | realm[40] | — | extensions |
| martial_arts | — | — | — | — | — | art[256] (1024B) | — | extensions |
| talk/chat | — | — | talk 파일 | setChat()/setChatChance() | talk/rndtalk | talk | — | extensions |
| wander | — | — | numwander | setWander() | numwander | numwander | — | extensions |
| special | — | custom_attrs | special (2B) | setAttackFunc() 등 | special (2B) | special (2B) | — | extensions |
| fame | — | — | — | setFame() | — | long | — | extensions |
| munpa | — | — | — | setMunpa() | — | — | — | extensions |
| saving_throws | — | — | — | — | — | — | 5종 (sav1-5) | extensions |
| move | — | — | — | — | — | movemax/movecur (long) | move | extensions |
| damroll | — | — | — | — | — | — | int | extensions |
| numattacks | — | — | — | — | — | — | int | extensions |
| back_desc | — | — | — | — | — | char[78] | — | extensions |
| war_stats | — | — | — | — | — | war_win/lose/gold | — | extensions |
| hwansaeng | — | — | — | — | — | int (환생 횟수) | — | extensions |

### 1.4 Skill (스킬/기술)

| 필드 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter | 분류 |
|------|--------|--------|-------|----------|---------|-------|----------|------|
| id | spello index | spello index | splno | #define 또는 파일명 | splno | splno | 순서 번호 | 공통 |
| name | string | string | char* (한글) | SKILL_NAME (한글) | char* (한글) | char* (한글) | Name (한글) | 공통 |
| type | — | — | — | — | — | — | Spell/Skill/Weapon/Tongue/Herb | extensions |
| level_req | — | — | spllv | — | — | — | Skill (클래스별) | extensions |
| mana_cost | max/min/change | max/min/change | ospell.mp | startSkill() 내부 | 불명 | 불명 | Mana | extensions |
| target | TAR_* flags (11종) | TAR_* flags (11종) | — | 기술별 고유 | — | — | Target | extensions |
| violence | violent flag | violent flag | — | — | — | — | — | extensions |
| routines | MAG_* flags (12종) | MAG_* flags (12종) | 함수 포인터 | skillMain()/endSkill() | 함수 포인터 | 함수 포인터 | Code (C함수명) | extensions |
| wearoff | string | — | — | — | — | — | Wearoff | extensions |
| damage_formula | spell별 고유 | spell별 고유 | ndice*D(sdice)+pdice | (스탯*계수+skill*N)/분모 | dice 기반 | dice+스탯보정 | Dammsg | extensions |
| magic_realm | — | — | ospell.realm (1-4) | ATTR (#define) | realm (1-4) | 8계파 | — | extensions |
| turn_count | — | — | — | TURN/ATTACK_TURN | — | — | — | extensions |
| mastery | — | — | — | SKILL_MASTER (100) | — | — | — | extensions |
| critical | — | — | — | 민첩>=random(200)→14x | — | — | — | extensions |
| proficiency_exp | — | — | — | getSkillUpExp() | — | — | — | extensions |
| affect | — | — | — | — | — | — | Affect 데이터 | extensions |

---

## 2. 시스템 비교표

### 2.1 전투 메시지

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 저장 | lib/misc/messages | lib/misc/messages | 소스 하드코딩 | 기술별 messageRoutine() | 소스 하드코딩 | 소스+무공 | skills.dat Dammsg |
| 포맷 | M블록×12줄 | M블록×12줄 (EUC-KR) | printf 직접 | 3단계 (source/target/room) | printf 직접 | printf+dice보정 | text (~) |
| 블록 수 | 55개 | 유사 | — | 367개 기술 각각 | — | — | 54 스킬 |
| 변수 | $n/$N/$s/$S/$m/$M/$e/$E | + $j/$g/$d/$C/$v/$D | — | HanAttack()/HanDesc() | — | — | — |
| 조사 처리 | 없음 (영어) | 받침 기반 자동 | 없음 (한글 직접) | 한글 조사 자동 | 한글 직접 | 한글 직접 | 한글 직접 |

### 2.2 상점(Shop)

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 수량 | 334개 | 103개 | 없음 | merchant/dealer | 없음 | 없음 | #SHOPS 섹션 |
| 정의 방식 | .shp 파일 | .shp 파일 | — | LPC inherit | — | — | 에리어 내장 |
| 구매 배율 | profit_buy | profit_buy | — | cost% 파라미터 | — | — | profit_buy |
| 판매 배율 | profit_sell | profit_sell | — | 75% 고정 | — | — | profit_sell |
| 타입 제한 | buy_types | buy_types | — | 타입 분류 | — | — | buy_types |
| 위탁 판매 | — | — | — | dealer (100개) | — | — | — |
| 은행 | — | — | — | banker (1억) | bank.c | bank.c | — |
| 치료 | — | — | — | healer (HP/SP) | — | — | #REPAIRS |
| 수리 | — | — | — | — | 제련 (forge) | — | #REPAIRS |

### 2.3 직업/종족(Class/Race)

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 직업 수 | 4 (기본) | 7 | 8 (+4 관리자) | 14 | 8 (+5 관리자) | **21** (진급제) | **30** (6기본+24고급) |
| 종족 수 | — | 5 | 8 | — (종족=문파) | 8 | 4 | 8 (+91 NPC) |
| 스탯 영향 | — | — | class_stats[13] | 6종 스탯 시스템 | class_stats | class_stats[21] | 종족별 스탯보정 |
| 레벨업 | exp 테이블 | exp 테이블 | level_cycle[14][10] | 경험치 테이블 | exp 테이블 | exp 테이블 | Expbase (클래스별) |
| THAC0 | class별 | class별 | thaco_list[18][20] | — (기술 기반) | thaco_list | thaco_list | Thac0/Thac32 |
| Saving Throw | 5종 | 5종 | — | — | — | — | 5종 |
| 최대 레벨 | 34 (구현) | 유사 | 200 | 불명 | 128 | 불명 | **777** |
| 전직 | — | — | 환생 (INVINCIBLE~) | — | 전직 (change_class) | 진급 (21단계) | 전직 (기본→고급) |
| 정의 파일 | C 소스 | C 소스 | C 소스 | LPC 헤더 | C 소스 | C 소스 | **외부 .class 파일** |

### 2.4 클랜/문파

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 존재 | 없음 | clan 파일 | family[16] | 문파 7개 | family[16] | 문중 16개 | clan 1개 |
| 구조 | — | 불명 | name/boss/gold | leader/sub(4)/jeja | name/boss/gold | name/boss/gold | #CLAN 파일 |
| 경제 | — | — | family_gold | 문파경제.c | family_gold | family_gold | — |
| 전쟁 | — | — | fam_win/fam_lost | 소공략/대공략 | call_war() | call_war() | — |
| 게시판 | — | — | family1~15/ | 문파 전용 | family1~15/ | family1~15/ | Board vnum |
| 상점 | — | — | — | 문파 상점 | — | — | — |
| 신/의회 | — | — | — | — | — | — | deity 2 + council 2 |

### 2.5 고유 시스템 비교

| 시스템 | 게임 | 설명 |
|--------|------|------|
| DG Script | tbaMUD | 1,461개 트리거 스크립트, 변수 시스템 |
| 한국어 조사 | Simoon | $j/$g/$d/$C/$v/$D 변수로 받침 기반 자동 조사 |
| 환생 | 3eyes, murim | 레벨 캡 후 클래스/능력 초기화 재성장 |
| 문파 경제 | 10woongi | 문파별 상점/게시판/소공략/대공략 |
| 은행 | muhan13, murim, 10woongi | 골드 입금/인출/아이템 보관 |
| 결혼 | muhan13, murim | 결혼식/이혼/배우자 메시지 |
| 제련 | muhan13 | forge()/newforge() 무기 제작 |
| 전쟁 | muhan13, murim | 왕국/문중 간 전쟁 선포 |
| 달돌(Moonstone) | muhan13 | 특수 이벤트 아이템 |
| 무공(Martial Arts) | murim | art[256], 8계파, 종족별 커리큘럼 |
| 내공심법 | murim | 내공 수련 레벨 시스템 |
| 분신법술 | murim | 동영인 전용, 환생 필수, 분신 몹 생성 |
| 무술 훈련 | murim | killmark+골드 기반 스킬 구매 |
| 신(Deity) | 99hunter | 신앙/은총 시스템, 2개 신 |
| 의회(Council) | 99hunter | 정치/조직 시스템 |
| OLC 빌더 | 99hunter | 인게임 에리어 편집 (build.c 220KB) |
| 의복 레이어 | 99hunter | MAX_LAYERS=8, 중첩 착용 |
| 약초(Herb) | 99hunter | herbs.dat 약초 시스템 |
| 언어(Tongue) | 99hunter | tongues.dat 언어 시스템 |

---

## 3. 인코딩/포맷 비교

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 인코딩 | ASCII (UTF-8) | EUC-KR | EUC-KR | EUC-KR | EUC-KR | EUC-KR | EUC-KR |
| 파일 포맷 | 텍스트 (CircleMUD) | 텍스트 (CircleMUD) | 바이너리 C struct | LPC 소스 코드 | 바이너리 C struct | 바이너리 C struct | 텍스트 (SMAUG) |
| 엔티티 정의 | ~ 구분 텍스트 블록 | ~ 구분 텍스트 블록 | 고정 크기 struct | 개별 .c 파일 setXxx() | 고정 크기 struct | 고정 크기 struct | ~ 구분 에리어 파일 |
| 파일 분리 | 타입별 (WLD/MOB/OBJ) | 타입별 | 타입별 (objmon/rooms) | 개별 .c | 타입별 | 타입별 | **단일 에리어 파일** |
| VNUM 체계 | 파일 내 #vnum | 파일 내 #vnum | 파일 경로 기반 | SHA-256 해시 | 파일 경로 기반 | 파일 경로 기반 | 파일 내 #vnum |
| 플래그 표현 | 128-bit bitvector | int/asciiflag | F_ISSET 비트맵 | 개별 set* 함수 | F_ISSET 비트맵 | F_ISSET (640-bit!) | 128-bit (4×32) |
| 색상 코드 | @색코드 | EUC-KR @색코드 | ANSI ESC 직접 | %^COLOR%^ | ANSI ESC 직접 | ANSI ESC 직접 | **&W &g 등** |
| 문자열 종료 | ~ (틸드) | ~ (틸드) | NULL (\0, 고정길이) | LPC string | NULL (\0, 고정길이) | NULL (\0, 고정길이) | ~ (틸드) |
| 스킬 정의 | C spello() | C spello() | C spllist[] | LPC #define | C 소스 | C 소스 | **외부 skills.dat** |
| 클래스 정의 | C class.c | C class.c | C global.c | LPC 직업.h | C global.c | C global.c | **외부 .class 파일** |

### 3.1 엔진 계보별 색상 코드 매핑

| 엔진 | 입력 코드 | 예시 (빨강) | GenOS 변환 |
|------|----------|------------|-----------|
| CircleMUD (tbaMUD) | @코드 | @r | {red} |
| Simoon | @코드 (EUC-KR) | @r | {red} |
| Mordor (3eyes/muhan13/murim) | \033[Nm | \033[31m | {red} |
| LP-MUD (10woongi) | %^COLOR%^ | %^RED%^ | {red} |
| SMAUG (99hunter) | &코드 | &R | {red} |

---

## 4. 파일 규모 비교표

| 카테고리 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter | 합계 |
|----------|--------|--------|-------|----------|---------|-------|----------|------|
| 방 (Room) | 12,700 | 6,508 | 7,439 | 17,590 | 3,218 | 미포함* | ~2,500-3,000 | **~50,000+** |
| 아이템 (Item) | 4,765 | 1,753 | 1,362 | 969 | 907 | ~1,077 | ~1,500-2,000 | **~12,300+** |
| 몬스터 (Mob) | 3,705 | 1,374 | 1,394 | 947 | 1,049 | ~683 | ~1,500-2,000 | **~10,650+** |
| 존 (Zone) | 189 | 128 | 103 | 122 | 10 | 11(맵) | 53 | **~616** |
| 상점 (Shop) | 334 | 103 | — | merchant | — | — | #SHOPS | **~437+** |
| 도움말 (Help) | 721 | 2,220 | 116 | 72 | ~228 | 30 | ~326 | **~3,713** |
| 스킬 (Skill) | 54 | 79 | 63 | 367 | 56 | 126+ | 54 | **~799+** |
| 명령어 (Cmd) | 275 | 546 | 405 | 51 | 350 | ~300 | 488 | **~2,415** |
| 트리거 | 1,461 | — | — | — | — | — | mprog | **~1,461+** |
| 퀘스트 | 8 | 16 | 128-bit | — | 128-bit | 128-bit | — | **~24+** |
| 소셜 | 104 | 104 | — | — | 40 | 100+ | 7 | **~355+** |
| 직업 | 4 | 7 | 8 | 14 | 8 | 21 | 30 | **92** |
| 종족 | — | 5 | 8 | — | 8 | 4 | 8(+91 NPC) | **33(+91)** |
| 클랜/문파 | — | 1+ | 16 | 7 | 16 | 16 | 1 | **~57+** |
| 게임 설정 | 다수 | 다수 | 다수 | 98 | 다수 | 다수 | sysdata.dat | — |
| 전투 메시지 | 55 블록 | 유사 | — | 367 기술별 | — | — | 54 스킬별 | — |
| 신/의회 | — | — | — | — | — | — | 2+2 | **4** |

\* murim rooms/ 디렉토리가 현재 스냅샷에 포함되지 않음 (맵 파일 분석으로 수천 개 방 존재 추정)

---

## 5. extensions 패턴 분석

### 5.1 공통 필드 (7게임 → DB 정규 컬럼)

모든 게임에서 공유되어 정규 DB 컬럼으로 처리해야 할 필드:

```
Room: vnum, name, description, zone_id
Item: vnum, name, description, type, weight, cost, wear_location, armor, damage
Monster: vnum, name, description, level, hp, gold, experience, sex, armor_class, alignment
Zone: number, name
Skill: id, name
```

### 5.2 준공통 필드 (3개+ 게임 → 정규 컬럼 권장)

```
Room: exits (7게임), flags (7게임 형태 다름), extra_desc (5게임)
Item: flags (7게임), affects (6게임), rent (3게임)
Monster: action_flags (7게임 형태 다름), damage (6게임), class (5게임), race (5게임)
Monster: mp (5게임), thaco (5게임), stats (5게임, 종류 다름)
Skill: mana_cost (5게임), routines (7게임), damage_formula (6게임)
```

### 5.3 게임 고유 필드 (→ extensions JSONB)

```
tbaMUD: trigger_vnums, enhanced_mob, 128-bit bitvectors
Simoon: custom_mob_attrs, korean_particles
3eyes: proficiency[5], realm[4], spells[16], magicpower/magicrealm, quests[16]
10woongi: stats(6종), skill_data, chat/chatChance, munpa, weapon_size/type,
          durability, upgrade, speed_factor, save_data, NPC_type
muhan13: creature2(title/bank/extended_flags), rndtalk, bank_data, marriage_data
murim: stats(18종), proficiency[50], realm[40], art[256], martial_skills(24종),
       owner_info, enchant_slots(20), hwansaeng, naekongsimbub, war_stats,
       640-bit flags
99hunter: saving_throws(5), layers, numattacks, speaks/speaking, resist/immune/suscept,
         attacks/defenses, deity_data, council_data, direction_10
```

### 5.4 권장 DB 스키마 원칙

1. **7게임 공통 → 정규 컬럼**: vnum, name, description, level 등
2. **형태만 다른 공통 → 통합 정규 컬럼**: flags는 JSONB array로 통합
3. **3-6게임 공유 → 정규 nullable 컬럼**: alignment, class, race, mp, damage_dice 등
4. **게임 고유 → extensions JSONB**: 위 5.3 항목들
5. **시스템 테이블 (game_configs)**: 게임별 상수/공식/테이블
6. **대규모 배열 → 별도 테이블**: murim art[256], proficiency[50] 등

### 5.5 extensions 규모 예측

| 게임 | extensions 필드 수 (추정) | 최대 단일 레코드 크기 |
|------|--------------------------|---------------------|
| tbaMUD | ~5 | ~1KB |
| Simoon | ~5 | ~1KB |
| 3eyes | ~15 | ~2KB |
| 10woongi | ~25 | ~5KB |
| muhan13 | ~20 | ~3KB |
| murim | **~40** | **~10KB** (art[256] 포함) |
| 99hunter | ~15 | ~2KB |

---

## 6. 범용 스키마 설계 시사점

### 6.1 핵심 인사이트

1. **CircleMUD 계열(tbaMUD/Simoon)은 데이터 완전성 높음** — 텍스트 기반 정형 포맷, 100% 파싱 달성
2. **바이너리(3eyes/muhan13)는 struct 매핑이 핵심** — 동일 크기도 필드 순서 다를 수 있음
3. **murim은 극단적 확장 사례** — creature 3,380B, 18종 스탯, art[256] → extensions JSONB 설계의 시금석
4. **SMAUG(99hunter)는 새 포맷 패러다임** — 단일 파일 전체 에리어, 외부 데이터 파일
5. **LPC(10woongi)는 가장 비정형** — 개별 파일 함수 호출 기반, 367개 기술 파일이 최대 도전
6. **extensions JSONB가 범용성의 핵심** — murim의 40+ 필드도 수용 가능해야 함

### 6.2 Mordor 계열 3종 비교 (struct 호환성)

```
3eyes    : creature(1184B, fd-first)   / object(352B, name[70]+etc[10]) / room(480B, name-first)
muhan13  : creature(1184B, name-first) / object(352B, name[80])        / room(480B, rom_num-first)
murim    : creature(3380B, name-first) / object(492B, +owner/enchant)  / room(~444B)
```

**결론**: struct 크기가 같아도 필드 순서 다름 → 각각 별도 파서 필수. 공통 로직은 파일 탐색/존 분류만.

### 6.3 스키마 확장 시 고려사항

- **전투 메시지 테이블** 필요: 7게임 모두 다른 방식이지만 "스킬→메시지" 매핑은 공통
- **NPC 유형 테이블** 필요: 10woongi merchant/dealer/banker/healer, 99hunter #SHOPS/#REPAIRS
- **클랜/문파 테이블** 필요: 3eyes/muhan13/murim family + 10woongi 문파 + Simoon clan + 99hunter clan
- **숙련도 시스템**: 3eyes proficiency[5] + murim proficiency[50] + 10woongi skill_data → 통합 가능
- **마법 영역**: 3eyes realm[4] + murim realm[40] → JSONB array
- **무공 배열**: murim art[256] → 별도 martial_arts 테이블 (monster_vnum, art_index, value)
- **인챈트**: murim obj01-20 → 별도 enchantments 테이블 또는 extensions
- **saving_throws**: 99hunter 5종 + tbaMUD/Simoon 5종 → 공통 테이블 가능

### 6.4 새 게임 추가 시 체크리스트

새 게임을 분석할 때 확인해야 할 항목:

1. 파일 포맷 (텍스트/바이너리/소스코드/에리어)
2. 인코딩 (ASCII/EUC-KR/UTF-8)
3. VNUM 체계 (정수/파일경로/해시)
4. 플래그 표현 (bitvector/int/함수호출) 및 비트 수
5. 스킬 정의 방식 (C함수/C배열/파일/LPC)
6. 전투 메시지 위치 (파일/소스/함수/외부)
7. NPC 특수유형 존재 여부 (상인/은행/치료/수리)
8. 클랜/길드 시스템 존재 여부
9. 고유 시스템 (트리거/환생/문파/무공/신/의회 등)
10. struct 크기 및 필드 순서 (바이너리 게임)
11. 색상 코드 체계
12. 플레이어 파일 포맷 (비밀번호 저장 방식 포함)

---

## 7. 런타임 메커닉 비교

### 7.1 전투 타이밍/루프

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 전투 루프 | violence_update (2초) | violence_update (2초) | combat_round (1초) | heart_beat (1초) | combat_round (1초) | combat_round (1초) | violence_update (~2초) |
| 비전투 tick | 75초 point_update | 75초 point_update | 1초 heart_beat | 1초 heart_beat | 1초 heart_beat | 1초 heart_beat | pulse_* 다단계 |
| 루프 방식 | 글로벌 character_list | 글로벌 character_list | 방 단위 active_fighters | 방 단위 turn/back_turn | 방 단위 active_fighters | 방 단위 active_fighters | 글로벌 char_list |
| 턴 개념 | 없음 (실시간) | 없음 (실시간) | 없음 (실시간) | **턴제** (others_turn/back_turn) | 없음 (실시간) | 없음 (실시간) | 없음 (실시간) |

### 7.2 명중 판정 (THAC0)

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 주사위 | d20 | d20 | **d30** | 없음 (기술 기반) | **d30** | **d20** | d20 |
| PC THAC0 | class_table[class][level] | **1 (고정!)** | thaco_list[class][level/10] | — | thaco_list[class][level/10] | thaco_list[class][level/10] | Thac0→Thac32 보간 |
| NPC THAC0 | level 기반 | 20 (기본) | mob.thaco | — | mob.thaco | mob.thaco | mob 데이터 |
| 보정치 | hitroll + STR | hitroll + **INT/WIS** | hitroll + STR | — | hitroll + STR | hitroll + STR | hitroll + STR |
| 특이사항 | 표준 | PC 30레벨+ 거의 100% 명중 | 30면체 (명중률 낮음) | 명중 판정 없음 (턴제) | 30면체 | 20면체 (3eyes와 다름!) | 보간 공식 |

### 7.3 데미지 계산

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 무기 데미지 | XdY | XdY | ndice×D(sdice)+pdice | MinDamage+rand(Range) | ndice×D(sdice)+pdice | ndice×D(sdice)+pdice | XdY |
| 스킬 데미지 | spell별 고유 | spell별 고유 | ospell dice | (스탯×계수+skill×N)/분모 | 소스 내 dice | dice+스탯보정 | Dammsg |
| damroll 보정 | + damroll | + damroll | + pdice (bonus) | + STR bonus | + pdice | + pdice | + damroll |
| 크리티컬 | 없음 | 없음 | 없음 | 민첩≥random(200)→**14배** | 없음 | **일격필살 (100배)** | 없음 |
| 상한 | 없음 | 없음 | 없음 | 없음 | 없음 | 없음 | level×1000 |
| 특수 데미지 | — | — | — | 내공×8~10 가산 | — | **내공/외공** 분리 | fighting_style ±20% |

### 7.4 다중 공격 (Multi-Hit)

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 최대 횟수 | 3 | 5 | 1 | 1 (기술 ATTACK_TURN) | 1 | 1 | 5 |
| 결정 기준 | 2nd/3rd attack 스킬% | **레벨 기반** (150+→5) | — | — | — | — | **스킬%** (5단계) |
| NPC | mob_specials | attack1/2/3 확률 | — | — | — | — | numattacks |
| 랜덤 추가 | 없음 | 10% +1, 희귀 +2 | — | — | — | 분신법술 (2체 분신) | — |

### 7.5 방어/감소 계산

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| AC 역할 | 명중 판정 보정 | 명중 판정 보정 | 명중 판정 보정 | **데미지 감소** | 명중 판정 보정 | 명중 판정 보정 | 명중 판정 보정 |
| Sanctuary | 데미지 ½ | 데미지 ½ | 데미지 ½ | — | 데미지 ½ | 데미지 ½ | 데미지 ½ |
| 추가 방어 | — | — | — | autoDefence (민첩×8/100+AC/4+투지/20) | — | — | — |
| SP 방어 | — | — | — | autoSpDefence (지혜×5/100+?) | — | — | — |
| 스킬 방어 | — | — | — | skillDefence (상태이상 저항) | — | — | — |
| RIS | — | — | — | — | — | — | **fire/cold/acid/elec/energy/drain/poison + blunt/pierce/slash** |
| 반격 | — | **SKILL_REATT** (10%) | — | — | — | — | — |
| Fighting Style | — | — | — | — | — | — | evasive/defensive/standard/aggressive/berserk |

### 7.6 사망 처리

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 사망 조건 | HP ≤ -11 | HP ≤ -11 | HP ≤ 0 | 몹종류0: HP≤0, 몹종류1: HP≤0 **AND** SP≤0 | HP ≤ 0 | HP ≤ 0 | HP ≤ -11 |
| PvM 패널티 | 경험치 손실 | **능력치 감소** (50+) | 경험치 손실 | 없음 (죽는 쪽이 몹) | 경험치 손실 | 경험치 4종 중 택 | **주석 처리** (실질 없음) |
| PvP 패널티 | 없음 | **없음** (킬마크 지급) | — | 없음 | — | — | — |
| 시체 생성 | make_corpse() | make_corpse() | — | 없음 (즉시 소멸) | — | — | make_corpse() |
| 부활 장소 | start_room | start_room | recall | 부활좌표 | recall | recall | temple |
| 특수 | — | maxHP/MANA/MOVE 영구감소 | — | eventDie()→ExpType별 분배 | — | — | — |

### 7.7 경험치 분배

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 분배 방식 | 킬러 단독 | 킬러 단독 | 킬러 단독 | **파티 분배** (같은 방) | 킬러 단독 | **4종 분리** | 킬러 단독 |
| 10w 분배율 | — | — | — | 킬러60%/그룹10-15%/최고피해10-25% | — | — | — |
| murim 4종 | — | — | — | — | — | 일반/실전/문파/무공 각각 분리 | — |
| 패널티 | 레벨 차 미적용 | 레벨 차 미적용 | 레벨 차 미적용 | 없음 | 레벨 차 미적용 | 레벨 차 미적용 | 레벨 차 미적용 |

### 7.8 HP/MP 회복

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 기본 | graf() 연령 기반 | graf() 연령 기반 | 1초 heart_beat | 10초 healBody | 1초 heart_beat | 1초 heart_beat | pulse_* |
| 위치 배수 | sleeping/resting/sitting | sleeping/resting/sitting | 없음 | 없음 | 없음 | 없음 | 있음 |
| 10w 몹 | — | — | — | **8% HP / 9% SP / 13% MP** (10초) | — | — | — |
| 장비 보정 | — | ITEM_MANA_REGEN +10 | — | — | — | — | — |
| 방 보정 | — | ROOM_GOOD_REGEN (HP×4) | — | fast_heal | — | — | — |

### 7.9 화폐/경제 시스템

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 기본 화폐 | gold | gold | gold | gold | gold | gold | gold |
| 추가 화폐 | — | **crystal + killmark** | — | — | — | **killmark** | — |
| 은행 | — | — | — | banker (1억 한도) | **bank.c** | **bank.c** | — |
| 특수 | — | crystal 레벨업 지급 | — | 위탁판매 dealer | 달돌(moonstone) | 무술 구매용 killmark | — |

### 7.10 환생/전직 시스템

| 항목 | tbaMUD | Simoon | 3eyes | 10woongi | muhan13 | murim | 99hunter |
|------|--------|--------|-------|----------|---------|-------|----------|
| 존재 | 없음 | **remort (303레벨)** | **환생 (200레벨)** | 없음 | **전직 (change_class)** | **환생 (hwansaeng)** | **전직 (6기본→24고급)** |
| 메커닉 | — | 7클래스 완료→HP/MP 100k | INVINCIBLE→CARETAKER→... | — | 같은 레벨 다른 직업 | 능력초기화+art 유지 | 기본→고급 직업 |
| 횟수 | — | 7회 (클래스 수) | 5단계 (선택4/비활성4) | — | 8회 (직업 수) | 무한 | 1회 |

### 7.11 특수 전투 메커닉

| 시스템 | 게임 | 설명 |
|--------|------|------|
| 턴제 전투 | 10woongi | others_turn → 상대 기술 → back_turn → 내 기술, continueCombat() 루프 |
| RIS (내성) | 99hunter | Resist/Immune/Susceptible: 화/냉/산/전기/에너지/흡수/독 + 타격/관통/참격 |
| Fighting Style | 99hunter | 5단계: evasive(-20% dam)/defensive(-10%)/standard/aggressive(+10%)/berserk(+20%) |
| 내공/외공 | murim | 내공 = MP 기반 추가 데미지, 외공 = STR 기반 물리 데미지, 별도 계산 |
| 분신법술 | murim | 동영인 전용, 환생 필수, 2체 분신 몹 생성 → 동시 공격 |
| 독 시스템 | 10woongi | poisoned → heart_beat마다 HP 감소, curePoison() 해독 |
| 무기 레벨 | 10woongi | WeaponSize(1-5) vs 몹 크기 비교 → 소형 무기로 대형 몹 공격 불가 |
| 활/화살 | Simoon | ITEM_BOW + ITEM_ARROW 조합, 화살 소모 (무게 -1), 데미지 ×2 |
| 뱀파이어 | 99hunter | IS_VAMPIRE → 낮 HP 손실, 밤 HP 회복, bloodlet 스킬 |
| 반격 | Simoon | SKILL_REATT 10% 확률, 피해자 레벨 ≥ 공격자 → 공격자 반사 피해 |

### 7.12 통합 설계 시사점 — 런타임

1. **전투 루프 추상화**: 2종 (글로벌 리스트 순회 vs 방 단위 턴제) → CombatSystem Protocol로 통합
2. **THAC0/명중 판정**: 4종 (d20/d30/고정/없음) → `calc_to_hit(attacker, victim)` 추상 메서드
3. **데미지 공식**: 게임마다 완전 다름 → `calc_damage(attacker, victim, skill)` 추상 메서드
4. **사망 조건**: HP≤0 단일 vs HP+SP 동시 vs 단계적 → `check_death(victim)` 추상 메서드
5. **다중 공격**: 스킬%/레벨/없음 → `calc_num_attacks(attacker)` 추상 메서드
6. **회복**: 연령 기반/시간 기반/장비 기반 → `calc_regen(character)` 추상 메서드
7. **경험치 분배**: 단독/파티/4종 분리 → `distribute_exp(killer, victim, room)` 추상 메서드
8. **특수 시스템은 플러그인**: RIS, 턴제, 문파, 무공 → 게임별 플러그인에서 처리
9. **화폐**: gold 공통 + extensions JSONB (crystal, killmark 등)
10. **환생/전직**: 게임별 완전 고유 → 플러그인 이벤트 훅 (on_level_max, on_remort)
