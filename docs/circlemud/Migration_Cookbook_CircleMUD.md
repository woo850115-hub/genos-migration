# CircleMUD/tbaMUD Migration Cookbook

**CircleMUD/tbaMUD 전용 마이그레이션 가이드**

공통 사용법(설치, CLI, 출력 구조)은 [Migration_Cookbook](../common/Migration_Cookbook.md)을 참조하세요.

---

## 전제 조건

tbaMUD 소스는 표준 디렉토리 구조를 따라야 합니다:

```
tbamud/
├── lib/
│   └── world/
│       ├── wld/    # *.wld 파일 + index
│       ├── obj/    # *.obj 파일 + index
│       ├── mob/    # *.mob 파일 + index
│       ├── zon/    # *.zon 파일 + index
│       ├── trg/    # *.trg 파일 + index
│       ├── shp/    # *.shp 파일 + index
│       └── qst/    # *.qst 파일 + index
└── src/            # C 소스 (선택적)
```

감지 기준: `lib/world/wld/` + `lib/world/mob/` 디렉토리가 존재하면 CircleMUD로 인식합니다.

---

## 분석 출력 예시

```bash
genos analyze /path/to/tbamud
```

```
Detected: CircleMudAdapter

MUD Type: CircleMUD/tbaMUD
Source: /home/genos/workspace/tbamud
Rooms: 12701
Items: 4765
Mobs: 3705
Zones: 189
Shops: 334
Triggers: 1461
Quests: 1
Socials: 104
Help Entries: 721
Skills: 65
Commands: 301
Races: 0
Estimated Conversion: 100.0%
```

---

## 변환 결과 해석

### SQL Schema (schema.sql)

21개 테이블이 생성됩니다:

| 테이블 | 설명 | 주요 JSONB 컬럼 | Phase |
|--------|------|-----------------|-------|
| rooms | 방 | exits, room_flags, extra_descs | 1 |
| items | 아이템 | values, extra_flags, wear_flags, affects | 1 |
| monsters | 몬스터 | action_flags, affect_flags | 1 |
| classes | 클래스 | extensions | 1 |
| zones | 존 | zone_flags, reset_commands | 1 |
| shops | 상점 | selling_items | 1 |
| triggers | 트리거 | - (script는 TEXT) | 1 |
| quests | 퀘스트 | - | 1 |
| socials | 감정표현 | - | 2 |
| help_entries | 도움말 | keywords | 2 |
| commands | 커맨드 목록 | - | 2 |
| skills | 스킬/스펠 | class_levels, extensions | 2 |
| races | 종족 | stat_modifiers, allowed_classes | 2 |
| game_configs | 게임 설정 | - | 3 |
| experience_table | 경험치 테이블 | - | 3 |
| thac0_table | THAC0 테이블 | - | 3 |
| saving_throws | 세이빙 스로우 | - | 3 |
| level_titles | 레벨 칭호 | - | 3 |
| attribute_modifiers | 능력치 보정 | modifiers (JSONB) | 3 |
| practice_params | 연습 파라미터 | extensions (JSONB) | 3 |

### Seed Data (seed_data.sql)

모든 엔티티의 INSERT 문입니다. 트랜잭션으로 감싸져 있어 원자적 로드가 가능합니다.

```sql
BEGIN;
INSERT INTO rooms (vnum, name, description, ...) VALUES (...);
-- ... (12,700 rooms)
INSERT INTO items (vnum, keywords, ...) VALUES (...);
-- ... (4,765 items)
COMMIT;
```

### Lua: Combat System (combat.lua)

```lua
-- THAC0 기반 명중 판정
Combat.calculate_hit(thac0, ac, hitroll)

-- 데미지 주사위 굴림
Combat.roll_damage(dice_num, dice_size, bonus)

-- 클래스/레벨별 THAC0 조회
Combat.get_thac0(class_id, level)
```

### Lua: Game Config (config.lua) — Phase 3

게임 설정을 카테고리별로 그룹핑합니다. `config.c`에서 추출한 ~54개 설정.

```lua
Config.game = {
    script_players = false,
    level_can_shout = 1,
    tunnel_size = 2,
    ...
}
Config.rent = { free_rent = true, ... }
Config.room = { mortal_start_room = 3001, ... }
```

### Lua: Experience Tables (exp_tables.lua) — Phase 3

클래스/레벨별 필요 경험치. `class.c`의 `level_exp()` 함수에서 추출.

```lua
ExpTables[0] = { [0] = 0, [1] = 1, [2] = 2500, ... }  -- Magic User
ExpTables[3] = { [0] = 0, [1] = 1, [2] = 2000, ... }  -- Warrior

function ExpTables.get_exp_required(class_id, level)
```

### Lua: Stat Tables (stat_tables.lua) — Phase 3

THAC0, 세이빙 스로우, 능력치 보정 테이블. `class.c`, `constants.c`에서 추출.

```lua
StatTables.thac0[0] = { [1] = 20, [2] = 20, ... }  -- Magic User THAC0
StatTables.saving_throws[0][0] = { [1] = 70, ... }  -- Magic User PARA
StatTables.str_app[18] = { tohit = 1, todam = 2, carry_w = 220, wield_w = 10 }
```

