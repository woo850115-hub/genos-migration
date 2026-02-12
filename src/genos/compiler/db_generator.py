"""UIR → PostgreSQL DDL + seed data generator (GenOS Unified Schema v1.0).

20+2 tables: Proto (immutable templates) + Instance (runtime mutable).
Design principles:
  - Proto/Instance separation
  - Regular columns + JSONB hybrid
  - Bitfield → TEXT[] tags with GIN index
  - Stats as JSONB (5~18 dynamic)
  - Graph model exits (room_exits table)
  - Dynamic equipment slots (TEXT[] wear_slots)
"""

from __future__ import annotations

import json
import math
from typing import Any, TextIO

from genos.uir.schema import UIR


# ── DDL ──────────────────────────────────────────────────────────────

_DDL = """\
-- GenOS Unified Database Schema v1.0
-- Auto-generated from UIR

BEGIN;

-- ── Proto Tables (immutable templates, migration tool generates) ──

CREATE TABLE IF NOT EXISTS rooms (
    vnum        INTEGER PRIMARY KEY,
    zone_vnum   INTEGER NOT NULL DEFAULT 0,
    name        TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    sector      INTEGER NOT NULL DEFAULT 0,
    flags       TEXT[] NOT NULL DEFAULT '{}',
    extra_descs JSONB NOT NULL DEFAULT '[]',
    scripts     JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_rooms_zone ON rooms (zone_vnum);
CREATE INDEX IF NOT EXISTS idx_rooms_flags ON rooms USING GIN (flags);

CREATE TABLE IF NOT EXISTS room_exits (
    from_vnum   INTEGER NOT NULL REFERENCES rooms(vnum),
    direction   SMALLINT NOT NULL,
    to_vnum     INTEGER NOT NULL DEFAULT -1,
    description TEXT NOT NULL DEFAULT '',
    keywords    TEXT NOT NULL DEFAULT '',
    key_vnum    INTEGER NOT NULL DEFAULT -1,
    flags       TEXT[] NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (from_vnum, direction)
);
CREATE INDEX IF NOT EXISTS idx_exits_to ON room_exits (to_vnum);

CREATE TABLE IF NOT EXISTS mob_protos (
    vnum        INTEGER PRIMARY KEY,
    zone_vnum   INTEGER NOT NULL DEFAULT 0,
    keywords    TEXT NOT NULL DEFAULT '',
    short_desc  TEXT NOT NULL DEFAULT '',
    long_desc   TEXT NOT NULL DEFAULT '',
    detail_desc TEXT NOT NULL DEFAULT '',
    level       INTEGER NOT NULL DEFAULT 1,
    max_hp      INTEGER NOT NULL DEFAULT 1,
    max_mana    INTEGER NOT NULL DEFAULT 0,
    max_move    INTEGER NOT NULL DEFAULT 0,
    armor_class INTEGER NOT NULL DEFAULT 100,
    hitroll     INTEGER NOT NULL DEFAULT 0,
    damroll     INTEGER NOT NULL DEFAULT 0,
    damage_dice TEXT NOT NULL DEFAULT '1d4+0',
    gold        INTEGER NOT NULL DEFAULT 0,
    experience  BIGINT NOT NULL DEFAULT 0,
    alignment   INTEGER NOT NULL DEFAULT 0,
    sex         SMALLINT NOT NULL DEFAULT 0,
    position    SMALLINT NOT NULL DEFAULT 8,
    class_id    INTEGER NOT NULL DEFAULT 0,
    race_id     INTEGER NOT NULL DEFAULT 0,
    act_flags   TEXT[] NOT NULL DEFAULT '{}',
    aff_flags   TEXT[] NOT NULL DEFAULT '{}',
    stats       JSONB NOT NULL DEFAULT '{}',
    skills      JSONB NOT NULL DEFAULT '{}',
    scripts     JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_mobs_zone ON mob_protos (zone_vnum);
CREATE INDEX IF NOT EXISTS idx_mobs_level ON mob_protos (level);
CREATE INDEX IF NOT EXISTS idx_mobs_act ON mob_protos USING GIN (act_flags);

CREATE TABLE IF NOT EXISTS item_protos (
    vnum        INTEGER PRIMARY KEY,
    zone_vnum   INTEGER NOT NULL DEFAULT 0,
    keywords    TEXT NOT NULL DEFAULT '',
    short_desc  TEXT NOT NULL DEFAULT '',
    long_desc   TEXT NOT NULL DEFAULT '',
    item_type   TEXT NOT NULL DEFAULT 'other',
    weight      INTEGER NOT NULL DEFAULT 0,
    cost        INTEGER NOT NULL DEFAULT 0,
    min_level   INTEGER NOT NULL DEFAULT 0,
    wear_slots  TEXT[] NOT NULL DEFAULT '{}',
    flags       TEXT[] NOT NULL DEFAULT '{}',
    values      JSONB NOT NULL DEFAULT '{}',
    affects     JSONB NOT NULL DEFAULT '[]',
    extra_descs JSONB NOT NULL DEFAULT '[]',
    scripts     JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_items_zone ON item_protos (zone_vnum);
CREATE INDEX IF NOT EXISTS idx_items_type ON item_protos (item_type);
CREATE INDEX IF NOT EXISTS idx_items_flags ON item_protos USING GIN (flags);
CREATE INDEX IF NOT EXISTS idx_items_wear ON item_protos USING GIN (wear_slots);

CREATE TABLE IF NOT EXISTS zones (
    vnum        INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    builders    TEXT NOT NULL DEFAULT '',
    lifespan    INTEGER NOT NULL DEFAULT 30,
    reset_mode  SMALLINT NOT NULL DEFAULT 2,
    level_range INT4RANGE,
    flags       TEXT[] NOT NULL DEFAULT '{}',
    resets      JSONB NOT NULL DEFAULT '[]',
    ext         JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS skills (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    skill_type  TEXT NOT NULL DEFAULT 'spell',
    mana_cost   INTEGER NOT NULL DEFAULT 0,
    target      TEXT NOT NULL DEFAULT 'ignore',
    violent     BOOLEAN NOT NULL DEFAULT false,
    min_position SMALLINT NOT NULL DEFAULT 0,
    routines    TEXT[] NOT NULL DEFAULT '{}',
    wearoff_msg TEXT NOT NULL DEFAULT '',
    class_levels JSONB NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS classes (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    abbrev      TEXT NOT NULL DEFAULT '',
    hp_gain     INT4RANGE NOT NULL DEFAULT '[1,10)',
    mana_gain   INT4RANGE NOT NULL DEFAULT '[0,0)',
    move_gain   INT4RANGE NOT NULL DEFAULT '[0,0)',
    base_stats  JSONB NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS races (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    abbrev      TEXT NOT NULL DEFAULT '',
    stat_mods   JSONB NOT NULL DEFAULT '{}',
    body_parts  TEXT[] NOT NULL DEFAULT '{}',
    size        TEXT NOT NULL DEFAULT 'medium',
    ext         JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS shops (
    vnum          INTEGER PRIMARY KEY,
    keeper_vnum   INTEGER NOT NULL,
    room_vnum     INTEGER NOT NULL DEFAULT 0,
    buy_types     TEXT[] NOT NULL DEFAULT '{}',
    buy_profit    REAL NOT NULL DEFAULT 1.1,
    sell_profit   REAL NOT NULL DEFAULT 0.9,
    hours         JSONB NOT NULL DEFAULT '{}',
    inventory     JSONB NOT NULL DEFAULT '[]',
    messages      JSONB NOT NULL DEFAULT '{}',
    ext           JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS quests (
    vnum        INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    quest_type  TEXT NOT NULL DEFAULT 'kill',
    level_range INT4RANGE,
    giver_vnum  INTEGER NOT NULL DEFAULT 0,
    target      JSONB NOT NULL DEFAULT '{}',
    rewards     JSONB NOT NULL DEFAULT '{}',
    chain       JSONB NOT NULL DEFAULT '{}',
    flags       TEXT[] NOT NULL DEFAULT '{}',
    ext         JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS socials (
    command     TEXT PRIMARY KEY,
    min_victim_position SMALLINT NOT NULL DEFAULT 0,
    messages    JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS help_entries (
    id          SERIAL PRIMARY KEY,
    keywords    TEXT[] NOT NULL DEFAULT '{}',
    category    TEXT NOT NULL DEFAULT 'general',
    min_level   INTEGER NOT NULL DEFAULT 0,
    body        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_help_keywords ON help_entries USING GIN (keywords);

CREATE TABLE IF NOT EXISTS combat_messages (
    id          SERIAL PRIMARY KEY,
    skill_id    INTEGER NOT NULL,
    hit_type    TEXT NOT NULL,
    to_char     TEXT NOT NULL DEFAULT '',
    to_victim   TEXT NOT NULL DEFAULT '',
    to_room     TEXT NOT NULL DEFAULT '',
    ext         JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_cmsg_skill ON combat_messages (skill_id);

CREATE TABLE IF NOT EXISTS text_files (
    name        TEXT PRIMARY KEY,
    category    TEXT NOT NULL DEFAULT 'system',
    content     TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS game_tables (
    table_name  TEXT NOT NULL,
    key         JSONB NOT NULL,
    value       JSONB NOT NULL,
    PRIMARY KEY (table_name, key)
);
CREATE INDEX IF NOT EXISTS idx_gtables_name ON game_tables (table_name);

CREATE TABLE IF NOT EXISTS game_configs (
    key         TEXT PRIMARY KEY,
    value       JSONB NOT NULL,
    category    TEXT NOT NULL DEFAULT 'general',
    description TEXT NOT NULL DEFAULT ''
);

-- ── Instance Tables (runtime mutable, engine manages) ──

CREATE TABLE IF NOT EXISTS players (
    id            SERIAL PRIMARY KEY,
    name          TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL DEFAULT '',
    class_id      INTEGER NOT NULL DEFAULT 0,
    race_id       INTEGER NOT NULL DEFAULT 0,
    sex           SMALLINT NOT NULL DEFAULT 0,
    level         INTEGER NOT NULL DEFAULT 1,
    experience    BIGINT NOT NULL DEFAULT 0,
    hp            INTEGER NOT NULL DEFAULT 100,
    max_hp        INTEGER NOT NULL DEFAULT 100,
    mana          INTEGER NOT NULL DEFAULT 100,
    max_mana      INTEGER NOT NULL DEFAULT 100,
    move          INTEGER NOT NULL DEFAULT 100,
    max_move      INTEGER NOT NULL DEFAULT 100,
    gold          INTEGER NOT NULL DEFAULT 0,
    bank_gold     INTEGER NOT NULL DEFAULT 0,
    armor_class   INTEGER NOT NULL DEFAULT 100,
    alignment     INTEGER NOT NULL DEFAULT 0,
    stats         JSONB NOT NULL DEFAULT '{}',
    equipment     JSONB NOT NULL DEFAULT '{}',
    inventory     JSONB NOT NULL DEFAULT '[]',
    affects       JSONB NOT NULL DEFAULT '[]',
    skills        JSONB NOT NULL DEFAULT '{}',
    flags         TEXT[] NOT NULL DEFAULT '{}',
    aliases       JSONB NOT NULL DEFAULT '{}',
    title         TEXT NOT NULL DEFAULT '',
    description   TEXT NOT NULL DEFAULT '',
    room_vnum     INTEGER NOT NULL DEFAULT 0,
    org_id        INTEGER NOT NULL DEFAULT 0,
    org_rank      INTEGER NOT NULL DEFAULT 0,
    ext           JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_players_name ON players (name);
CREATE INDEX IF NOT EXISTS idx_players_level ON players (level);

CREATE TABLE IF NOT EXISTS organizations (
    id          SERIAL PRIMARY KEY,
    org_type    TEXT NOT NULL DEFAULT 'clan',
    name        TEXT NOT NULL DEFAULT '',
    leader      TEXT NOT NULL DEFAULT '',
    treasury    INTEGER NOT NULL DEFAULT 0,
    room_vnum   INTEGER NOT NULL DEFAULT 0,
    ext         JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS lua_scripts (
    id          SERIAL PRIMARY KEY,
    game        TEXT NOT NULL DEFAULT '',
    category    TEXT NOT NULL DEFAULT '',
    name        TEXT NOT NULL DEFAULT '',
    source      TEXT NOT NULL DEFAULT '',
    version     INTEGER NOT NULL DEFAULT 1,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (game, category, name)
);

COMMIT;
"""


