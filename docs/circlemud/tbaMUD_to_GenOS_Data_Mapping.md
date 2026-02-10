# tbaMUD → GenOS 데이터 매핑 참조

**Version**: 2.0

이 문서는 tbaMUD의 데이터 파일/C 소스 구조가 UIR 데이터클래스, 그리고 최종 GenOS 데이터베이스 스키마로 어떻게 매핑되는지를 추적합니다.

---

## 1. Room 매핑

### tbaMUD C → UIR → PostgreSQL

| tbaMUD (`struct room_data`) | UIR (`Room`) | PostgreSQL (`rooms`) |
|---|---|---|
| `number` (room_vnum) | `vnum` | `vnum INTEGER PK` |
| `name` (char*) | `name` | `name TEXT` |
| `description` (char*) | `description` | `description TEXT` |
| `zone` (zone_rnum) | `zone_number` | `zone_number INTEGER` |
| `sector_type` (int) | `sector_type` | `sector_type INTEGER` |
| `room_flags[4]` (int[]) | `room_flags: list[int]` | `room_flags JSONB` |
| `dir_option[10]` (struct*[]) | `exits: list[Exit]` | `exits JSONB` |
| `ex_description` (linked list) | `extra_descriptions` | `extra_descs JSONB` |
| `proto_script` (trigger list) | `trigger_vnums` | `trigger_vnums JSONB` |

### Room Flags 비트 → 이름 매핑

| 비트 | C 상수 | UIR flags 리스트 값 | GenOS 의미 |
|------|--------|-------------------|-----------|
| 0 | ROOM_DARK | `0` | 빛 필요 |
| 1 | ROOM_DEATH | `1` | 즉사 트랩 |
| 2 | ROOM_NOMOB | `2` | NPC 진입 불가 |
| 3 | ROOM_INDOORS | `3` | 실내 (날씨 없음) |
| 4 | ROOM_PEACEFUL | `4` | 전투 불가 |
| 5 | ROOM_SOUNDPROOF | `5` | 소리 차단 |
| 6 | ROOM_NOTRACK | `6` | 추적 불가 |
| 7 | ROOM_NOMAGIC | `7` | 마법 불가 |
| 8 | ROOM_TUNNEL | `8` | 1인 제한 |
| 9 | ROOM_PRIVATE | `9` | 텔레포트 불가 |
| 10 | ROOM_GODROOM | `10` | 관리자 전용 |
| 16 | ROOM_WORLDMAP | `16` | 월드맵 표시 |

### Exit Flags 매핑

| C 상수 | 값 | UIR `door_flags` 비트 | 의미 |
|--------|----|-----------------------|------|
| EX_ISDOOR | 1 | bit 0 | 문 있음 |
| EX_CLOSED | 2 | bit 1 | 닫힘 |
| EX_LOCKED | 4 | bit 2 | 잠김 |
| EX_PICKPROOF | 8 | bit 3 | 따기 불가 |
| EX_HIDDEN | 16 | bit 4 | 숨겨짐 |

---

## 2. Item/Object 매핑

### tbaMUD C → UIR → PostgreSQL

| tbaMUD (`struct obj_data`) | UIR (`Item`) | PostgreSQL (`items`) |
|---|---|---|
| `item_number` (obj_rnum) | `vnum` | `vnum INTEGER PK` |
| `name` (char*) | `keywords` | `keywords TEXT` |
| `short_description` (char*) | `short_description` | `short_description TEXT` |
| `description` (char*) | `long_description` | `long_description TEXT` |
| `action_description` (char*) | `action_description` | - (생략) |
| `obj_flags.type_flag` (byte) | `item_type` | `item_type INTEGER` |
| `obj_flags.extra_flags[4]` | `extra_flags: list[int]` | `extra_flags JSONB` |
| `obj_flags.wear_flags[4]` | `wear_flags: list[int]` | `wear_flags JSONB` |
| `obj_flags.value[4]` (int[]) | `values: list[int]` | `values JSONB` |
| `obj_flags.weight` (int) | `weight` | `weight INTEGER` |
| `obj_flags.cost` (int) | `cost` | `cost INTEGER` |
| `obj_flags.cost_per_day` (int) | `rent` | `rent INTEGER` |
| `obj_flags.timer` (int) | `timer` | - (생략) |
| `affected[6]` (struct[]) | `affects: list[ItemAffect]` | `affects JSONB` |
| `ex_description` (linked list) | `extra_descriptions` | `extra_descs JSONB` |

### 128-bit 형식의 파일 → UIR 필드 매핑

파일에서 13 필드 라인:
```
type ef0 ef1 ef2 ef3 wf0 wf1 wf2 wf3 af0 af1 af2 af3
```

