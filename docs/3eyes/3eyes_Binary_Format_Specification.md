# 3eyes 바이너리 파일 포맷 스펙

> **Version**: 1.0
> **대상**: 3eyes MUD (Mordor/CircleMUD variant, 32-bit Linux)
> **바이트 오더**: Little-endian (x86)
> **정렬**: Natural alignment (char=1, short=2, int/long/ptr=4)

---

## 목차

1. [개요](#1-개요)
2. [기본 규칙](#2-기본-규칙)
3. [Object 구조체 (352 bytes)](#3-object-구조체-352-bytes)
4. [Creature 구조체 (1184 bytes)](#4-creature-구조체-1184-bytes)
5. [Room 구조체 (480 bytes)](#5-room-구조체-480-bytes)
6. [Exit 구조체 (44 bytes)](#6-exit-구조체-44-bytes)
7. [Room 파일 형식 (가변 길이)](#7-room-파일-형식-가변-길이)
8. [Object/Monster 파일 형식](#8-objectmonster-파일-형식)
9. [Talk 파일 형식](#9-talk-파일-형식)
10. [Ddesc 파일 형식](#10-ddesc-파일-형식)
11. [Help 파일 형식](#11-help-파일-형식)
12. [플래그 비트 매크로](#12-플래그-비트-매크로)

---

## 1. 개요

3eyes는 C의 `write(fd, &struct, sizeof(struct))`로 데이터를 직접 디스크에 기록한다. 텍스트 파싱 없이 `read(fd, &struct, sizeof(struct))`로 그대로 메모리에 로드하는 방식이다.

이 때문에:
- 구조체의 **패딩(padding)** 바이트가 파일에 그대로 포함됨
- **포인터 필드**가 파일에 기록되지만 디스크에서는 무의미한 값
- 플랫폼(32-bit vs 64-bit, endianness)이 다르면 파싱 불가

### 보조 구조체

```c
typedef struct daily {     // 8 bytes
    char max;              // +0
    char cur;              // +1
    // 2 pad
    long ltime;            // +4
} daily;

typedef struct lasttime {  // 12 bytes
    long interval;         // +0
    long ltime;            // +4
    short misc;            // +8
    // 2 pad
} lasttime;
```

---

## 2. 기본 규칙

### 타입 크기 (32-bit Linux)

| C 타입 | 크기 | 정렬 |
|--------|------|------|
| char | 1 | 1 |
| unsigned char | 1 | 1 |
| short | 2 | 2 |
| int | 4 | 4 |
| long | 4 | 4 |
| pointer (*) | 4 | 4 |

### 문자열 인코딩
- 모든 `char[]` 필드는 **null-terminated EUC-KR** 문자열
- 남는 공간은 null(\x00)로 채워짐
- EUC-KR: 한글 1자 = 2바이트

### 플래그 비트 연산
```c
#define F_ISSET(p,f)  ((p)->flags[(f)/8] & (1<<((f)%8)))
#define F_SET(p,f)    ((p)->flags[(f)/8] |= 1<<((f)%8))
```
예: flag 17을 확인하려면 `flags[17/8] = flags[2]`의 `bit (17%8) = bit 1`을 검사.

---

## 3. Object 구조체 (352 bytes)

```
경로: objmon/o{nn}
파일당 레코드: 100개 (OFILESIZE)
레코드 크기: 352 bytes
VNUM 계산: file_index × 100 + record_index
```

### 필드 레이아웃

| Offset | Size | Type | Field | 설명 |
|--------|------|------|-------|------|
| 0 | 70 | char[70] | name | 아이템 이름 |
| 70 | 10 | char[10] | etc | 기타 정보 |
| 80 | 80 | char[80] | description | 바닥에 있을 때 설명 |
| 160 | 60 | char[3][20] | key | 검색 키워드 3개 |
| 220 | 80 | char[80] | use_output | 사용 시 출력 메시지 |
| 300 | 4 | long | value | 가치/가격 |
| 304 | 2 | short | weight | 무게 |
| 306 | 1 | char | type | 아이템 타입 (5=armor, 8=wand 등) |
| 307 | 1 | char | adjustment | 히트롤 보정치 |
| 308 | 2 | short | shotsmax | 최대 사용 횟수 |
| 310 | 2 | short | shotscur | 현재 사용 횟수 |
| 312 | 2 | short | ndice | 데미지 주사위 수 |
| 314 | 2 | short | sdice | 주사위 면 수 |
| 316 | 2 | short | pdice | 데미지 보정치 |
| 318 | 1 | char | armor | AC 보정치 |
| 319 | 1 | char | wearflag | 착용 위치 (1=body~20=wield) |
| 320 | 1 | char | magicpower | 마법력 |
| 321 | 1 | char | magicrealm | 마법 영역 |
| 322 | 2 | short | special | 특수 기능 번호 |
| 324 | 8 | char[8] | flags | 아이템 플래그 비트필드 |
| 332 | 1 | char | questnum | 퀘스트 번호 |
| 333 | 3 | — | (padding) | 포인터 정렬용 |
| 336 | 4 | ptr | first_obj | (무시) 내부 오브젝트 리스트 |
| 340 | 4 | ptr | parent_obj | (무시) 부모 오브젝트 |
| 344 | 4 | ptr | parent_rom | (무시) 부모 방 |
| 348 | 4 | ptr | parent_crt | (무시) 부모 크리처 |

### 빈 레코드 판별
`name[0:70]`이 전부 `\x00`이면 빈 슬롯으로 건너뛴다.

### 아이템 타입 값

| 값 | 상수 | 설명 |
|----|------|------|
| 0 | — | 무기 (기본) |
| 5 | ARMOR | 방어구 |
| 6 | POTION | 포션 |
| 7 | SCROLL | 스크롤 |
| 8 | WAND | 완드 |
| 9 | CONTAINER | 컨테이너 |
| 10 | MONEY | 돈 |
| 11 | KEY | 열쇠 |
| 12 | LIGHTSOURCE | 광원 |
| 13 | MISC | 기타 |
| 14 | CONTAINER2 | 컨테이너2 |
| 15 | OHPUP | HP 증가 |

---

## 4. Creature 구조체 (1184 bytes)

```
경로: objmon/m{nn}
파일당 레코드: 100개 (MFILESIZE)
레코드 크기: 1184 bytes
VNUM 계산: file_index × 100 + record_index
```

### 필드 레이아웃

| Offset | Size | Type | Field | 설명 |
|--------|------|------|-------|------|
| 0 | 2 | short | fd | 소켓 번호 (무시) |
| 2 | 1 | unsigned char | level | 레벨 (0-255) |
| 3 | 1 | char | type | 0=PLAYER, 1=MONSTER |
| 4 | 1 | char | class | 직업 (1-8) |
| 5 | 1 | char | race | 종족 (1-8) |
| 6 | 1 | char | numwander | 배회 범위 |
| 7 | 1 | — | (padding) | |
| 8 | 2 | short | alignment | 성향 (-32768~32767) |
| 10 | 1 | char | strength | 힘 |
| 11 | 1 | char | dexterity | 민첩 |
| 12 | 1 | char | constitution | 체력 |
| 13 | 1 | char | intelligence | 지능 |
| 14 | 1 | char | piety | 신앙 |
| 15 | 1 | — | (padding) | |
| 16 | 2 | short | hpmax | 최대 HP |
| 18 | 2 | short | hpcur | 현재 HP |
| 20 | 2 | short | mpmax | 최대 MP |
| 22 | 2 | short | mpcur | 현재 MP |
| 24 | 1 | char | armor | AC |
| 25 | 1 | char | thaco | THAC0 |
| 26 | 2 | — | (padding) | |
| 28 | 4 | long | experience | 경험치 |
| 32 | 4 | long | gold | 소지금 |
| 36 | 2 | short | ndice | 공격 주사위 수 |
| 38 | 2 | short | sdice | 주사위 면 수 |
| 40 | 2 | short | pdice | 데미지 보정치 |
| 42 | 2 | short | special | 특수 번호 |
| 44 | 80 | char[80] | name | 이름 |
| 124 | 80 | char[80] | description | 설명 |
| 204 | 80 | char[80] | talk | 대화/talk 파일 참조 |
| 284 | 15 | char[15] | etc | 기타 정보 |
| 299 | 60 | char[3][20] | key | 검색 키워드 3개 |
| 359 | 1 | — | (padding) | |
| 360 | 20 | long[5] | proficiency | 무기 숙련도 (sharp/thrust/blunt/pole/missile) |
| 380 | 16 | long[4] | realm | 마법 영역 레벨 (earth/wind/fire/water) |
| 396 | 16 | char[16] | spells | 알려진 주문 비트필드 |
| 412 | 8 | char[8] | flags | 몬스터 플래그 비트필드 |
| 420 | 16 | char[16] | quests | 퀘스트 비트필드 |
| 436 | 1 | char | questnum | 퀘스트 번호 |
| 437 | 1 | — | (padding) | |
| 438 | 20 | short[10] | carry | 랜덤 소지 아이템 |
| 458 | 2 | short | rom_num | 방 번호 |
| 460 | 80 | ptr[20] | ready | (무시) 장비 슬롯 포인터 |
| 540 | 80 | daily[10] | daily | (무시) 일일 사용 변수 |
| 620 | 540 | lasttime[45] | lasttime | (무시) 시간 기반 변수 |
| 1160 | 4 | ptr | following | (무시) |
| 1164 | 4 | ptr | first_fol | (무시) |
| 1168 | 4 | ptr | first_obj | (무시) |
| 1172 | 4 | ptr | first_enm | (무시) |
| 1176 | 4 | ptr | first_tlk | (무시) |
| 1180 | 4 | ptr | parent_rom | (무시) |

### 레코드 필터링
- `type == 1` (MONSTER)인 레코드만 파싱
- `type == 0` (PLAYER)은 건너뜀
- `name[0:80]`이 전부 null이면 빈 슬롯

---

## 5. Room 구조체 (480 bytes)

```
경로: rooms/r{nn}/r{nnnnn}
파일당 레코드: 1개 (개별 파일)
```

### 필드 레이아웃

| Offset | Size | Type | Field | 설명 |
|--------|------|------|-------|------|
| 0 | 80 | char[80] | name | 방 이름 |
| 80 | 2 | short | rom_num | 방 번호 |
| 82 | 2 | — | (padding) | |
| 84 | 4 | ptr | long_desc | (무시) 긴 설명 포인터 |
| 88 | 4 | ptr | short_desc | (무시) 짧은 설명 포인터 |
| 92 | 4 | ptr | obj_desc | (무시) 오브젝트 설명 포인터 |
| 96 | 2 | short | special | 특수 기능 번호 |
| 98 | 1 | char | trap | 함정 타입 |
| 99 | 1 | — | (padding) | |
| 100 | 2 | short | trapexit | 함정 출구 |
| 102 | 80 | char[80] | track | 추적 경로 |
| 182 | 8 | char[8] | flags | 방 플래그 비트필드 |
| 190 | 20 | short[10] | random | 랜덤 몬스터 VNUM (10개 슬롯) |
| 210 | 1 | char | traffic | 몬스터 출현 빈도 |
| 211 | 1 | — | (padding) | |
| 212 | 120 | lasttime[10] | perm_mon | 영구 몬스터 리스폰 타이머 |
| 332 | 120 | lasttime[10] | perm_obj | 영구 아이템 리스폰 타이머 |
| 452 | 4 | long | lVisitedTime | 방문 카운터 |
| 456 | 4 | long | established | 생성 시각 |
| 460 | 1 | char | lolevel | 최소 레벨 제한 |
| 461 | 1 | char | hilevel | 최대 레벨 제한 |
| 462 | 2 | — | (padding) | |
| 464 | 4 | ptr | first_ext | (무시) |
| 468 | 4 | ptr | first_obj | (무시) |
| 472 | 4 | ptr | first_mon | (무시) |
| 476 | 4 | ptr | first_ply | (무시) |

---

## 6. Exit 구조체 (44 bytes)

| Offset | Size | Type | Field | 설명 |
|--------|------|------|-------|------|
| 0 | 20 | char[20] | name | 출구 이름 (한글: "동", "서" 등) |
| 20 | 2 | short | room | 목적지 방 번호 |
| 22 | 4 | char[4] | flags | 출구 플래그 비트필드 |
| 26 | 2 | — | (padding) | lasttime 정렬용 |
| 28 | 12 | lasttime | ltime | 시간 기반 잠금 |
| 40 | 1 | char | key | 필요한 열쇠 번호 |
| 41 | 3 | — | (padding) | |

### 주의사항
- 출구 direction은 구조체에 저장되지 않음
- 방의 exit 리스트에서의 순서(index)가 direction을 결정
- 출구 이름이 direction을 나타냄 (예: "동", "서", "남", "북", "위", "아래")

---

## 7. Room 파일 형식 (가변 길이)

Room 파일은 고정 구조체 + 가변 길이 섹션으로 구성된다.

### 기록 순서 (write_rom 기준)

```
[1] room 구조체                    (480 bytes, 고정)
[2] int exit_count                 (4 bytes)
    exit_ 구조체 × exit_count      (44 bytes each)
[3] int monster_count              (4 bytes)
    creature + inventory × count   (가변, 재귀적)
[4] int object_count               (4 bytes)
    object + contents × count      (가변, 재귀적)
[5] int short_desc_len             (4 bytes)
    short_desc 문자열              (short_desc_len bytes, null 포함)
[6] int long_desc_len              (4 bytes)
    long_desc 문자열               (long_desc_len bytes, null 포함)
[7] int obj_desc_len               (4 bytes)
    obj_desc 문자열                (obj_desc_len bytes, null 포함)
```

### Monster 재귀 구조

```
creature 구조체         (1184 bytes)
int inv_count           (4 bytes)
  object + contents × inv_count  (각 object도 재귀)
```

### Object 재귀 구조

```
object 구조체           (352 bytes)
int contained_count     (4 bytes)
  object + contents × contained_count  (재귀)
```

### 문자열 길이
- `strlen(str) + 1` (null terminator 포함) 이 기록됨
- length가 0이면 문자열 데이터 없음

---

## 8. Object/Monster 파일 형식

```
경로: objmon/o{nn}  (Object)
경로: objmon/m{nn}  (Monster)
```

- 각 파일에 **최대 100개** 레코드가 연속 배치
- 파일 번호 `{nn}`이 file_index
- VNUM = `file_index × 100 + record_index`
- 일부 파일은 100개 미만의 레코드를 포함 (파일 크기가 작음)
- 파일 내에 구분자 없음 — 순수 레코드 연속 배치

---

## 9. Talk 파일 형식

```
경로: objmon/talk/{name}-{level}
인코딩: EUC-KR 텍스트
```

키워드와 응답이 줄 단위로 교대:

```
키워드1
응답1
키워드2
응답2
...
```

파일명에서 몬스터 매칭: `name`이 몬스터 이름, `level`이 레벨과 일치해야 함.

---

## 10. Ddesc 파일 형식

```
경로: objmon/ddesc/{name}_{level}
인코딩: EUC-KR 텍스트
```

파일 전체 내용이 몬스터의 상세 설명이다. 별도의 구분자 없이 텍스트 전체를 읽으면 된다.

파일명 구분자가 talk(`-`)과 다르게 밑줄(`_`)을 사용한다. 이름 자체에 밑줄이 포함될 수 있으므로 마지막 `_` 기준으로 분리한다.

---

## 11. Help 파일 형식

```
경로: help/help.{n}
인코딩: EUC-KR 텍스트
```

각 파일이 하나의 도움말 항목:
- 첫 줄: 키워드/제목 (콜론으로 끝날 수 있음)
- 나머지: 본문 텍스트

---

## 12. 플래그 비트 매크로

플래그는 `char flags[N]` 배열에 저장되며, 각 비트가 하나의 플래그를 나타낸다.

```
F_ISSET(p, f):
  byte_index = f / 8
  bit_index  = f % 8
  result     = flags[byte_index] & (1 << bit_index)
```

Python 변환:
```python
def flags_to_bit_positions(flag_bytes: bytes) -> list[int]:
    positions = []
    for byte_idx, byte_val in enumerate(flag_bytes):
        for bit in range(8):
            if byte_val & (1 << bit):
                positions.append(byte_idx * 8 + bit)
    return positions
```

### 플래그 배열 크기

| 구조체 | flags 크기 | 최대 플래그 수 |
|--------|-----------|---------------|
| room | 8 bytes | 64개 |
| creature | 8 bytes | 64개 |
| object | 8 bytes | 64개 |
| exit_ | 4 bytes | 32개 |
| creature.spells | 16 bytes | 128개 (실사용 63개) |
| creature.quests | 16 bytes | 128개 |