def generate_ddl(uir: UIR, out: TextIO) -> None:
    """Write PostgreSQL CREATE TABLE statements (20 tables)."""
    out.write(_DDL)


# ── Seed data ────────────────────────────────────────────────────────

def generate_seed_data(uir: UIR, out: TextIO) -> None:
    """Write INSERT statements for seed data."""
    out.write("-- GenOS Seed Data (Unified Schema v1.0)\n")
    out.write("-- Auto-generated from UIR\n\n")
    out.write("BEGIN;\n\n")

    _seed_rooms(uir, out)
    _seed_room_exits(uir, out)
    _seed_mob_protos(uir, out)
    _seed_item_protos(uir, out)
    _seed_zones(uir, out)
    _seed_skills(uir, out)
    _seed_classes(uir, out)
    _seed_races(uir, out)
    _seed_shops(uir, out)
    _seed_quests(uir, out)
    _seed_socials(uir, out)
    _seed_help_entries(uir, out)
    _seed_game_tables(uir, out)
    _seed_game_configs(uir, out)

    out.write("\nCOMMIT;\n")


# ── Individual seed generators ───────────────────────────────────────

def _seed_rooms(uir: UIR, out: TextIO) -> None:
    for r in uir.rooms:
        flags = _int_flags_to_tags(r.room_flags, _ROOM_FLAG_NAMES)
        extra_json = json.dumps([
            {"keywords": ed.keywords, "description": ed.description}
            for ed in r.extra_descriptions
        ], ensure_ascii=False)
        scripts_json = json.dumps(r.trigger_vnums)
        ext = json.dumps(r.extensions, ensure_ascii=False) if r.extensions else '{}'
        out.write(
            f"INSERT INTO rooms (vnum, zone_vnum, name, description, sector, "
            f"flags, extra_descs, scripts, ext) VALUES "
            f"({r.vnum}, {r.zone_number}, {_sql(r.name)}, {_sql(r.description)}, "
            f"{r.sector_type}, {_sql_arr(flags)}, "
            f"{_sql(extra_json)}, {_sql(scripts_json)}, {_sql(ext)});\n"
        )
    if uir.rooms:
        out.write("\n")


