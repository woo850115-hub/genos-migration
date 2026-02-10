# UIR (Universal Intermediate Representation) 스키마 참조

**Version**: 2.0
**정의 파일**: `src/genos/uir/schema.py`
**JSON Schema**: `schema/uir.schema.json`

---

## 개요

UIR은 MUD 게임 데이터의 소스 독립적인 중간 표현입니다. 어떤 MUD 코드베이스(CircleMUD, DikuMUD, ROM, SMAUG 등)에서 파싱된 데이터든 동일한 UIR 구조로 변환된 후, 타겟 플랫폼(GenOS)의 아티팩트로 컴파일됩니다.

```
┌─────────────┐     ┌─────┐     ┌──────────────┐
│ CircleMUD   │────→│     │────→│ PostgreSQL   │
│ DikuMUD     │────→│ UIR │────→│ Lua Scripts  │
│ ROM / SMAUG │────→│     │────→│ Config Files │
└─────────────┘     └─────┘     └──────────────┘
   Adapters        Neutral      Compilers
```

---

## 최상위 구조

```python
@dataclass
class UIR:
    uir_version: str                           # "1.0"
    source_mud: SourceMudInfo | None           # 소스 정보
    metadata: GameMetadata                     # 게임 메타데이터
    migration_stats: MigrationStats            # 변환 통계
    rooms: list[Room]                          # 방
    items: list[Item]                          # 아이템/오브젝트
    monsters: list[Monster]                    # 몬스터/NPC
    character_classes: list[CharacterClass]     # 플레이어 클래스
    combat_system: CombatSystem                # 전투 시스템
    commands: list[Command]                    # 게임 커맨드
    zones: list[Zone]                          # 존/지역
    shops: list[Shop]                          # 상점
    triggers: list[Trigger]                    # 스크립트 트리거
    quests: list[Quest]                        # 퀘스트
    socials: list[Social]                      # 감정표현 (Phase 2)
    help_entries: list[HelpEntry]              # 도움말 (Phase 2)
    skills: list[Skill]                        # 스킬/스펠 메타데이터 (Phase 2)
    races: list[Race]                          # 종족 (Phase 2)
    extensions: dict[str, Any]                 # 소스별 확장 데이터
```

---

## 엔티티 상세

### Room

방/공간을 표현합니다. 플레이어가 탐험하는 기본 단위.

```python
@dataclass
class Room:
    vnum: int                                  # 고유 식별자
    name: str                                  # 방 이름
    description: str                           # 방 설명 (여러 줄)
    zone_number: int                           # 소속 존 번호
    room_flags: list[int]                      # 방 플래그 (비트 위치 리스트)
    sector_type: int                           # 지형 타입 (0-9)
    exits: list[Exit]                          # 출구 목록 (최대 10방향)
    extra_descriptions: list[ExtraDescription]  # 추가 살펴보기 설명
    trigger_vnums: list[int]                   # 부착된 트리거 VNUM
    # tbaMUD 확장
    tba_unlinked: int
    tba_previous: int
    tba_map_x: int
    tba_map_y: int
```

**room_flags 표현**: 정수 비트마스크가 아닌, 설정된 비트 위치의 리스트입니다.
예: `room_flags=[3, 4]` = INDOORS + PEACEFUL

### Exit

방 간의 연결(출구).

```python
@dataclass
class Exit:
    direction: int       # 0-9 (N/E/S/W/U/D/NW/NE/SE/SW)
    destination: int     # 도착 방 VNUM (-1=없음)
    description: str     # 출구 살펴보기 설명
    keyword: str         # 문 키워드 (open/close 대상)
    door_flags: int      # 문 플래그 비트마스크
    key_vnum: int        # 열쇠 아이템 VNUM (-1=없음)
```

### Item

게임 내 오브젝트/아이템.

```python
@dataclass
class Item:
    vnum: int
    keywords: str                              # 검색 키워드 (공백 구분)
    short_description: str                     # 인벤토리 표시명
    long_description: str                      # 바닥에 놓였을 때 표시
    action_description: str                    # 사용시 표시
    item_type: int                             # 아이템 타입 (1-23)
    extra_flags: list[int]                     # 아이템 추가 플래그
    wear_flags: list[int]                      # 장착 가능 위치
    values: list[int]                          # 타입별 4개 값
    weight: int
    cost: int                                  # 판매 가격
    rent: int                                  # 일일 보관 비용
    timer: int                                 # 소멸 타이머
    min_level: int                             # 최소 사용 레벨
    extra_descriptions: list[ExtraDescription]
    affects: list[ItemAffect]                  # 스탯 보정 (최대 6개)
    trigger_vnums: list[int]
```