### Lua: Triggers (triggers.lua)

DG Script가 Lua로 변환되며, 완전 자동 변환이 불가능한 부분은 `-- TODO:` 주석이 붙습니다.

자동 변환 가능:
- `say`, `emote` → `self:say()`, `self:emote()`
- `if/elseif/else/end` → Lua 조건문
- `wait N sec` → `coroutine.yield(N)`
- `*` 주석 → `--` 주석

수동 변환 필요 (`-- TODO:` 표시):
- `%load%` (엔티티 로드)
- `%purge%` (엔티티 제거)
- `%send%`, `%echoaround%` (메시지 전송)
- `eval` (변수 연산)
- `give`, `unlock`, `open`, `close`, `lock` (게임 커맨드)

---

## 검증 체크리스트

### 1. 파싱 정합성

```bash
# 테스트 실행
source .venv/bin/activate
python -m pytest tests/ -v
```

### 2. 엔티티 수 대조

| 타입 | 기대 수 (tbaMUD stock) | Phase |
|------|----------------------|-------|
| Rooms | ~12,700 | 1 |
| Items | ~4,765 | 1 |
| Mobs | ~3,705 | 1 |
| Zones | 189 | 1 |
| Shops | ~334 | 1 |
| Triggers | ~1,461 | 1 |
| Quests | 1 | 1 |
| Socials | ~104 | 2 |
| Help | ~721 | 2 |
| Commands | ~275 | 2 |
| Skills | ~65 | 2 |
| Commands | ~301 | 2 |
| Game Configs | ~54 | 3 |
| Exp Table | ~128 | 3 |
| THAC0 Table | ~140 | 3 |
| Saving Throws | ~870 | 3 |
| Level Titles | ~204 | 3 |
| Attr Modifiers | ~161 | 3 |
| Practice Params | ~4 | 3 |

### 3. 특정 엔티티 검증

파싱 후 주요 엔티티가 올바르게 변환되었는지 확인:

```python
from genos.adapters.circlemud.adapter import CircleMudAdapter

adapter = CircleMudAdapter("/path/to/tbamud")
uir = adapter.parse()

# Puff the Dragon (mob vnum 1)
puff = next(m for m in uir.monsters if m.vnum == 1)
assert puff.level == 34
assert puff.hp_dice.num == 6
assert puff.hp_dice.size == 6
assert puff.hp_dice.bonus == 340

# The Void (room vnum 0)
void = next(r for r in uir.rooms if r.vnum == 0)
assert "floating" in void.description.lower()
assert any(e.direction == 4 for e in void.exits)  # UP exit
```

### 4. SQL 유효성

생성된 SQL이 PostgreSQL에서 오류 없이 실행되는지 확인:

```bash
psql -d testdb -f output/sql/schema.sql
psql -d testdb -f output/sql/seed_data.sql
psql -d testdb -c "SELECT count(*) FROM rooms;"
```

---

## 트러블슈팅

### "Could not detect MUD type"

소스 디렉토리 구조를 확인하세요. `lib/world/wld/`와 `lib/world/mob/` 디렉토리가 존재해야 합니다.

### 파싱 경고 (Parse Warnings)

`-v` 플래그로 상세 로그를 확인하세요:

```bash
genos -v migrate /path/to/mud
```

일반적인 경고:
- "Error parsing <file>": 파일 형식 문제. 해당 파일을 수동 검사 필요.
- 비어있는 파일은 자동 건너뜀

### UIR 검증 경고

검증 경고는 참조 무결성 문제를 나타냅니다:
- "exit points to non-existent room": 출구가 없는 방을 가리킴 (다른 존의 방일 수 있음)
- "trigger not found": 트리거 파일이 누락되었거나 VNUM이 잘못됨
- "keeper mob not found": 상점 점원 MOB이 없음

이들은 경고(warning)이므로 마이그레이션 자체는 계속 진행됩니다.

---

## 알려진 한계

1. **Simple (S) 포맷 모바일**: 테스트되지 않음 (tbaMUD stock은 모두 Enhanced 포맷)
2. **DG Script 완전 변환**: 약 60-70%만 자동 변환, 나머지는 TODO 마킹
3. **Spell/Skill 로직**: 스킬 메타데이터(이름, 마나, 타겟 등)는 마이그레이션 되지만, 실제 효과 로직은 재구현 필요
4. **Player 데이터**: 플레이어 세이브 파일(.plr)은 마이그레이션 대상 아님
5. **Binary 데이터**: 바이너리 세이브 파일은 지원하지 않음
6. **C 소스 파싱 한계**: cmd_info[], spello(), config 변수, 경험치/THAC0/세이빙 스로우 추출은 모두 정규식 기반이므로, 소스가 크게 수정된 MUD에서는 수동 조정 필요
7. **Phase 3 데이터 소스 의존**: config.c, class.c, constants.c 파일이 `src/` 디렉토리에 존재해야 Phase 3 데이터가 추출됨. 파일이 없으면 해당 항목은 빈 리스트로 처리