def _seed_room_exits(uir: UIR, out: TextIO) -> None:
    for r in uir.rooms:
        for e in r.exits:
            flags = _exit_flags_to_tags(e.door_flags)
            out.write(
                f"INSERT INTO room_exits (from_vnum, direction, to_vnum, "
                f"description, keywords, key_vnum, flags) VALUES "
                f"({r.vnum}, {e.direction}, {e.destination}, "
                f"{_sql(e.description)}, {_sql(e.keyword)}, "
                f"{e.key_vnum}, {_sql_arr(flags)});\n"
            )
    has_exits = any(r.exits for r in uir.rooms)
    if has_exits:
        out.write("\n")


def _seed_mob_protos(uir: UIR, out: TextIO) -> None:
    for m in uir.monsters:
        act_flags = _int_flags_to_tags(m.action_flags, _MOB_ACT_FLAG_NAMES)
        aff_flags = _int_flags_to_tags(m.affect_flags, _AFF_FLAG_NAMES)
        max_hp = _dice_median(m.hp_dice)
        ext = dict(m.extensions) if m.extensions else {}
        # Preserve original dice in ext
        hp_dice_str = str(m.hp_dice)
        if hp_dice_str != "0d0+0":
            ext["hp_dice"] = hp_dice_str
        stats_json = json.dumps(ext.pop("stats", {}), ensure_ascii=False) if "stats" in ext else '{}'
        skills_json = json.dumps(ext.pop("skills", {}), ensure_ascii=False) if "skills" in ext else '{}'
        scripts_json = json.dumps(m.trigger_vnums)
        ext_json = json.dumps(ext, ensure_ascii=False) if ext else '{}'
        out.write(
            f"INSERT INTO mob_protos (vnum, zone_vnum, keywords, short_desc, "
            f"long_desc, detail_desc, level, max_hp, armor_class, hitroll, damroll, "
            f"damage_dice, gold, experience, alignment, sex, position, "
            f"act_flags, aff_flags, stats, skills, scripts, ext) VALUES "
            f"({m.vnum}, {m.vnum // 100}, {_sql(m.keywords)}, "
            f"{_sql(m.short_description)}, {_sql(m.long_description)}, "
            f"{_sql(m.detailed_description)}, {m.level}, {max_hp}, "
            f"{m.armor_class}, {m.hitroll}, 0, "
            f"{_sql(str(m.damage_dice))}, {m.gold}, {m.experience}, "
            f"{m.alignment}, {m.sex}, {m.default_position}, "
            f"{_sql_arr(act_flags)}, {_sql_arr(aff_flags)}, "
            f"{_sql(stats_json)}, {_sql(skills_json)}, "
            f"{_sql(scripts_json)}, {_sql(ext_json)});\n"
        )
    if uir.monsters:
        out.write("\n")


