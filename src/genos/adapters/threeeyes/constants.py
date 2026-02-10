"""Constants and flag mappings for 3eyes MUD (from mtype.h / mstruct.h)."""

from __future__ import annotations

# ── Struct sizes (32-bit Linux, natural alignment) ──────────────────────

SIZEOF_OBJECT = 352
SIZEOF_CREATURE = 1184
SIZEOF_ROOM = 480
SIZEOF_EXIT = 44
SIZEOF_DAILY = 8
SIZEOF_LASTTIME = 12

RECORDS_PER_FILE = 100  # MFILESIZE / OFILESIZE

# ── Creature types ──────────────────────────────────────────────────────

CREATURE_PLAYER = 0
CREATURE_MONSTER = 1
CREATURE_NPC = 2

# ── Character classes (1-indexed) ──────────────────────────────────────

CLASSES: dict[int, str] = {
    1: "Assassin",
    2: "Barbarian",
    3: "Cleric",
    4: "Fighter",
    5: "Mage",
    6: "Paladin",
    7: "Ranger",
    8: "Thief",
}

# ── Character races (1-indexed) ────────────────────────────────────────

RACES: dict[int, str] = {
    1: "Dwarf",
    2: "Elf",
    3: "Half-Elf",
    4: "Hobbit",
    5: "Human",
    6: "Orc",
    7: "Half-Giant",
    8: "Gnome",
}

# ── Object types ───────────────────────────────────────────────────────

ITEM_TYPES: dict[int, str] = {
    5: "armor",
    6: "potion",
    7: "scroll",
    8: "wand",
    9: "container",
    10: "money",
    11: "key",
    12: "lightsource",
    13: "misc",
    14: "container2",
    15: "hp_up",
}

# ── Proficiencies (index into proficiency[5]) ──────────────────────────

PROFICIENCIES: dict[int, str] = {
    0: "sharp",
    1: "thrust",
    2: "blunt",
    3: "pole",
    4: "missile",
}

# ── Magic Realms (1-indexed in code, 0-indexed in array) ──────────────

MAGIC_REALMS: dict[int, str] = {
    1: "earth",
    2: "wind",
    3: "fire",
    4: "water",
}

# ── Spell names (index = spell constant) ──────────────────────────────

SPELL_NAMES: dict[int, str] = {
    0: "vigor",
    1: "hurt",
    2: "light",
    3: "cure_poison",
    4: "bless",
    5: "protection",
    6: "fireball",
    7: "invisibility",
    8: "restore",
    9: "detect_invisible",
    10: "detect_magic",
    11: "teleport",
    12: "befuddle",
    13: "lightning",
    14: "ice_blast",
    15: "enchant",
    16: "recall",
    17: "summon",
    18: "mend_wounds",
    19: "full_heal",
    20: "track",
    21: "levitate",
    22: "resist_fire",
    23: "fly",
    24: "resist_magic",
    25: "shock",
    26: "rumble",
    27: "burn",
    28: "blister",
    29: "dust_gust",
    30: "water_bolt",
    31: "crush",
    32: "engulf",
    33: "burst",
    34: "steam",
    35: "shatter",
    36: "immolate",
    37: "blood_boil",
    38: "thunder",
    39: "earthquake",
    40: "flood_fill",
    41: "know_alignment",
    42: "remove_curse",
    43: "resist_cold",
    44: "breathe_water",
    45: "stone_shield",
    46: "locate",
    47: "drain_exp",
    48: "remove_disease",
    49: "remove_blind",
    50: "fear",
    51: "room_vigor",
    52: "transport",
    53: "blindness",
    54: "silence",
    55: "charm",
    56: "dragon_slave",
    57: "giga_slave",
    58: "plasma",
    59: "megiddo",
    60: "hellfire",
    61: "aqua_ray",
    62: "upgrade",
}

# ── Wear positions (wearflag on object / MAXWEAR=20) ──────────────────

WEAR_POSITIONS: dict[int, str] = {
    1: "body",
    2: "arms",
    3: "legs",
    4: "neck",
    5: "neck2",
    6: "hands",
    7: "head",
    8: "feet",
    9: "finger",
    10: "finger2",
    11: "finger3",
    12: "finger4",
    13: "finger5",
    14: "finger6",
    15: "finger7",
    16: "finger8",
    17: "held",
    18: "shield",
    19: "face",
    20: "wield",
}

# ── Room flags (bit positions) ─────────────────────────────────────────