| 파일 인덱스 | C 필드 | UIR 필드 |
|-------------|--------|----------|
| [0] | `type_flag` | `item_type` |
| [1] | `extra_flags[0]` | `extra_flags` (asciiflag→int→bit list) |
| [2] | `extra_flags[1]` | (미사용, 항상 0) |
| [3] | `extra_flags[2]` | (미사용) |
| [4] | `extra_flags[3]` | (미사용) |
| **[5]** | **`wear_flags[0]`** | **`wear_flags`** (핵심!) |
| [6] | `wear_flags[1]` | (미사용) |
| [7] | `wear_flags[2]` | (미사용) |
| [8] | `wear_flags[3]` | (미사용) |
| [9] | `bitvector[0]` | (affect bitvector, 미사용) |
| [10] | `bitvector[1]` | (미사용) |
| [11] | `bitvector[2]` | (미사용) |
| [12] | `bitvector[3]` | (미사용) |

### Item Type별 Values 해석

| item_type | 이름 | v0 | v1 | v2 | v3 |
|-----------|------|----|----|----|----|
| 1 | LIGHT | - | - | hours(-1=무한) | - |
| 2 | SCROLL | spell_level | spell1 | spell2 | spell3 |
| 3 | WAND | spell_level | max_charges | cur_charges | spell |
| 4 | STAFF | spell_level | max_charges | cur_charges | spell |
| 5 | WEAPON | - | dice_num | dice_size | attack_type |
| 6 | FURNITURE | max_people | - | - | - |
| 9 | ARMOR | ac_apply | - | - | - |
| 10 | POTION | spell_level | spell1 | spell2 | spell3 |
| 15 | CONTAINER | capacity | cont_flags | key_vnum | - |
| 17 | DRINKCON | capacity | current | liquid_type | poisoned |
| 19 | FOOD | hours_fill | - | - | poisoned |
| 20 | MONEY | gold_amount | - | - | - |
| 23 | FOUNTAIN | capacity | current | liquid_type | poisoned |

---

## 3. Monster/Mobile 매핑

### tbaMUD C → UIR → PostgreSQL

| tbaMUD (`struct char_data`) | UIR (`Monster`) | PostgreSQL (`monsters`) |
|---|---|---|
| NPC `nr` | `vnum` | `vnum INTEGER PK` |
| `player.name` | `keywords` | `keywords TEXT` |
| `player.short_descr` | `short_description` | `short_description TEXT` |
| `player.long_descr` | `long_description` | `long_description TEXT` |
| `player.description` | `detailed_description` | `detailed_description TEXT` |
| `char_specials.saved.act[4]` | `action_flags` | `action_flags JSONB` |
| `char_specials.saved.affected_by[4]` | `affect_flags` | `affect_flags JSONB` |
| `char_specials.saved.alignment` | `alignment` | `alignment INTEGER` |
| `player.level` | `level` | `level INTEGER` |
| `points.hitroll` | `hitroll` | `hitroll INTEGER` |
| `points.armor` | `armor_class` | `armor_class INTEGER` |
| (dice from file) | `hp_dice: DiceRoll` | `hp_dice TEXT` ("6d6+340") |
| `mob_specials.damnodice/damsizedice` | `damage_dice: DiceRoll` | `damage_dice TEXT` |
| `points.gold` | `gold` | `gold INTEGER` |
| (calculated) | `experience` | `experience INTEGER` |
| `char_specials.position` | `load_position` | - |
| `mob_specials.default_pos` | `default_position` | - |
| `player.sex` | `sex` | `sex INTEGER` |
| `mob_specials.attack_type` | `bare_hand_attack` | - |

### 파일 형식 → UIR 필드

```
# Enhanced 포맷 (E)
<action_flags> <affect_flags> <alignment> [...] E     → flags + mob_type
<level> <hitroll> <ac> <NdS+B(hp)> <NdS+B(dam)>     → stats
<gold> <exp>                                          → economy
<load_pos> <default_pos> <sex>                        → state
[BareHandAttack: <type>]                              → combat
E                                                     → end marker
[T <vnum>]...                                         → triggers
```

---

## 4. Zone 매핑

### tbaMUD → UIR → PostgreSQL

| tbaMUD (zone file) | UIR (`Zone`) | PostgreSQL (`zones`) |
|---|---|---|
| `#<vnum>` | `vnum` | `vnum INTEGER PK` |
| builder name~ | `builders` | `builders TEXT` |
| zone name~ | `name` | `name TEXT` |
| params line[0] | `bot` | `bot INTEGER` |
| params line[1] | `top` | `top INTEGER` |
| params line[2] | `lifespan` | `lifespan INTEGER` |
| params line[3] | `reset_mode` | `reset_mode INTEGER` |
| params line[4] | `zone_flags` | `zone_flags JSONB` |
| params line[8] | `min_level` | - |
| params line[9] | `max_level` | - |
| reset commands | `reset_commands` | `reset_commands JSONB` |

