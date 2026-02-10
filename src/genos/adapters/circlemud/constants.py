"""CircleMUD/tbaMUD constant mappings."""

# ── Directions ──────────────────────────────────────────────────────────

DIRECTIONS = {
    0: "north", 1: "east", 2: "south", 3: "west",
    4: "up", 5: "down", 6: "northwest", 7: "northeast",
    8: "southeast", 9: "southwest",
}
NUM_DIRS = 10

# ── Sector Types ────────────────────────────────────────────────────────

SECTOR_TYPES = {
    0: "inside", 1: "city", 2: "field", 3: "forest",
    4: "hills", 5: "mountain", 6: "water_swim", 7: "water_noswim",
    8: "flying", 9: "underwater",
}

# ── Room Flags ──────────────────────────────────────────────────────────

ROOM_FLAGS = {
    0: "dark", 1: "death", 2: "nomob", 3: "indoors",
    4: "peaceful", 5: "soundproof", 6: "notrack", 7: "nomagic",
    8: "tunnel", 9: "private", 10: "godroom", 11: "house",
    12: "house_crash", 13: "atrium", 14: "olc", 15: "bfs_mark",
    16: "worldmap",
}

# ── Exit Flags ──────────────────────────────────────────────────────────

EX_ISDOOR = 1 << 0
EX_CLOSED = 1 << 1
EX_LOCKED = 1 << 2
EX_PICKPROOF = 1 << 3
EX_HIDDEN = 1 << 4

# ── Item Types ──────────────────────────────────────────────────────────

ITEM_TYPES = {
    1: "light", 2: "scroll", 3: "wand", 4: "staff",
    5: "weapon", 6: "furniture", 7: "free", 8: "treasure",
    9: "armor", 10: "potion", 11: "worn", 12: "other",
    13: "trash", 14: "free2", 15: "container", 16: "note",
    17: "drinkcon", 18: "key", 19: "food", 20: "money",
    21: "pen", 22: "boat", 23: "fountain",
}

# ── Item Extra Flags ────────────────────────────────────────────────────

ITEM_EXTRA_FLAGS = {
    0: "glow", 1: "hum", 2: "norent", 3: "nodonate",
    4: "noinvis", 5: "invisible", 6: "magic", 7: "nodrop",
    8: "bless", 9: "anti_good", 10: "anti_evil", 11: "anti_neutral",
    12: "anti_magic_user", 13: "anti_cleric", 14: "anti_thief",
    15: "anti_warrior", 16: "nosell", 17: "quest",
}

# ── Item Wear Flags ─────────────────────────────────────────────────────

ITEM_WEAR_FLAGS = {
    0: "take", 1: "finger", 2: "neck", 3: "body",
    4: "head", 5: "legs", 6: "feet", 7: "hands",
    8: "arms", 9: "shield", 10: "about", 11: "waist",
    12: "wrist", 13: "wield", 14: "hold",
}

# ── Equipment Slots ─────────────────────────────────────────────────────

WEAR_SLOTS = {
    0: "light", 1: "finger_r", 2: "finger_l", 3: "neck_1",
    4: "neck_2", 5: "body", 6: "head", 7: "legs",
    8: "feet", 9: "hands", 10: "arms", 11: "shield",
    12: "about", 13: "waist", 14: "wrist_r", 15: "wrist_l",
    16: "wield", 17: "hold",
}

# ── Apply Types ─────────────────────────────────────────────────────────

APPLY_TYPES = {
    0: "none", 1: "str", 2: "dex", 3: "int",
    4: "wis", 5: "con", 6: "cha", 7: "class",
    8: "level", 9: "age", 10: "char_weight", 11: "char_height",
    12: "mana", 13: "hit", 14: "move", 15: "gold",
    16: "exp", 17: "ac", 18: "hitroll", 19: "damroll",
    20: "saving_para", 21: "saving_rod", 22: "saving_petri",
    23: "saving_breath", 24: "saving_spell",
}