### Monster

NPC/몬스터. Enhanced 포맷 기준.

```python
@dataclass
class Monster:
    vnum: int
    keywords: str
    short_description: str                     # 전투/대화시 표시명
    long_description: str                      # 방 안에서의 묘사
    detailed_description: str                  # look 시 상세 묘사
    action_flags: list[int]                    # MOB 플래그
    affect_flags: list[int]                    # AFF 플래그
    alignment: int                             # -1000(악) ~ +1000(선)
    level: int
    hitroll: int                               # 명중 보너스
    armor_class: int                           # AC (-100 ~ 100)
    hp_dice: DiceRoll                          # HP = NdS+B
    damage_dice: DiceRoll                      # 데미지 = NdS+B
    gold: int                                  # 소지 골드
    experience: int                            # 처치 경험치
    load_position: int                         # 로드시 자세
    default_position: int                      # 기본 자세
    sex: int                                   # 0=중성, 1=남, 2=여
    bare_hand_attack: int                      # 맨손 공격 타입 (0-14)
    trigger_vnums: list[int]
    mob_type: str                              # "E"=Enhanced, "S"=Simple
```

### DiceRoll

주사위 표기법.

```python
@dataclass
class DiceRoll:
    num: int       # 주사위 개수
    size: int      # 주사위 면 수
    bonus: int     # 고정 보너스
    # str(): "6d6+340"
```

### Zone

존/지역 정의와 리셋 커맨드.

```python
@dataclass
class Zone:
    vnum: int
    name: str
    builders: str                              # 제작자 이름
    lifespan: int                              # 리셋 주기 (분)
    bot: int                                   # 시작 VNUM
    top: int                                   # 종료 VNUM
    reset_mode: int                            # 0/1/2
    zone_flags: list[int]
    min_level: int                             # -1=제한없음
    max_level: int
    reset_commands: list[ZoneResetCommand]
```

### Trigger

DG Script 트리거.

```python
@dataclass
class Trigger:
    vnum: int
    name: str
    attach_type: int     # 0=MOB, 1=OBJ, 2=WLD
    trigger_type: int    # 타입 플래그 (bitvector)
    numeric_arg: int     # 발동 확률 등
    arg_list: str        # 인자 문자열
    script: str          # DG Script 본문 전체
```

### Shop

상점 정의.

```python
@dataclass
class Shop:
    vnum: int
    selling_items: list[int]     # 판매 아이템 VNUM 목록
    profit_buy: float            # 구매 배율 (예: 1.20)
    profit_sell: float           # 판매 배율 (예: 0.90)
    accepting_types: list[int]   # 매입 가능 아이템 타입
    no_such_item1: str           # 메시지 7종
    no_such_item2: str
    do_not_buy: str
    missing_cash1: str
    missing_cash2: str
    message_buy: str
    message_sell: str
    keeper_vnum: int             # 점원 MOB VNUM
    shop_room: int               # 상점 방 VNUM
    open1: int                   # 영업시간
    close1: int
    open2: int
    close2: int
```

### CharacterClass

플레이어 클래스 정의.

```python
@dataclass
class CharacterClass:
    id: int
    name: str                    # "Magic User", "Warrior" 등
    abbreviation: str            # "Mu", "Wa"
    base_thac0: int              # 기본 THAC0 (20)
    thac0_gain: float            # 레벨당 THAC0 감소율
    hp_gain_min: int             # 레벨업 HP 증가 최소
    hp_gain_max: int             # 레벨업 HP 증가 최대
    mana_gain_min: int
    mana_gain_max: int
    move_gain_min: int
    move_gain_max: int
    extensions: dict[str, Any]   # 소스별 확장 데이터
```

### Social (Phase 2)

감정표현/소셜 커맨드.

```python
@dataclass
class Social:
    command: str = ""                  # 소셜 커맨드 이름 ("smile", "laugh")
    min_victim_position: int = 0       # 대상의 최소 포지션
    flags: int = 0                     # 소셜 플래그
    no_arg_to_char: str = ""           # 대상 없음 → 자신에게 표시
    no_arg_to_room: str = ""           # 대상 없음 → 방에 표시
    found_to_char: str = ""            # 대상 있음 → 자신에게 표시
    found_to_room: str = ""            # 대상 있음 → 방에 표시
    found_to_victim: str = ""          # 대상 있음 → 대상에게 표시
    not_found: str = ""                # 대상을 찾지 못함
    self_to_char: str = ""             # 자기 자신 대상 → 자신에게 표시
    self_to_room: str = ""             # 자기 자신 대상 → 방에 표시
```