def _seed_item_protos(uir: UIR, out: TextIO) -> None:
    for item in uir.items:
        item_type = _ITEM_TYPE_NAMES.get(item.item_type, "other")
        wear_slots = _wear_flags_to_slots(item.wear_flags)
        flags = _int_flags_to_tags(item.extra_flags, _ITEM_FLAG_NAMES)
        values = _item_values_to_json(item.item_type, item.values)
        affects_json = json.dumps([
            {"stat": _APPLY_NAMES.get(a.location, str(a.location)), "mod": a.modifier}
            for a in item.affects
        ], ensure_ascii=False)
        extra_json = json.dumps([
            {"keywords": ed.keywords, "description": ed.description}
            for ed in item.extra_descriptions
        ], ensure_ascii=False)
        scripts_json = json.dumps(item.trigger_vnums)
        ext_json = '{}'
        out.write(
            f"INSERT INTO item_protos (vnum, zone_vnum, keywords, short_desc, "
            f"long_desc, item_type, weight, cost, min_level, "
            f"wear_slots, flags, values, affects, extra_descs, scripts, ext) VALUES "
            f"({item.vnum}, {item.vnum // 100}, {_sql(item.keywords)}, "
            f"{_sql(item.short_description)}, {_sql(item.long_description)}, "
            f"{_sql(item_type)}, {item.weight}, {item.cost}, {item.min_level}, "
            f"{_sql_arr(wear_slots)}, {_sql_arr(flags)}, "
            f"{_sql(values)}, {_sql(affects_json)}, {_sql(extra_json)}, "
            f"{_sql(scripts_json)}, {_sql(ext_json)});\n"
        )
    if uir.items:
        out.write("\n")