---

## 5. Shop 매핑

### tbaMUD → UIR → PostgreSQL

| tbaMUD (shop file) | UIR (`Shop`) | PostgreSQL (`shops`) |
|---|---|---|
| `#<vnum>~` | `vnum` | `vnum INTEGER PK` |
| item vnums until -1 | `selling_items` | `selling_items JSONB` |
| profit_buy | `profit_buy` | `profit_buy REAL` |
| profit_sell | `profit_sell` | `profit_sell REAL` |
| type list until -1 | `accepting_types` | - |
| 7 messages | `no_such_item1`, etc. | - |
| temper | `temper` | - |
| bitvector | `bitvector` | - |
| keeper | `keeper_vnum` | `keeper_vnum INTEGER` |
| room | `shop_room` | `shop_room INTEGER` |
| hours | `open1/close1/open2/close2` | `open1/close1/open2/close2` |

---

## 6. Trigger 매핑

### tbaMUD → UIR → PostgreSQL + Lua

| tbaMUD (trg file) | UIR (`Trigger`) | PostgreSQL | Lua |
|---|---|---|---|
| `#<vnum>` | `vnum` | `vnum PK` | `Triggers[vnum]` |
| name~ | `name` | `name TEXT` | `.name` |
| attach_type | `attach_type` | `attach_type INT` | `.attach_type` |
| trigger_type | `trigger_type` | `trigger_type INT` | `.trigger_type` |
| numeric_arg | `numeric_arg` | `numeric_arg INT` | `.numeric_arg` |
| arg_list~ | `arg_list` | `arg_list TEXT` | - |
| script~ | `script` | `script TEXT` | `.execute()` 함수 |

DG Script → Lua 변환 매핑:

| DG Script | Lua |
|-----------|-----|
| `* comment` | `-- comment` |
| `if %cond%` | `if cond then` |
| `elseif %cond%` | `elseif cond then` |
| `else` | `else` |
| `end` | `end` |
| `say <msg>` | `self:say("<msg>")` |
| `emote <msg>` | `self:emote("<msg>")` |
| `wait N sec` | `coroutine.yield(N)` |
| `return 0` | `return 0` |
| `&&` | `and` |
| `\|\|` | `or` |
| `!=` | `~=` |
| `%var.prop%` | `var_prop` |

---

## 7. Class 매핑 (하드코딩)

tbaMUD의 클래스 정보는 파일이 아닌 소스 코드에 하드코딩되어 있으므로, 수동으로 UIR에 매핑합니다.

| class_id | 이름 | 약자 | THAC0 기본/감소율 | HP 증가 | Mana 증가 |
|----------|------|------|-------------------|---------|-----------|
| 0 | Magic User | Mu | 20 / 0.66 | 3-8 | 5-10 |
| 1 | Cleric | Cl | 20 / 0.66 | 5-10 | 3-8 |
| 2 | Thief | Th | 20 / 0.75 | 6-11 | 0-0 |
| 3 | Warrior | Wa | 20 / 1.00 | 10-15 | 0-0 |

소스 참조: `src/class.c`의 `thaco()`, `src/constants.c`

---

## 8. 정수 값 해석 참조표

### Sector Type → 이름

```
0=inside  1=city    2=field     3=forest   4=hills
5=mountain 6=water_swim 7=water_noswim 8=flying 9=underwater
```

### Position → 이름

```
0=dead  1=mortally_wounded  2=incapacitated  3=stunned
4=sleeping  5=resting  6=sitting  7=fighting  8=standing
```

### Sex → 이름

```
0=neutral  1=male  2=female
```

### Attack Type → 이름

```
0=hit  1=sting  2=whip  3=slash  4=bite  5=bludgeon
6=crush  7=pound  8=claw  9=maul  10=thrash  11=pierce
12=blast  13=punch  14=stab
```

### Apply Type → 이름

```
0=none  1=str  2=dex  3=int  4=wis  5=con  6=cha
12=mana  13=hit  14=move  17=ac  18=hitroll  19=damroll
20-24=saving throws
```

### Liquid Type → 이름

```
0=water  1=beer  2=wine  3=ale  4=dark_ale  5=whisky
6=lemonade  7=firebreather  8=local_special  9=slime
10=milk  11=tea  12=coffee  13=blood  14=salt_water  15=clear_water
```

---

## 9. Social 매핑 (Phase 2)

### lib/misc/socials → UIR → PostgreSQL