ROOM_FLAGS: dict[int, str] = {
    0: "shop",
    1: "dump",
    2: "pawn",
    3: "train",
    7: "repair",
    8: "dark_always",
    9: "dark_night",
    10: "post_office",
    11: "no_kill",
    12: "no_teleport",
    13: "heal_room",
    14: "one_player",
    15: "two_player",
    16: "three_player",
    17: "no_magic",
    18: "perm_track",
    19: "earth_realm",
    20: "wind_realm",
    21: "fire_realm",
    22: "water_realm",
    23: "player_wander",
    24: "player_harm",
    25: "player_poison",
    26: "player_mp_drain",
    27: "player_befuddle",
    28: "no_leave",
    29: "pledge",
    30: "rescind",
    31: "no_potion",
    32: "magic_extend",
    33: "no_login",
    34: "election",
    35: "forge",
    36: "survival",
    37: "family",
    38: "only_family",
    39: "bank",
    40: "marriage_only",
    41: "marriage",
    42: "killer",
    43: "no_map",
    44: "casino",
    45: "poker",
    46: "event",
    47: "shrine",
}

# ── Monster flags (bit positions) ─────────────────────────────────────

MOB_FLAGS: dict[int, str] = {
    0: "permanent",
    1: "hidden",
    2: "invisible",
    3: "man_to_men",
    4: "no_s_plural",
    5: "no_prefix",
    6: "aggressive",
    7: "guards_treasure",
    8: "blocks_exits",
    9: "follows_attacker",
    10: "flees",
    11: "scavenger",
    12: "male",
    13: "poisoner",
    14: "undead",
    15: "no_steal",
    16: "poisoned",
    17: "casts_magic",
    18: "has_scavenged",
    19: "breath_weapon",
    20: "magic_only",
    21: "detect_invisible",
    22: "enchant_only",
    23: "talks",
    24: "unkillable",
    25: "no_random_gold",
    26: "talk_aggro",
    27: "resist_magic",
    28: "breath_type1",
    29: "breath_type2",
    30: "energy_drain",
    31: "kingdom",
    32: "pledge",
    33: "rescind",
    34: "disease",
    35: "dissolve_item",
    36: "purchase",
    37: "trade",
    38: "passive_guard",
    39: "good_aggro",
    40: "evil_aggro",
    41: "death_desc",
    42: "magic_percent",
    43: "resist_befuddle",
    44: "no_circle",
    45: "blinds",
    46: "dm_follow",
    47: "fearful",
    48: "silenced",
    49: "blind",
    50: "charmed",
    51: "befuddled",
}

# ── Object flags (bit positions) ──────────────────────────────────────

ITEM_FLAGS: dict[int, str] = {
    0: "permanent",
    1: "hidden",
    2: "invisible",
    3: "some_prefix",
    4: "no_s_plural",
    5: "no_prefix",
    6: "container",
    7: "weightless",
    8: "temp_perm",
    9: "perm_inventory",
    10: "no_mage",
    11: "light",
    12: "good_only",
    13: "evil_only",
    14: "enchanted",
    15: "no_fix",
    16: "climbing",
    17: "no_take",
    18: "scenery",
    19: "size1",
    20: "size2",
    21: "random_enchant",
    22: "cursed",
    23: "worn",
    24: "use_from_floor",
    25: "container_devour",
    26: "female_only",
    27: "male_only",
    28: "obj_dice_damage",
    29: "pledge_only",
    30: "kingdom",
    31: "class_selective",
    32: "class_assassin",
    33: "class_barbarian",
    34: "class_cleric",
    35: "class_fighter",
    36: "class_mage",
    37: "class_paladin",
    38: "class_ranger",
    39: "class_thief",
    40: "stun_by_ndice",
    41: "no_shatter",
    42: "always_critical",
    43: "custom_name",
    44: "special",
    45: "marriage_only",
    46: "event",
    47: "named",
    48: "no_decompose",
    49: "bokun",
    50: "shadow",
    51: "shadow2",
    52: "event2",
    53: "invin_only",
    54: "caretaker_only",
    55: "care2_only",
    56: "family",
    57: "threeeyes",
    58: "care3_only",
    59: "bomb",
}

# ── Exit flags (bit positions) ────────────────────────────────────────

EXIT_FLAGS: dict[int, str] = {
    0: "secret",
    1: "invisible",
    2: "locked",
    3: "closed",
    4: "lockable",
    5: "closable",
    6: "unpickable",
    7: "naked",
    8: "climb",
    9: "repel",
    10: "difficult_climb",
    11: "fly_only",
    12: "female_only",
    13: "male_only",
    14: "pledge_only",
    15: "kingdom",
    16: "night_only",
    17: "day_only",
    18: "passive_guard",
    19: "no_see",
}