def _seed_zones(uir: UIR, out: TextIO) -> None:
    for z in uir.zones:
        flags = _int_flags_to_tags(z.zone_flags, {})
        resets_json = json.dumps([
            {"command": c.command, "if_flag": c.if_flag,
             "arg1": c.arg1, "arg2": c.arg2, "arg3": c.arg3, "arg4": c.arg4}
            for c in z.reset_commands
        ])
        lvl_range = "NULL"
        if z.min_level >= 0 and z.max_level >= 0:
            lvl_range = f"'[{z.min_level},{z.max_level + 1})'"
        out.write(
            f"INSERT INTO zones (vnum, name, builders, lifespan, reset_mode, "
            f"level_range, flags, resets) VALUES "
            f"({z.vnum}, {_sql(z.name)}, {_sql(z.builders)}, {z.lifespan}, "
            f"{z.reset_mode}, {lvl_range}, {_sql_arr(flags)}, "
            f"{_sql(resets_json)});\n"
        )
    if uir.zones:
        out.write("\n")


def _seed_skills(uir: UIR, out: TextIO) -> None:
    for sk in uir.skills:
        skill_type = sk.spell_type if sk.spell_type else "spell"
        routines_tags = _int_to_routine_tags(sk.routines)
        target_name = _TARGET_NAMES.get(sk.targets, "ignore")
        class_levels_json = json.dumps(
            {str(k): v for k, v in sk.class_levels.items()},
            ensure_ascii=False,
        )
        ext = dict(sk.extensions) if sk.extensions else {}
        # Move old fields to ext
        if sk.max_mana:
            ext["max_mana"] = sk.max_mana
        if sk.mana_change:
            ext["mana_change"] = sk.mana_change
        ext_json = json.dumps(ext, ensure_ascii=False) if ext else '{}'
        out.write(
            f"INSERT INTO skills (id, name, skill_type, mana_cost, target, "
            f"violent, min_position, routines, wearoff_msg, class_levels, ext) VALUES "
            f"({sk.id}, {_sql(sk.name)}, {_sql(skill_type)}, "
            f"{sk.min_mana}, {_sql(target_name)}, "
            f"{str(sk.violent).upper()}, {sk.min_position}, "
            f"{_sql_arr(routines_tags)}, {_sql(sk.wearoff_msg)}, "
            f"{_sql(class_levels_json)}, {_sql(ext_json)});\n"
        )
    if uir.skills:
        out.write("\n")


def _seed_classes(uir: UIR, out: TextIO) -> None:
    for c in uir.character_classes:
        hp_range = f"'[{c.hp_gain_min},{c.hp_gain_max + 1})'"
        mana_range = f"'[{c.mana_gain_min},{c.mana_gain_max + 1})'"
        move_range = f"'[{c.move_gain_min},{c.move_gain_max + 1})'"
        ext = dict(c.extensions) if c.extensions else {}
        base_stats = json.dumps(ext.pop("base_stats", {}), ensure_ascii=False) if "base_stats" in ext else '{}'
        ext_json = json.dumps(ext, ensure_ascii=False) if ext else '{}'
        out.write(
            f"INSERT INTO classes (id, name, abbrev, hp_gain, mana_gain, "
            f"move_gain, base_stats, ext) VALUES "
            f"({c.id}, {_sql(c.name)}, {_sql(c.abbreviation)}, "
            f"{hp_range}, {mana_range}, {move_range}, "
            f"{_sql(base_stats)}, {_sql(ext_json)});\n"
        )
    if uir.character_classes:
        out.write("\n")


def _seed_races(uir: UIR, out: TextIO) -> None:
    for race in uir.races:
        stat_mods = json.dumps(race.stat_modifiers, ensure_ascii=False)
        ext = dict(race.extensions) if race.extensions else {}
        body_parts = ext.pop("body_parts", [])
        size = ext.pop("size", "medium")
        ext_json = json.dumps(ext, ensure_ascii=False) if ext else '{}'
        out.write(
            f"INSERT INTO races (id, name, abbrev, stat_mods, body_parts, "
            f"size, ext) VALUES "
            f"({race.id}, {_sql(race.name)}, {_sql(race.abbreviation)}, "
            f"{_sql(stat_mods)}, {_sql_arr(body_parts)}, {_sql(size)}, "
            f"{_sql(ext_json)});\n"
        )
    if uir.races:
        out.write("\n")


def _seed_shops(uir: UIR, out: TextIO) -> None:
    for s in uir.shops:
        buy_types = [_ITEM_TYPE_NAMES.get(t, str(t)) for t in s.accepting_types]
        hours = json.dumps({
            "open1": s.open1, "close1": s.close1,
            "open2": s.open2, "close2": s.close2,
        })
        inventory = json.dumps([
            {"vnum": v, "quantity": -1} for v in s.selling_items
        ])
        messages = json.dumps({
            k: v for k, v in [
                ("no_such_item1", s.no_such_item1),
                ("no_such_item2", s.no_such_item2),
                ("do_not_buy", s.do_not_buy),
                ("missing_cash1", s.missing_cash1),
                ("missing_cash2", s.missing_cash2),
                ("message_buy", s.message_buy),
                ("message_sell", s.message_sell),
            ] if v
        }, ensure_ascii=False)
        out.write(
            f"INSERT INTO shops (vnum, keeper_vnum, room_vnum, buy_types, "
            f"buy_profit, sell_profit, hours, inventory, messages) VALUES "
            f"({s.vnum}, {s.keeper_vnum}, {s.shop_room}, "
            f"{_sql_arr(buy_types)}, {s.profit_buy}, {s.profit_sell}, "
            f"{_sql(hours)}, {_sql(inventory)}, {_sql(messages)});\n"
        )
    if uir.shops:
        out.write("\n")


