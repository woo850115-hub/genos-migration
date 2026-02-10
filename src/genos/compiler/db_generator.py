"""UIR → PostgreSQL DDL + seed data generator."""

from __future__ import annotations

import json
from typing import TextIO

from genos.uir.schema import UIR


def generate_ddl(uir: UIR, out: TextIO) -> None:
    """Write PostgreSQL CREATE TABLE statements."""
    out.write("-- GenOS Database Schema\n")
    out.write("-- Auto-generated from UIR\n\n")

    out.write("BEGIN;\n\n")

    out.write("""\
CREATE TABLE IF NOT EXISTS rooms (
    vnum        INTEGER PRIMARY KEY,
    name        TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    zone_number INTEGER NOT NULL DEFAULT 0,
    sector_type INTEGER NOT NULL DEFAULT 0,
    room_flags  JSONB NOT NULL DEFAULT '[]',
    exits       JSONB NOT NULL DEFAULT '[]',
    extra_descs JSONB NOT NULL DEFAULT '[]',
    trigger_vnums JSONB NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS items (
    vnum              INTEGER PRIMARY KEY,
    keywords          TEXT NOT NULL DEFAULT '',
    short_description TEXT NOT NULL DEFAULT '',
    long_description  TEXT NOT NULL DEFAULT '',
    item_type         INTEGER NOT NULL DEFAULT 0,
    extra_flags       JSONB NOT NULL DEFAULT '[]',
    wear_flags        JSONB NOT NULL DEFAULT '[]',
    values            JSONB NOT NULL DEFAULT '[0,0,0,0]',
    weight            INTEGER NOT NULL DEFAULT 0,
    cost              INTEGER NOT NULL DEFAULT 0,
    rent              INTEGER NOT NULL DEFAULT 0,
    affects           JSONB NOT NULL DEFAULT '[]',
    extra_descs       JSONB NOT NULL DEFAULT '[]',
    trigger_vnums     JSONB NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS monsters (
    vnum                 INTEGER PRIMARY KEY,
    keywords             TEXT NOT NULL DEFAULT '',
    short_description    TEXT NOT NULL DEFAULT '',
    long_description     TEXT NOT NULL DEFAULT '',
    detailed_description TEXT NOT NULL DEFAULT '',
    level                INTEGER NOT NULL DEFAULT 1,
    hitroll              INTEGER NOT NULL DEFAULT 0,
    armor_class          INTEGER NOT NULL DEFAULT 100,
    hp_dice              TEXT NOT NULL DEFAULT '0d0+0',
    damage_dice          TEXT NOT NULL DEFAULT '0d0+0',
    gold                 INTEGER NOT NULL DEFAULT 0,
    experience           INTEGER NOT NULL DEFAULT 0,
    action_flags         JSONB NOT NULL DEFAULT '[]',
    affect_flags         JSONB NOT NULL DEFAULT '[]',
    alignment            INTEGER NOT NULL DEFAULT 0,
    sex                  INTEGER NOT NULL DEFAULT 0,
    trigger_vnums        JSONB NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS classes (
    id           INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    abbreviation TEXT NOT NULL DEFAULT '',
    hp_gain_min  INTEGER NOT NULL DEFAULT 1,
    hp_gain_max  INTEGER NOT NULL DEFAULT 10,
    extensions   JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS zones (
    vnum           INTEGER PRIMARY KEY,
    name           TEXT NOT NULL DEFAULT '',
    builders       TEXT NOT NULL DEFAULT '',
    lifespan       INTEGER NOT NULL DEFAULT 30,
    bot            INTEGER NOT NULL DEFAULT 0,
    top            INTEGER NOT NULL DEFAULT 0,
    reset_mode     INTEGER NOT NULL DEFAULT 2,
    zone_flags     JSONB NOT NULL DEFAULT '[]',
    reset_commands JSONB NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS shops (
    vnum          INTEGER PRIMARY KEY,
    keeper_vnum   INTEGER NOT NULL DEFAULT -1,
    selling_items JSONB NOT NULL DEFAULT '[]',
    profit_buy    REAL NOT NULL DEFAULT 1.0,
    profit_sell   REAL NOT NULL DEFAULT 1.0,
    shop_room     INTEGER NOT NULL DEFAULT -1,
    open1         INTEGER NOT NULL DEFAULT 0,
    close1        INTEGER NOT NULL DEFAULT 0,
    open2         INTEGER NOT NULL DEFAULT 0,
    close2        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS triggers (
    vnum         INTEGER PRIMARY KEY,
    name         TEXT NOT NULL DEFAULT '',
    attach_type  INTEGER NOT NULL DEFAULT 0,
    trigger_type INTEGER NOT NULL DEFAULT 0,
    numeric_arg  INTEGER NOT NULL DEFAULT 0,
    arg_list     TEXT NOT NULL DEFAULT '',
    script       TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS quests (
    vnum               INTEGER PRIMARY KEY,
    name               TEXT NOT NULL DEFAULT '',
    keywords           TEXT NOT NULL DEFAULT '',
    description        TEXT NOT NULL DEFAULT '',
    completion_message TEXT NOT NULL DEFAULT '',
    quest_flags        INTEGER NOT NULL DEFAULT 0,
    quest_type         INTEGER NOT NULL DEFAULT 0,
    target_vnum        INTEGER NOT NULL DEFAULT -1,
    mob_vnum           INTEGER NOT NULL DEFAULT -1,
    reward_gold        INTEGER NOT NULL DEFAULT 0,
    reward_exp         INTEGER NOT NULL DEFAULT 0,
    reward_obj         INTEGER NOT NULL DEFAULT -1
);

CREATE TABLE IF NOT EXISTS socials (
    command              TEXT PRIMARY KEY,
    min_victim_position  INTEGER NOT NULL DEFAULT 0,
    flags                INTEGER NOT NULL DEFAULT 0,
    no_arg_to_char       TEXT NOT NULL DEFAULT '',
    no_arg_to_room       TEXT NOT NULL DEFAULT '',
    found_to_char        TEXT NOT NULL DEFAULT '',
    found_to_room        TEXT NOT NULL DEFAULT '',
    found_to_victim      TEXT NOT NULL DEFAULT '',
    not_found            TEXT NOT NULL DEFAULT '',
    self_to_char         TEXT NOT NULL DEFAULT '',
    self_to_room         TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS help_entries (
    id       SERIAL PRIMARY KEY,
    keywords JSONB NOT NULL DEFAULT '[]',
    min_level INTEGER NOT NULL DEFAULT 0,
    text     TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS commands (
    name         TEXT PRIMARY KEY,
    min_position INTEGER NOT NULL DEFAULT 0,
    min_level    INTEGER NOT NULL DEFAULT 0,
    min_match    TEXT NOT NULL DEFAULT '',
    handler      TEXT NOT NULL DEFAULT '',
    subcmd       INTEGER NOT NULL DEFAULT 0,
    category     TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS skills (
    id           INTEGER PRIMARY KEY,
    name         TEXT NOT NULL DEFAULT '',
    spell_type   TEXT NOT NULL DEFAULT '',
    max_mana     INTEGER NOT NULL DEFAULT 0,
    min_mana     INTEGER NOT NULL DEFAULT 0,
    mana_change  INTEGER NOT NULL DEFAULT 0,
    min_position INTEGER NOT NULL DEFAULT 0,
    targets      INTEGER NOT NULL DEFAULT 0,
    violent      BOOLEAN NOT NULL DEFAULT FALSE,
    routines     INTEGER NOT NULL DEFAULT 0,
    wearoff_msg  TEXT NOT NULL DEFAULT '',
    class_levels JSONB NOT NULL DEFAULT '{}',
    extensions   JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS races (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL DEFAULT '',
    abbreviation    TEXT NOT NULL DEFAULT '',
    stat_modifiers  JSONB NOT NULL DEFAULT '{}',
    allowed_classes JSONB NOT NULL DEFAULT '[]',
    extensions      JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS game_configs (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL DEFAULT '',
    value_type  TEXT NOT NULL DEFAULT 'int',
    category    TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS experience_table (
    class_id     INTEGER NOT NULL DEFAULT 0,
    level        INTEGER NOT NULL,
    exp_required BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (class_id, level)
);

CREATE TABLE IF NOT EXISTS thac0_table (
    class_id INTEGER NOT NULL DEFAULT 0,
    level    INTEGER NOT NULL,
    thac0    INTEGER NOT NULL DEFAULT 20,
    PRIMARY KEY (class_id, level)
);

CREATE TABLE IF NOT EXISTS saving_throws (
    class_id   INTEGER NOT NULL DEFAULT 0,
    save_type  INTEGER NOT NULL DEFAULT 0,
    level      INTEGER NOT NULL,
    save_value INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (class_id, save_type, level)
);

CREATE TABLE IF NOT EXISTS level_titles (
    class_id INTEGER NOT NULL DEFAULT 0,
    level    INTEGER NOT NULL,
    gender   TEXT NOT NULL DEFAULT 'male',
    title    TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (class_id, level, gender)
);

CREATE TABLE IF NOT EXISTS attribute_modifiers (
    stat_name TEXT NOT NULL,
    score     INTEGER NOT NULL,
    modifiers JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (stat_name, score)
);

CREATE TABLE IF NOT EXISTS practice_params (
    class_id         INTEGER PRIMARY KEY,
    learned_level    INTEGER NOT NULL DEFAULT 0,
    max_per_practice INTEGER NOT NULL DEFAULT 0,
    min_per_practice INTEGER NOT NULL DEFAULT 0,
    prac_type        TEXT NOT NULL DEFAULT 'skill',
    extensions       JSONB NOT NULL DEFAULT '{}'
);

""")

    out.write("COMMIT;\n")