| 소스 (socials 파일) | UIR (`Social`) | PostgreSQL (`socials`) |
|---|---|---|
| command word | `command` | `command TEXT PK` |
| min_victim_position | `min_victim_position` | `min_victim_position INTEGER` |
| flags | `flags` | `flags INTEGER` |
| line 1 | `no_arg_to_char` | `no_arg_to_char TEXT` |
| line 2 | `no_arg_to_room` | `no_arg_to_room TEXT` |
| line 3 | `found_to_char` | `found_to_char TEXT` |
| line 4 | `found_to_room` | `found_to_room TEXT` |
| line 5 | `found_to_victim` | `found_to_victim TEXT` |
| line 6 | `not_found` | `not_found TEXT` |
| line 7 | `self_to_char` | `self_to_char TEXT` |
| line 8 | `self_to_room` | `self_to_room TEXT` |

메시지 줄에서 `#`은 빈 문자열로 변환됩니다.

---

## 10. Help 매핑 (Phase 2)

### lib/text/help/*.hlp → UIR → PostgreSQL

| 소스 (hlp 파일) | UIR (`HelpEntry`) | PostgreSQL (`help_entries`) |
|---|---|---|
| keyword line | `keywords: list[str]` | `keywords JSONB` |
| `#<level>` terminator | `min_level` | `min_level INTEGER` |
| body text | `text` | `text TEXT` |

- `id`는 PostgreSQL에서 `SERIAL`로 자동 생성 (소스에는 ID 없음)
- 키워드는 공백 구분 → 리스트로 분할

---

## 11. Command 매핑 (Phase 2)

### src/interpreter.c cmd_info[] → UIR → PostgreSQL

| 소스 (C 배열) | UIR (`Command`) | PostgreSQL (`commands`) |
|---|---|---|
| `"name"` | `name` | `name TEXT PK` |
| `"min_match"` | `min_match` | `min_match TEXT` |
| `POS_*` | `min_position` | `min_position INTEGER` |
| `do_*` | `handler` | `handler TEXT` |
| level int/`LVL_*` | `min_level` | `min_level INTEGER` |
| `SCMD_*` | `subcmd` | `subcmd INTEGER` |
| (추론) | `category` | `category TEXT` |

**category 추론 규칙**:
- `do_move` → "movement"
- `do_gen_comm` → "communication"
- `do_action` → "social"
- 기타 → "" (빈 문자열)

**Simoon 차이**: `min_match` 필드 없음 → 빈 문자열

---

## 12. Skill 매핑 (Phase 2)

### src/spells.h + spell_parser.c + class.c → UIR → PostgreSQL

| 소스 | UIR (`Skill`) | PostgreSQL (`skills`) |
|---|---|---|
| `#define SPELL_*` (spells.h) | `id` | `id INTEGER PK` |
| spello arg / constant name | `name` | `name TEXT` |
| SPELL_*/SKILL_* prefix | `spell_type` ("spell"/"skill") | `spell_type TEXT` |
| spello max_mana | `max_mana` | `max_mana INTEGER` |
| spello min_mana | `min_mana` | `min_mana INTEGER` |
| spello mana_change | `mana_change` | `mana_change INTEGER` |
| spello POS_* | `min_position` | `min_position INTEGER` |
| spello TAR_* | `targets` | `targets INTEGER` |
| spello TRUE/FALSE | `violent` | `violent BOOLEAN` |
| spello MAG_* | `routines` | `routines INTEGER` |
| spello wearoff msg | `wearoff_msg` | `wearoff_msg TEXT` |
| spell_level() (class.c) | `class_levels: dict` | `class_levels JSONB` |
| han_spells[] (Simoon) | `extensions["korean_name"]` | `extensions JSONB` |

---

## 13. Race 매핑 (Phase 2, Simoon 전용)

### 소스 코드 하드코딩 → UIR → PostgreSQL

| 소스 | UIR (`Race`) | PostgreSQL (`races`) |
|---|---|---|
| structs.h 정의 | `id` | `id INTEGER PK` |
| 이름 문자열 | `name` | `name TEXT` |
| 약어 | `abbreviation` | `abbreviation TEXT` |
| class.c 스탯 보정 | `stat_modifiers` | `stat_modifiers JSONB` |
| class.c 클래스 제한 | `allowed_classes` | `allowed_classes JSONB` |
| 확장 데이터 | `extensions` | `extensions JSONB` |

**Simoon 종족 (5개)**:

| id | name | abbreviation | 스탯 보정 |
|----|------|--------------|-----------|
| 0 | 인간 (Human) | Hu | 없음 |
| 1 | 드워프 (Dwarf) | Dw | str+1, con+1, dex-1 |
| 2 | 엘프 (Elf) | El | int+1, dex+1, con-1 |
| 3 | 호빗 (Hobbit) | Ho | dex+2, str-1, con-1 |
| 4 | 하프엘프 (Half-Elf) | HE | int+1, cha+1, str-1 |

tbaMUD에는 종족 시스템이 없으므로 races 테이블은 비어 있습니다.