def _seed_quests(uir: UIR, out: TextIO) -> None:
    for q in uir.quests:
        target = {}
        if q.target_vnum >= 0:
            target["vnum"] = q.target_vnum
        if q.value0 >= 0:
            target["count"] = q.value0
        rewards = {}
        if q.reward_gold > 0:
            rewards["gold"] = q.reward_gold
        if q.reward_exp > 0:
            rewards["exp"] = q.reward_exp
        if q.reward_obj >= 0:
            rewards["item_vnum"] = q.reward_obj
        chain: dict[str, Any] = {}
        if q.prev_quest >= 0:
            chain["prev"] = q.prev_quest
        if q.next_quest >= 0:
            chain["next"] = q.next_quest
        lvl_range = "NULL"
        if q.min_level > 0 or q.max_level > 0:
            lvl_range = f"'[{q.min_level},{q.max_level + 1})'"
        out.write(
            f"INSERT INTO quests (vnum, name, description, quest_type, "
            f"level_range, giver_vnum, target, rewards, chain) VALUES "
            f"({q.vnum}, {_sql(q.name)}, {_sql(q.description)}, "
            f"{_sql(_QUEST_TYPE_NAMES.get(q.quest_type, 'kill'))}, "
            f"{lvl_range}, {q.mob_vnum}, "
            f"{_sql(json.dumps(target))}, {_sql(json.dumps(rewards))}, "
            f"{_sql(json.dumps(chain))});\n"
        )
    if uir.quests:
        out.write("\n")


def _seed_socials(uir: UIR, out: TextIO) -> None:
    for soc in uir.socials:
        messages: dict[str, Any] = {}
        if soc.no_arg_to_char or soc.no_arg_to_room:
            messages["no_arg"] = {
                "char": soc.no_arg_to_char,
                "room": soc.no_arg_to_room,
            }
        if soc.found_to_char or soc.found_to_room or soc.found_to_victim:
            messages["found"] = {
                "char": soc.found_to_char,
                "victim": soc.found_to_victim,
                "room": soc.found_to_room,
            }
        if soc.not_found:
            messages["not_found"] = soc.not_found
        if soc.self_to_char or soc.self_to_room:
            messages["self"] = {
                "char": soc.self_to_char,
                "room": soc.self_to_room,
            }
        out.write(
            f"INSERT INTO socials (command, min_victim_position, messages) VALUES "
            f"({_sql(soc.command)}, {soc.min_victim_position}, "
            f"{_sql(json.dumps(messages, ensure_ascii=False))});\n"
        )
    if uir.socials:
        out.write("\n")


def _seed_help_entries(uir: UIR, out: TextIO) -> None:
    for h in uir.help_entries:
        out.write(
            f"INSERT INTO help_entries (keywords, min_level, body) VALUES "
            f"({_sql_arr(h.keywords)}, {h.min_level}, {_sql(h.text)});\n"
        )
    if uir.help_entries:
        out.write("\n")


def _seed_game_tables(uir: UIR, out: TextIO) -> None:
    """Merge 6 legacy tables into unified game_tables."""
    # Experience table
    for exp in uir.experience_table:
        key = json.dumps({"class_id": exp.class_id, "level": exp.level})
        out.write(
            f"INSERT INTO game_tables (table_name, key, value) VALUES "
            f"('exp_table', {_sql(key)}, '{exp.exp_required}');\n"
        )
    # THAC0
    for th in uir.thac0_table:
        key = json.dumps({"class_id": th.class_id, "level": th.level})
        out.write(
            f"INSERT INTO game_tables (table_name, key, value) VALUES "
            f"('thac0', {_sql(key)}, '{th.thac0}');\n"
        )
    # Saving throws
    for st in uir.saving_throws:
        key = json.dumps({"class_id": st.class_id, "type": st.save_type, "level": st.level})
        out.write(
            f"INSERT INTO game_tables (table_name, key, value) VALUES "
            f"('saving_throw', {_sql(key)}, '{st.save_value}');\n"
        )
    # Level titles
    for lt in uir.level_titles:
        key = json.dumps({"class_id": lt.class_id, "level": lt.level, "gender": lt.gender})
        out.write(
            f"INSERT INTO game_tables (table_name, key, value) VALUES "
            f"('level_title', {_sql(key)}, {_sql(json.dumps(lt.title))});\n"
        )
    # Attribute modifiers
    for am in uir.attribute_modifiers:
        key = json.dumps({"stat": am.stat_name, "score": am.score})
        value = json.dumps(am.modifiers)
        out.write(
            f"INSERT INTO game_tables (table_name, key, value) VALUES "
            f"('stat_bonus', {_sql(key)}, {_sql(value)});\n"
        )
    # Practice params
    for pp in uir.practice_params:
        key = json.dumps({"class_id": pp.class_id})
        value = json.dumps({
            "learned_level": pp.learned_level,
            "max": pp.max_per_practice,
            "min": pp.min_per_practice,
            "type": pp.prac_type,
        })
        out.write(
            f"INSERT INTO game_tables (table_name, key, value) VALUES "
            f"('practice', {_sql(key)}, {_sql(value)});\n"
        )
    has_any = (uir.experience_table or uir.thac0_table or uir.saving_throws
               or uir.level_titles or uir.attribute_modifiers or uir.practice_params)
    if has_any:
        out.write("\n")


