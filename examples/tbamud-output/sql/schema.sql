-- GenOS Database Schema
-- Auto-generated from UIR

BEGIN;

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
    base_thac0   INTEGER NOT NULL DEFAULT 20,
    hp_gain_min  INTEGER NOT NULL DEFAULT 1,
    hp_gain_max  INTEGER NOT NULL DEFAULT 10
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

COMMIT;