def generate_seed_data(uir: UIR, out: TextIO) -> None:
    """Write INSERT statements for seed data."""
    out.write("-- GenOS Seed Data\n")
    out.write("-- Auto-generated from UIR\n\n")
    out.write("BEGIN;\n\n")

    # Rooms
    for r in uir.rooms:
        exits_json = json.dumps([
            {"dir": e.direction, "dest": e.destination,
             "desc": e.description, "keyword": e.keyword,
             "door_flags": e.door_flags, "key_vnum": e.key_vnum}
            for e in r.exits
        ])
        extra_json = json.dumps([
            {"keywords": ed.keywords, "description": ed.description}
            for ed in r.extra_descriptions
        ])
        out.write(
            f"INSERT INTO rooms (vnum, name, description, zone_number, "
            f"sector_type, room_flags, exits, extra_descs, trigger_vnums) "
            f"VALUES ({r.vnum}, {_sql_str(r.name)}, {_sql_str(r.description)}, "
            f"{r.zone_number}, {r.sector_type}, "
            f"{_sql_str(json.dumps(r.room_flags))}, "
            f"{_sql_str(exits_json)}, {_sql_str(extra_json)}, "
            f"{_sql_str(json.dumps(r.trigger_vnums))});\n"
        )

    out.write("\n")

    # Items
    for item in uir.items:
        affects_json = json.dumps([
            {"location": a.location, "modifier": a.modifier}
            for a in item.affects
        ])
        extra_json = json.dumps([
            {"keywords": ed.keywords, "description": ed.description}
            for ed in item.extra_descriptions
        ])
        out.write(
            f"INSERT INTO items (vnum, keywords, short_description, "
            f"long_description, item_type, extra_flags, wear_flags, "
            f"values, weight, cost, rent, affects, extra_descs, trigger_vnums) "
            f"VALUES ({item.vnum}, {_sql_str(item.keywords)}, "
            f"{_sql_str(item.short_description)}, "
            f"{_sql_str(item.long_description)}, {item.item_type}, "
            f"{_sql_str(json.dumps(item.extra_flags))}, "
            f"{_sql_str(json.dumps(item.wear_flags))}, "
            f"{_sql_str(json.dumps(item.values))}, "
            f"{item.weight}, {item.cost}, {item.rent}, "
            f"{_sql_str(affects_json)}, {_sql_str(extra_json)}, "
            f"{_sql_str(json.dumps(item.trigger_vnums))});\n"
        )

    out.write("\n")

    # Monsters
    for m in uir.monsters:
        out.write(
            f"INSERT INTO monsters (vnum, keywords, short_description, "
            f"long_description, detailed_description, level, hitroll, "
            f"armor_class, hp_dice, damage_dice, gold, experience, "
            f"action_flags, affect_flags, alignment, sex, trigger_vnums) "
            f"VALUES ({m.vnum}, {_sql_str(m.keywords)}, "
            f"{_sql_str(m.short_description)}, "
            f"{_sql_str(m.long_description)}, "
            f"{_sql_str(m.detailed_description)}, "
            f"{m.level}, {m.hitroll}, {m.armor_class}, "
            f"{_sql_str(str(m.hp_dice))}, {_sql_str(str(m.damage_dice))}, "
            f"{m.gold}, {m.experience}, "
            f"{_sql_str(json.dumps(m.action_flags))}, "
            f"{_sql_str(json.dumps(m.affect_flags))}, "
            f"{m.alignment}, {m.sex}, "
            f"{_sql_str(json.dumps(m.trigger_vnums))});\n"
        )

    out.write("\n")

    # Classes
    for c in uir.character_classes:
        out.write(
            f"INSERT INTO classes (id, name, abbreviation, "
            f"hp_gain_min, hp_gain_max, extensions) "
            f"VALUES ({c.id}, {_sql_str(c.name)}, "
            f"{_sql_str(c.abbreviation)}, "
            f"{c.hp_gain_min}, {c.hp_gain_max}, "
            f"{_sql_str(json.dumps(c.extensions))});\n"
        )

    out.write("\n")

    # Zones
    for z in uir.zones:
        cmds_json = json.dumps([
            {"cmd": c.command, "if_flag": c.if_flag,
             "arg1": c.arg1, "arg2": c.arg2, "arg3": c.arg3, "arg4": c.arg4}
            for c in z.reset_commands
        ])
        out.write(
            f"INSERT INTO zones (vnum, name, builders, lifespan, bot, top, "
            f"reset_mode, zone_flags, reset_commands) "
            f"VALUES ({z.vnum}, {_sql_str(z.name)}, "
            f"{_sql_str(z.builders)}, {z.lifespan}, {z.bot}, {z.top}, "
            f"{z.reset_mode}, {_sql_str(json.dumps(z.zone_flags))}, "
            f"{_sql_str(cmds_json)});\n"
        )

    out.write("\n")

    # Shops
    for s in uir.shops:
        out.write(
            f"INSERT INTO shops (vnum, keeper_vnum, selling_items, "
            f"profit_buy, profit_sell, shop_room, "
            f"open1, close1, open2, close2) "
            f"VALUES ({s.vnum}, {s.keeper_vnum}, "
            f"{_sql_str(json.dumps(s.selling_items))}, "
            f"{s.profit_buy}, {s.profit_sell}, {s.shop_room}, "
            f"{s.open1}, {s.close1}, {s.open2}, {s.close2});\n"
        )

    out.write("\n")

    # Triggers
    for t in uir.triggers:
        out.write(
            f"INSERT INTO triggers (vnum, name, attach_type, trigger_type, "
            f"numeric_arg, arg_list, script) "
            f"VALUES ({t.vnum}, {_sql_str(t.name)}, {t.attach_type}, "
            f"{t.trigger_type}, {t.numeric_arg}, "
            f"{_sql_str(t.arg_list)}, {_sql_str(t.script)});\n"
        )

    out.write("\n")

    # Quests
    for q in uir.quests:
        out.write(
            f"INSERT INTO quests (vnum, name, keywords, description, "
            f"completion_message, quest_flags, quest_type, target_vnum, "
            f"mob_vnum, reward_gold, reward_exp, reward_obj) "
            f"VALUES ({q.vnum}, {_sql_str(q.name)}, "
            f"{_sql_str(q.keywords)}, {_sql_str(q.description)}, "
            f"{_sql_str(q.completion_message)}, {q.quest_flags}, "
            f"{q.quest_type}, {q.target_vnum}, {q.mob_vnum}, "
            f"{q.reward_gold}, {q.reward_exp}, {q.reward_obj});\n"
        )

    out.write("\n")

    # Socials
    for soc in uir.socials:
        out.write(
            f"INSERT INTO socials (command, min_victim_position, flags, "
            f"no_arg_to_char, no_arg_to_room, found_to_char, found_to_room, "
            f"found_to_victim, not_found, self_to_char, self_to_room) "
            f"VALUES ({_sql_str(soc.command)}, {soc.min_victim_position}, "
            f"{soc.flags}, {_sql_str(soc.no_arg_to_char)}, "
            f"{_sql_str(soc.no_arg_to_room)}, {_sql_str(soc.found_to_char)}, "
            f"{_sql_str(soc.found_to_room)}, {_sql_str(soc.found_to_victim)}, "
            f"{_sql_str(soc.not_found)}, {_sql_str(soc.self_to_char)}, "
            f"{_sql_str(soc.self_to_room)});\n"
        )

    out.write("\n")

    # Help entries
    for h in uir.help_entries:
        out.write(
            f"INSERT INTO help_entries (keywords, min_level, text) "
            f"VALUES ({_sql_str(json.dumps(h.keywords))}, {h.min_level}, "
            f"{_sql_str(h.text)});\n"
        )

    out.write("\n")

    # Commands
    for cmd in uir.commands:
        out.write(
            f"INSERT INTO commands (name, min_position, min_level, "
            f"min_match, handler, subcmd, category) "
            f"VALUES ({_sql_str(cmd.name)}, {cmd.min_position}, "
            f"{cmd.min_level}, {_sql_str(cmd.min_match)}, "
            f"{_sql_str(cmd.handler)}, {cmd.subcmd}, "
            f"{_sql_str(cmd.category)});\n"
        )

    out.write("\n")

    # Skills
    for sk in uir.skills:
        out.write(
            f"INSERT INTO skills (id, name, spell_type, max_mana, min_mana, "
            f"mana_change, min_position, targets, violent, routines, "
            f"wearoff_msg, class_levels, extensions) "
            f"VALUES ({sk.id}, {_sql_str(sk.name)}, "
            f"{_sql_str(sk.spell_type)}, {sk.max_mana}, {sk.min_mana}, "
            f"{sk.mana_change}, {sk.min_position}, {sk.targets}, "
            f"{str(sk.violent).upper()}, {sk.routines}, "
            f"{_sql_str(sk.wearoff_msg)}, "
            f"{_sql_str(json.dumps({str(k): v for k, v in sk.class_levels.items()}))}, "
            f"{_sql_str(json.dumps(sk.extensions))});\n"
        )

    out.write("\n")

    # Races
    for race in uir.races:
        out.write(
            f"INSERT INTO races (id, name, abbreviation, "
            f"stat_modifiers, allowed_classes, extensions) "
            f"VALUES ({race.id}, {_sql_str(race.name)}, "
            f"{_sql_str(race.abbreviation)}, "
            f"{_sql_str(json.dumps(race.stat_modifiers))}, "
            f"{_sql_str(json.dumps(race.allowed_classes))}, "
            f"{_sql_str(json.dumps(race.extensions))});\n"
        )

    # Game configs
    for gc in uir.game_configs:
        out.write(
            f"INSERT INTO game_configs (key, value, value_type, category, description) "
            f"VALUES ({_sql_str(gc.key)}, {_sql_str(gc.value)}, "
            f"{_sql_str(gc.value_type)}, {_sql_str(gc.category)}, "
            f"{_sql_str(gc.description)});\n"
        )

    out.write("\n")

    # Experience table
    for exp in uir.experience_table:
        out.write(
            f"INSERT INTO experience_table (class_id, level, exp_required) "
            f"VALUES ({exp.class_id}, {exp.level}, {exp.exp_required});\n"
        )

    out.write("\n")

    # THAC0 table
    for th in uir.thac0_table:
        out.write(
            f"INSERT INTO thac0_table (class_id, level, thac0) "
            f"VALUES ({th.class_id}, {th.level}, {th.thac0});\n"
        )

    out.write("\n")

    # Saving throws
    for st in uir.saving_throws:
        out.write(
            f"INSERT INTO saving_throws (class_id, save_type, level, save_value) "
            f"VALUES ({st.class_id}, {st.save_type}, {st.level}, {st.save_value});\n"
        )

    out.write("\n")

    # Level titles
    for lt in uir.level_titles:
        out.write(
            f"INSERT INTO level_titles (class_id, level, gender, title) "
            f"VALUES ({lt.class_id}, {lt.level}, {_sql_str(lt.gender)}, "
            f"{_sql_str(lt.title)});\n"
        )

    out.write("\n")

    # Attribute modifiers
    for am in uir.attribute_modifiers:
        out.write(
            f"INSERT INTO attribute_modifiers (stat_name, score, modifiers) "
            f"VALUES ({_sql_str(am.stat_name)}, {am.score}, "
            f"{_sql_str(json.dumps(am.modifiers))});\n"
        )

    out.write("\n")

    # Practice params
    for pp in uir.practice_params:
        out.write(
            f"INSERT INTO practice_params (class_id, learned_level, "
            f"max_per_practice, min_per_practice, prac_type, extensions) "
            f"VALUES ({pp.class_id}, {pp.learned_level}, "
            f"{pp.max_per_practice}, {pp.min_per_practice}, "
            f"{_sql_str(pp.prac_type)}, "
            f"{_sql_str(json.dumps(pp.extensions))});\n"
        )

    out.write("\nCOMMIT;\n")


def _sql_str(value: str) -> str:
    """Escape a string for SQL single-quote literals."""
    escaped = value.replace("'", "''")
    return f"'{escaped}'"