def _seed_game_configs(uir: UIR, out: TextIO) -> None:
    for gc in uir.game_configs:
        # Convert value to JSONB-compatible format
        value_json = _config_value_to_json(gc.value, gc.value_type)
        out.write(
            f"INSERT INTO game_configs (key, value, category, description) VALUES "
            f"({_sql(gc.key)}, {_sql(value_json)}, "
            f"{_sql(gc.category)}, {_sql(gc.description)});\n"
        )
    if uir.game_configs:
        out.write("\n")


# ── Conversion helpers ───────────────────────────────────────────────

def _sql(value: str) -> str:
    """Escape a string for SQL single-quote literals."""
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def _sql_arr(tags: list[str]) -> str:
    """Format a Python list as a PostgreSQL TEXT[] literal."""
    if not tags:
        return "'{}'::TEXT[]"
    inner = ",".join(f'"{t}"' for t in tags)
    return f"'{{{inner}}}'::TEXT[]"


def _dice_median(dice: Any) -> int:
    """Calculate the median value of a DiceRoll (NdS+B) → N*(S+1)/2+B."""
    n = getattr(dice, "num", 0)
    s = getattr(dice, "size", 0)
    b = getattr(dice, "bonus", 0)
    if n <= 0 or s <= 0:
        return max(1, b)
    return max(1, math.ceil(n * (s + 1) / 2) + b)


def _config_value_to_json(value: str, value_type: str) -> str:
    """Convert a config value string to JSONB-compatible string."""
    if value_type == "bool":
        return "true" if value in ("1", "true", "yes") else "false"
    if value_type == "int" or value_type == "room_vnum":
        try:
            return str(int(value))
        except (ValueError, TypeError):
            return json.dumps(value)
    if value_type == "str":
        return json.dumps(value)
    # Default: try number, then string
    try:
        return str(int(value))
    except (ValueError, TypeError):
        return json.dumps(value)


def _int_flags_to_tags(flags: list[int], name_map: dict[int, str]) -> list[str]:
    """Convert a list of integer flag positions to human-readable tag strings."""
    if not flags:
        return []
    tags = []
    for f in flags:
        name = name_map.get(f)
        if name:
            tags.append(name)
        else:
            tags.append(f"flag_{f}")
    return tags


def _exit_flags_to_tags(door_flags: int) -> list[str]:
    """Convert exit door_flags bitmask to tag list."""
    tags = []
    if door_flags & 1:
        tags.append("door")
    if door_flags & 2:
        tags.append("closed")
    if door_flags & 4:
        tags.append("locked")
    if door_flags & 8:
        tags.append("pickproof")
    if door_flags & 16:
        tags.append("hidden")
    return tags


def _int_to_routine_tags(routines: int) -> list[str]:
    """Convert routine bitmask to tag list."""
    tags = []
    for bit, name in _ROUTINE_NAMES.items():
        if routines & bit:
            tags.append(name)
    return tags


def _item_values_to_json(item_type: int, values: list[int]) -> str:
    """Convert item values list to structured JSONB based on item_type."""
    v = values + [0] * (4 - len(values))  # pad to 4
    data: dict[str, Any] = {}

    if item_type == 5:   # WEAPON
        data = {"damage": f"{v[1]}d{v[2]}+0", "weapon_type": v[3]}
    elif item_type == 9:   # ARMOR
        data = {"ac": v[0]}
    elif item_type == 10:  # POTION
        data = {"level": v[0], "spell1": v[1], "spell2": v[2], "spell3": v[3]}
    elif item_type == 2:   # SCROLL
        data = {"level": v[0], "spell1": v[1], "spell2": v[2], "spell3": v[3]}
    elif item_type == 3:   # WAND
        data = {"level": v[0], "max_charges": v[1], "charges": v[2], "spell": v[3]}
    elif item_type == 4:   # STAFF
        data = {"level": v[0], "max_charges": v[1], "charges": v[2], "spell": v[3]}
    elif item_type == 15:  # CONTAINER
        data = {"capacity": v[0], "flags": v[1], "key_vnum": v[2]}
    elif item_type == 13:  # FOOD
        data = {"nutrition": v[0], "poison": bool(v[3])}
    elif item_type == 17:  # DRINKCON
        data = {"capacity": v[0], "current": v[1], "liquid": v[2], "poison": bool(v[3])}
    elif item_type == 18:  # KEY
        data = {}
    elif item_type == 20:  # MONEY
        data = {"amount": v[0]}
    else:
        # Generic: preserve raw values
        data = {"v0": v[0], "v1": v[1], "v2": v[2], "v3": v[3]}

    return json.dumps(data)


