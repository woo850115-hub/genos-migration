# 파서 구현 노트 — 3eyes 바이너리 파싱 삽질 기록

3eyes 어댑터를 구현하면서 발견한 함정, 비직관적인 형식 특성, 디버깅 과정에서 배운 교훈을 기록합니다.

---

## 1. 구조체 패딩을 무시하면 모든 필드가 어긋난다

### 문제
C 구조체를 순서대로 나열하고 단순히 크기를 더하면 실제 오프셋과 맞지 않는다. 32-bit Linux의 자연 정렬(natural alignment) 규칙에 따라 패딩 바이트가 삽입된다.

### 실제 예시 — creature 구조체

```c
short fd;             // offset 0 (2 bytes)
unsigned char level;  // offset 2 (1 byte)
char type;            // offset 3 (1 byte)
char class;           // offset 4 (1 byte)
char race;            // offset 5 (1 byte)
char numwander;       // offset 6 (1 byte)
                      // offset 7: ★1 byte padding★ (short 정렬)
short alignment;      // offset 8 (2 bytes)
```

패딩이 없다고 가정하면 alignment가 offset 7에 있을 것 같지만, short는 2-byte 정렬이 필요하므로 실제로는 offset 8이다.

### 근거 — ctypes로 검증

```python
import ctypes

class Creature(ctypes.Structure):
    _fields_ = [
        ("fd", ctypes.c_short),
        ("level", ctypes.c_ubyte),
        ("type", ctypes.c_char),
        # ...
    ]

print(ctypes.sizeof(Creature))  # 1184 ✓
```

### 해결

모든 구조체의 오프셋을 ctypes로 검증한 후 하드코딩했다. 주요 패딩 위치:

| 구조체 | 패딩 위치 (offset) | 원인 |
|--------|-------------------|------|
| creature | 7 | short alignment (numwander→alignment) |
| creature | 15 | short alignment (piety→hpmax) |
| creature | 26-27 | long alignment (thaco→experience) |
| creature | 359 | long alignment (key→proficiency) |
| creature | 437 | short alignment (questnum→carry) |
| object | 333-335 | pointer alignment (questnum→first_obj) |
| room | 82-83 | pointer alignment (rom_num→long_desc) |
| room | 99 | short alignment (trap→trapexit) |
| room | 211 | lasttime alignment (traffic→perm_mon) |
| room | 462-463 | pointer alignment (hilevel→first_ext) |
| exit_ | 26-27 | lasttime alignment (flags→ltime) |
| exit_ | 41-43 | struct tail padding |

---

## 2. 파일 크기가 100 × struct_size가 아닌 경우가 있다

### 문제
초기 구현에서 `file_size == SIZEOF * 100`을 detect 조건으로 사용했더니, 일부 파일에서 detect가 실패했다.

```
m03: 117,216 bytes (expected 118,400)
m05: 111,296 bytes (expected 118,400)
```

### 근거
3eyes 서버가 100개 미만의 레코드만 사용하는 경우, 파일 끝에 빈 레코드를 채우지 않고 실제 사용 중인 레코드까지만 기록한다. m03은 99개 레코드(117,216 / 1,184 = 98.99...)이다.

### 해결
detect에서는 "크기가 struct_size의 배수"인지만 확인하고, 파싱에서는 `min(file_size // struct_size, 100)`으로 레코드 수를 결정한다.

```python
# detect
for mfile in sorted(self._objmon_dir.glob("m[0-9][0-9]")):
    size = mfile.stat().st_size
    if size > 0 and size % SIZEOF_CREATURE == 0:
        return True

# parse
record_count = min(len(data) // SIZEOF_CREATURE, RECORDS_PER_FILE)
```

---

## 3. Room 파일의 설명 순서: short → long → obj (직관과 반대)

### 문제
Room 설명이 "long → short → obj" 순서일 것으로 예상했으나, 실제로는 C 소스의 `write_rom()` 순서를 따라 **short → long → obj** 순서로 기록된다.

### 근거 — files1.c의 write_rom()

```c
// short_desc 먼저
if(!rom_ptr->short_desc) cnt = 0;
else cnt = strlen(rom_ptr->short_desc) + 1;
write(fd, &cnt, sizeof(int));
if(cnt) write(fd, rom_ptr->short_desc, cnt);

// long_desc 다음
if(!rom_ptr->long_desc) cnt = 0;
else cnt = strlen(rom_ptr->long_desc) + 1;
write(fd, &cnt, sizeof(int));
if(cnt) write(fd, rom_ptr->long_desc, cnt);

// obj_desc 마지막
if(!rom_ptr->obj_desc) cnt = 0;
...
```

### 해결

```python
short_desc, pos = _read_length_prefixed_string(data, pos)
long_desc, pos = _read_length_prefixed_string(data, pos)
obj_desc, pos = _read_length_prefixed_string(data, pos)
```

---

## 4. Room 파일의 가변 길이 섹션은 재귀적이다

### 문제
Room 파일에서 monster와 object 섹션을 건너뛸 때, 단순히 `pos += SIZEOF_CREATURE * count`로 건너뛸 수 없다. 각 creature는 인벤토리 오브젝트를 가질 수 있고, 각 오브젝트는 다시 내부 오브젝트를 가질 수 있다.

### 근거 — write_rom의 구조

```
creature(1184) + int(inv_count) + [object(352) + int(contained) + [재귀...]] × inv_count
```

실제로 room 파일에서 monster가 아이템을 소지하고, 그 아이템이 컨테이너여서 다시 아이템을 포함하는 경우가 있다.

### 해결

재귀 skip 함수 구현:

```python
def _skip_object_with_contents(data, pos):
    pos += SIZEOF_OBJECT  # 352 bytes
    cnt = read_int(data, pos)
    pos += 4
    for _ in range(cnt):
        pos = _skip_object_with_contents(data, pos)  # 재귀
    return pos

def _skip_creature_with_inventory(data, pos):
    pos += SIZEOF_CREATURE  # 1184 bytes
    cnt = read_int(data, pos)
    pos += 4
    for _ in range(cnt):
        pos = _skip_object_with_contents(data, pos)
    return pos
```

---

## 5. Creature의 type 필드로 PLAYER를 걸러야 한다

### 문제
Monster 파일에 type=0(PLAYER) 레코드가 섞여 있다. 실제로는 빈 슬롯이나 삭제된 데이터일 수 있지만, name 필드에 데이터가 남아있으면 파싱이 시도된다.

### 근거 — mtype.h

```c
#define PLAYER  0
#define MONSTER 1
#define NPC     2
#define KILLER  3
```

서버에서 몬스터 파일에 플레이어 데이터를 임시 저장하거나, 이전 데이터가 덮어쓰이지 않고 남아있는 경우가 있다.

### 해결

```python
crt_type = read_byte(record, 3)  # offset 3: type
if crt_type != CREATURE_MONSTER:
    continue
```

---

## 6. Talk 파일과 Ddesc 파일의 파일명 구분자가 다르다

### 문제
Talk 파일은 `{name}-{level}` 형식(하이픈), ddesc 파일은 `{name}_{level}` 형식(밑줄)이다. 이름 자체에 밑줄이 포함될 수 있어서 단순 split으로는 올바르게 분리되지 않는다.

### 예시

```
talk/길라잡이-25       → name="길라잡이", level=25
ddesc/검은_알_10       → name="검은_알", level=10  (밑줄이 이름의 일부)
ddesc/마계도시의_시장_127 → name="마계도시의_시장", level=127
```

### 해결

마지막 구분자 기준으로 분리 (`rsplit`):

```python
def parse_talk_filename(filename):
    parts = filename.rsplit("-", 1)  # 마지막 하이픈 기준
    return parts[0], int(parts[1])

def parse_ddesc_filename(filename):
    parts = filename.rsplit("_", 1)  # 마지막 밑줄 기준
    return parts[0], int(parts[1])
```

---

## 7. Ddesc 몬스터 매칭 시 밑줄↔공백 변환이 필요하다

### 문제
Ddesc 파일명에서는 공백이 밑줄로 대체된다. 그러나 실제 몬스터 데이터의 이름에는 공백이 사용된다.

```
ddesc 파일명: "블랙_드래건_127"  → name = "블랙_드래건"
monster 이름: "블랙 드래건"      → 불일치!
```

### 해결

밑줄을 공백으로 변환하여 재시도:

```python
name_display = name.replace("_", " ")
mob = mob_lookup.get((name_display, level))
if mob is None:
    mob = mob_lookup.get((name, level))  # 원본으로도 시도
```

이렇게 해도 41개 talk 파일 중 9개, 39개 ddesc 파일 중 2개가 매칭 실패한다. 이는 파일명과 실제 몬스터 이름의 불일치(오타, 삭제된 몬스터 등)가 원인이다.

---

## 8. Exit의 direction은 구조체가 아닌 리스트 인덱스에서 결정된다

### 문제
`exit_` 구조체에 direction 필드가 없다. CircleMUD에서는 exit가 `world[room].dir_option[NUM_OF_DIRS]` 고정 배열에 direction별로 저장되지만, 3eyes(Mordor)에서는 linked list로 관리된다.

### 근거
Room 파일에서 exit가 기록된 순서가 곧 방향을 나타낸다. 첫 번째 exit가 direction 0, 두 번째가 direction 1, ... 이 순서는 CircleMUD의 표준 방향(N=0, E=1, S=2, W=3, U=4, D=5)과 반드시 일치하지는 않는다.

### 해결
현재 구현에서는 리스트 인덱스를 direction으로 사용한다. 실제 방향은 exit의 `name` 필드("동", "서", "남", "북" 등)에서 유추해야 하며, 추후 이름→방향 매핑을 추가할 수 있다.

---

## 9. read_crt 후 talk/etc 필드 패치 로직

### 문제
C 소스의 `read_crt()`에 특이한 로직이 있다:

```c
if(strlen(crt_ptr->talk) < 2) {
    strcpy(crt_ptr->talk, crt_ptr->etc);
    crt_ptr->talk[15] = 0;
}
for(i=0; i<15; i++)
    crt_ptr->etc[i] = 0;
```

talk 필드가 비어있으면 etc에서 복사하고, etc를 초기화한다. 이 로직은 **디스크에 기록된 후**가 아니라 **메모리에서 읽은 후**에 실행되므로, 디스크의 바이너리를 직접 읽는 우리 파서에는 영향이 없다.

### 해결
디스크 데이터를 그대로 파싱한다. 이 런타임 패치 로직은 무시해도 안전하다.

---

## 10. 3eyes의 Color Code 형식

### 문제
방 설명에 `#색상{텍스트}` 형식의 색상 코드가 사용된다:

```
#녹{검제3의 }#빨{검눈}으로 오신것을 환영합니다.
```

이 형식은 CircleMUD의 `&R`, `&G` 코드나 Simoon의 `&cNN` 코드와 완전히 다른 3eyes 고유 형식이다.

### 확인된 색상 코드

| 코드 | 색상 |
|------|------|
| `#녹{...}` | 녹색 (green) |
| `#빨{...}` | 빨간색 (red) |
| `#노{...}` | 노란색 (yellow) |

### 해결
현재 파서에서는 색상 코드를 원본 그대로 유지한다. GenOS 변환 시 후처리 단계에서 이 패턴을 정규식으로 매칭하여 적절한 마크업으로 변환해야 한다.