# ── MOB Flags ───────────────────────────────────────────────────────────

MOB_FLAGS = {
    0: "spec", 1: "sentinel", 2: "scavenger", 3: "isnpc",
    4: "aware", 5: "aggressive", 6: "stay_zone", 7: "wimpy",
    8: "aggr_evil", 9: "aggr_good", 10: "aggr_neutral",
    11: "memory", 12: "helper", 13: "nocharm", 14: "nosummon",
    15: "nosleep", 16: "nobash", 17: "noblind", 18: "nokill",
    19: "notdeadyet",
}

# ── Affect Flags ────────────────────────────────────────────────────────

AFF_FLAGS = {
    0: "dontuse", 1: "blind", 2: "invisible", 3: "detect_align",
    4: "detect_invis", 5: "detect_magic", 6: "sense_life",
    7: "waterwalk", 8: "sanctuary", 9: "unused", 10: "curse",
    11: "infravision", 12: "poison", 13: "protect_evil",
    14: "protect_good", 15: "sleep", 16: "notrack", 17: "flying",
    18: "scuba", 19: "sneak", 20: "hide", 21: "free", 22: "charm",
}

# ── Positions ───────────────────────────────────────────────────────────

POSITIONS = {
    0: "dead", 1: "mortally_wounded", 2: "incapacitated",
    3: "stunned", 4: "sleeping", 5: "resting", 6: "sitting",
    7: "fighting", 8: "standing",
}

# ── Sexes ───────────────────────────────────────────────────────────────

SEXES = {0: "neutral", 1: "male", 2: "female"}

# ── PC Classes ──────────────────────────────────────────────────────────

PC_CLASSES = {
    0: "magic_user", 1: "cleric", 2: "thief", 3: "warrior",
}

# ── NPC Classes ─────────────────────────────────────────────────────────

NPC_CLASSES = {
    0: "other", 1: "undead", 2: "humanoid",
    3: "animal", 4: "dragon", 5: "giant",
}

# ── Zone Flags ──────────────────────────────────────────────────────────

ZONE_FLAGS = {
    0: "closed", 1: "noimmort", 2: "quest", 3: "grid",
    4: "nobuild", 5: "noastral", 6: "worldmap",
}

# ── Bare Hand Attack Types ──────────────────────────────────────────────

ATTACK_TYPES = {
    0: "hit", 1: "sting", 2: "whip", 3: "slash",
    4: "bite", 5: "bludgeon", 6: "crush", 7: "pound",
    8: "claw", 9: "maul", 10: "thrash", 11: "pierce",
    12: "blast", 13: "punch", 14: "stab",
}

# ── Trigger Types ───────────────────────────────────────────────────────

TRIG_ATTACH_TYPES = {0: "mob", 1: "obj", 2: "wld"}

# Bitvector letter-to-number mapping (CircleMUD uses 'a'=1, 'b'=2, ... for bitvectors)
# The asciiflag_conv function in utils.c handles this
def asciiflag_to_int(flag_str: str) -> int:
    """Convert CircleMUD ascii bitvector string to integer.

    CircleMUD uses a custom encoding where lowercase letters represent
    bit positions (a=bit0, b=bit1, ..., z=bit25) and uppercase continue
    (A=bit26, B=bit27, ...). Multiple letters set multiple bits.
    A plain number is returned as-is.
    """
    if not flag_str or flag_str == "0":
        return 0

    # If it's a plain number, return it
    try:
        return int(flag_str)
    except ValueError:
        pass

    result = 0
    for ch in flag_str:
        if ch.islower():
            result |= 1 << (ord(ch) - ord('a'))
        elif ch.isupper():
            result |= 1 << (26 + ord(ch) - ord('A'))
    return result


def int_to_flag_list(value: int) -> list[int]:
    """Convert an integer bitvector to a list of set bit positions."""
    flags = []
    bit = 0
    while value > 0:
        if value & 1:
            flags.append(bit)
        value >>= 1
        bit += 1
    return flags