# ── Wear flag → slot name mapping ────────────────────────────────────

_WEAR_FLAG_SLOTS: dict[int, str] = {
    0: "take",
    1: "finger",
    2: "neck",
    3: "body",
    4: "head",
    5: "legs",
    6: "feet",
    7: "hands",
    8: "arms",
    9: "shield",
    10: "about",
    11: "waist",
    12: "wrist",
    13: "wield",
    14: "hold",
    15: "float",
}


def _wear_flags_to_slots(wear_flags: list[int]) -> list[str]:
    """Convert wear_flags int list to slot name strings."""
    slots = []
    for f in wear_flags:
        name = _WEAR_FLAG_SLOTS.get(f)
        if name and name != "take":  # skip "take" — it's not a slot
            slots.append(name)
        elif f > 0 and name is None:
            slots.append(f"slot_{f}")
    return slots


# ── Flag name maps ───────────────────────────────────────────────────

_ROOM_FLAG_NAMES: dict[int, str] = {
    0: "dark", 1: "death", 2: "no_mob", 3: "indoors",
    4: "peaceful", 5: "soundproof", 6: "no_track", 7: "no_magic",
    8: "tunnel", 9: "private", 10: "godroom", 11: "house",
    12: "house_crash", 13: "atrium", 14: "olc", 15: "bfs_mark",
}

_MOB_ACT_FLAG_NAMES: dict[int, str] = {
    0: "spec", 1: "sentinel", 2: "scavenger", 3: "is_npc",
    4: "aware", 5: "aggressive", 6: "stay_zone", 7: "wimpy",
    8: "aggr_evil", 9: "aggr_good", 10: "aggr_neutral",
    11: "memory", 12: "helper", 13: "no_charm", 14: "no_summn",
    15: "no_sleep", 16: "no_bash", 17: "no_blind",
}

_AFF_FLAG_NAMES: dict[int, str] = {
    0: "blind", 1: "invisible", 2: "detect_align", 3: "detect_invis",
    4: "detect_magic", 5: "sense_life", 6: "waterwalk", 7: "sanctuary",
    8: "group", 9: "curse", 10: "infravision", 11: "poison",
    12: "protect_evil", 13: "protect_good", 14: "sleep", 15: "no_track",
    16: "fly", 17: "scuba", 18: "sneak", 19: "hide",
    20: "charm",
}

_ITEM_FLAG_NAMES: dict[int, str] = {
    0: "glow", 1: "hum", 2: "no_rent", 3: "no_donate",
    4: "no_invis", 5: "invisible", 6: "magic", 7: "no_drop",
    8: "bless", 9: "anti_good", 10: "anti_evil", 11: "anti_neutral",
    12: "anti_mage", 13: "anti_cleric", 14: "anti_thief", 15: "anti_warrior",
    16: "no_sell",
}

_ITEM_TYPE_NAMES: dict[int, str] = {
    0: "undefined", 1: "light", 2: "scroll", 3: "wand", 4: "staff",
    5: "weapon", 6: "fireweapon", 7: "missile", 8: "treasure",
    9: "armor", 10: "potion", 11: "worn", 12: "other",
    13: "food", 14: "trash", 15: "container", 16: "note",
    17: "drinkcon", 18: "key", 19: "pen", 20: "money",
    21: "boat", 22: "fountain",
}

_APPLY_NAMES: dict[int, str] = {
    0: "none", 1: "str", 2: "dex", 3: "int", 4: "wis",
    5: "con", 6: "cha", 7: "class", 8: "level",
    9: "age", 10: "weight", 11: "height",
    12: "mana", 13: "hp", 14: "move",
    15: "gold", 16: "exp", 17: "ac",
    18: "hitroll", 19: "damroll",
    24: "saving_para", 25: "saving_rod", 26: "saving_petri",
    27: "saving_breath", 28: "saving_spell",
}

_TARGET_NAMES: dict[int, str] = {
    0: "ignore", 1: "char_room", 2: "char_world",
    4: "fight_self", 8: "fight_vict",
    16: "self_only", 32: "not_self",
    64: "obj_inv", 128: "obj_room", 256: "obj_world", 512: "obj_equip",
}

_ROUTINE_NAMES: dict[int, str] = {
    1: "damage", 2: "affects", 4: "unaffects", 8: "points",
    16: "alter_objs", 32: "groups", 64: "masses", 128: "areas",
    256: "summons", 512: "creations", 1024: "manual",
}

_QUEST_TYPE_NAMES: dict[int, str] = {
    0: "kill", 1: "gather", 2: "explore",
}