### HelpEntry (Phase 2)

도움말 항목.

```python
@dataclass
class HelpEntry:
    keywords: list[str] = field(default_factory=list)  # 검색 키워드
    min_level: int = 0                                  # 최소 열람 레벨
    text: str = ""                                      # 도움말 본문
```

### Skill (Phase 2)

스킬/스펠 메타데이터. 로직은 포함하지 않고 정의 데이터만.

```python
@dataclass
class Skill:
    id: int = 0                                         # 스펠/스킬 ID
    name: str = ""                                      # 영문 이름 ("magic missile")
    spell_type: str = ""                                # "spell" 또는 "skill"
    max_mana: int = 0                                   # 최대 마나 소모
    min_mana: int = 0                                   # 최소 마나 소모
    mana_change: int = 0                                # 레벨당 마나 감소
    min_position: int = 0                               # 최소 시전 포지션
    targets: int = 0                                    # 타겟 플래그
    violent: bool = False                               # 적대적 여부
    routines: int = 0                                   # 루틴 플래그
    wearoff_msg: str = ""                               # 효과 해제 메시지
    class_levels: dict[int, int] = field(default_factory=dict)  # 클래스ID → 최소레벨
    extensions: dict[str, Any] = field(default_factory=dict)    # 확장 데이터
```

**class_levels 예시**: `{0: 1, 1: 3}` → 클래스 0(Magic User)은 레벨 1, 클래스 1(Cleric)은 레벨 3에 습득.

### Race (Phase 2)

종족 정의. tbaMUD에는 없고 Simoon 등 확장 MUD에서 사용.

```python
@dataclass
class Race:
    id: int = 0
    name: str = ""                                      # "Human", "Elf" 등
    abbreviation: str = ""                              # "Hu", "El"
    stat_modifiers: dict[str, int] = field(default_factory=dict)  # {"str": 1, "dex": -1}
    allowed_classes: list[int] = field(default_factory=list)      # 허용 클래스 ID
    extensions: dict[str, Any] = field(default_factory=dict)      # 확장 데이터
```

### Command (Phase 2 확장)

게임 커맨드 정의. `src/interpreter.c`의 `cmd_info[]` 배열에서 추출.

```python
@dataclass
class Command:
    name: str = ""               # 커맨드 이름 ("look", "kill")
    min_position: int = 0        # 실행 가능 최소 포지션
    min_level: int = 0           # 실행 가능 최소 레벨
    min_match: str = ""          # 최소 약어 ("lo" for "look"), tbaMUD 전용
    handler: str = ""            # C 함수 이름 ("do_look")
    subcmd: int = 0              # 서브커맨드 번호
    category: str = ""           # 분류 ("movement", "combat", "info" 등)
```

### CombatSystem

전투 시스템 파라미터.

```python
@dataclass
class CombatSystem:
    type: str                    # "thac0", "d20", "custom"
    base_thac0: int              # 20
    ac_range: tuple[int, int]    # (-10, 10)
    damage_types: list[str]      # ["hit", "sting", "whip", ...]
```

---

## 검증 (Validation)

`validate_uir(uir)` 함수가 다음을 검증합니다:

1. **Exit 참조 무결성**: 출구 목적지 방이 실제 존재하는지
2. **Trigger 참조**: 부착된 트리거 VNUM이 트리거 목록에 있는지
3. **Zone 리셋 커맨드**: M/O 커맨드가 유효한 mob/item을 참조하는지
4. **Shop keeper**: 상점 점원 VNUM이 유효한 mob인지
5. **필수 필드**: source_mud 정보, 최소 1개 room

반환: `ValidationResult(valid=bool, errors=list, warnings=list)`

---

## MigrationStats

변환 통계 추적.

```python
@dataclass
class MigrationStats:
    total_rooms: int = 0
    total_items: int = 0
    total_monsters: int = 0
    total_zones: int = 0
    total_shops: int = 0
    total_triggers: int = 0
    total_quests: int = 0
    total_socials: int = 0          # Phase 2
    total_help_entries: int = 0     # Phase 2
    total_skills: int = 0           # Phase 2
    total_commands: int = 0         # Phase 2
    total_races: int = 0            # Phase 2
    parse_errors: int = 0
    parse_warnings: int = 0
```

---

## 직렬화

UIR은 YAML 또는 JSON으로 출력 가능합니다.

```bash
genos migrate /path/to/tbamud -f yaml   # YAML (기본)
genos migrate /path/to/tbamud -f json   # JSON
```

tbaMUD 전체 변환시 UIR YAML은 약 878,000 라인(~40MB)입니다.
