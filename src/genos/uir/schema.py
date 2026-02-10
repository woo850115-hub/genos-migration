"""UIR (Universal Intermediate Representation) data classes.

Defines the canonical intermediate format for migrating MUD game data
from any source (CircleMUD, DikuMUD, etc.) to the GenOS platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── Source Info ──────────────────────────────────────────────────────────

@dataclass
class SourceMudInfo:
    name: str
    version: str
    codebase: str  # e.g. "CircleMUD", "tbaMUD"
    source_path: str


@dataclass
class MigrationStats:
    total_rooms: int = 0
    total_items: int = 0
    total_monsters: int = 0
    total_zones: int = 0
    total_shops: int = 0
    total_triggers: int = 0
    total_quests: int = 0
    total_socials: int = 0
    total_help_entries: int = 0
    total_skills: int = 0
    total_commands: int = 0
    total_races: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class GameMetadata:
    game_name: str = ""
    description: str = ""
    num_classes: int = 0
    num_directions: int = 10
    num_item_types: int = 24
    num_equip_slots: int = 18


# ── Room / Exit ─────────────────────────────────────────────────────────

@dataclass
class Exit:
    direction: int  # 0-9: N E S W U D NW NE SE SW
    destination: int  # room vnum (or -1 for none)
    description: str = ""
    keyword: str = ""
    door_flags: int = 0
    key_vnum: int = -1


@dataclass
class ExtraDescription:
    keywords: str = ""
    description: str = ""


@dataclass
class Room:
    vnum: int
    name: str = ""
    description: str = ""
    zone_number: int = 0
    room_flags: list[int] = field(default_factory=list)
    sector_type: int = 0
    exits: list[Exit] = field(default_factory=list)
    extra_descriptions: list[ExtraDescription] = field(default_factory=list)
    trigger_vnums: list[int] = field(default_factory=list)
    extensions: dict[str, Any] = field(default_factory=dict)


# ── Item / Object ───────────────────────────────────────────────────────

@dataclass
class ItemAffect:
    location: int = 0  # APPLY_XXX
    modifier: int = 0


@dataclass
class Item:
    vnum: int
    keywords: str = ""
    short_description: str = ""
    long_description: str = ""
    action_description: str = ""
    item_type: int = 0
    extra_flags: list[int] = field(default_factory=list)
    wear_flags: list[int] = field(default_factory=list)
    values: list[int] = field(default_factory=lambda: [0, 0, 0, 0])
    weight: int = 0
    cost: int = 0
    rent: int = 0
    timer: int = 0
    min_level: int = 0
    extra_descriptions: list[ExtraDescription] = field(default_factory=list)
    affects: list[ItemAffect] = field(default_factory=list)
    trigger_vnums: list[int] = field(default_factory=list)


# ── Monster / Mobile ────────────────────────────────────────────────────

@dataclass
class DiceRoll:
    num: int = 0
    size: int = 0
    bonus: int = 0

    def __str__(self) -> str:
        return f"{self.num}d{self.size}+{self.bonus}"


@dataclass
class Monster:
    vnum: int
    keywords: str = ""
    short_description: str = ""
    long_description: str = ""
    detailed_description: str = ""
    action_flags: list[int] = field(default_factory=list)
    affect_flags: list[int] = field(default_factory=list)
    alignment: int = 0
    level: int = 1
    hitroll: int = 0
    armor_class: int = 100
    hp_dice: DiceRoll = field(default_factory=DiceRoll)
    damage_dice: DiceRoll = field(default_factory=DiceRoll)
    gold: int = 0
    experience: int = 0
    load_position: int = 8  # POS_STANDING
    default_position: int = 8
    sex: int = 0
    bare_hand_attack: int = 0
    trigger_vnums: list[int] = field(default_factory=list)
    # Enhanced mob format
    mob_type: str = "E"  # S = Simple, E = Enhanced
    extensions: dict[str, Any] = field(default_factory=dict)


# ── Character Class ─────────────────────────────────────────────────────

@dataclass
class CharacterClass:
    id: int
    name: str = ""
    abbreviation: str = ""
    hp_gain_min: int = 1
    hp_gain_max: int = 10
    mana_gain_min: int = 0
    mana_gain_max: int = 0
    move_gain_min: int = 0
    move_gain_max: int = 0
    extensions: dict[str, Any] = field(default_factory=dict)


# ── Combat System ───────────────────────────────────────────────────────

@dataclass
class CombatSystem:
    type: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    damage_types: list[str] = field(default_factory=list)


# ── Zone ────────────────────────────────────────────────────────────────

@dataclass
class ZoneResetCommand:
    command: str  # M, O, G, E, P, D, R, T, V
    if_flag: int = 0
    arg1: int = 0
    arg2: int = 0
    arg3: int = -1
    arg4: int = -1
    comment: str = ""


@dataclass
class Zone:
    vnum: int
    name: str = ""
    builders: str = ""
    lifespan: int = 30
    bot: int = 0
    top: int = 0
    reset_mode: int = 2
    zone_flags: list[int] = field(default_factory=list)
    min_level: int = -1
    max_level: int = -1
    reset_commands: list[ZoneResetCommand] = field(default_factory=list)


# ── Shop ────────────────────────────────────────────────────────────────

@dataclass
class Shop:
    vnum: int
    selling_items: list[int] = field(default_factory=list)  # item vnums
    profit_buy: float = 1.0
    profit_sell: float = 1.0
    accepting_types: list[int] = field(default_factory=list)
    no_such_item1: str = ""
    no_such_item2: str = ""
    do_not_buy: str = ""
    missing_cash1: str = ""
    missing_cash2: str = ""
    message_buy: str = ""
    message_sell: str = ""
    temper: int = 0
    bitvector: int = 0
    keeper_vnum: int = -1
    with_who: int = 0
    shop_room: int = -1
    open1: int = 0
    close1: int = 0
    open2: int = 0
    close2: int = 0


# ── Trigger (DG Script) ────────────────────────────────────────────────

@dataclass
class Trigger:
    vnum: int
    name: str = ""
    attach_type: int = 0  # 0=MOB, 1=OBJ, 2=WLD
    trigger_type: int = 0
    numeric_arg: int = 0
    arg_list: str = ""
    script: str = ""


# ── Quest ───────────────────────────────────────────────────────────────

@dataclass
class Quest:
    vnum: int
    name: str = ""
    keywords: str = ""
    description: str = ""
    completion_message: str = ""
    quit_message: str = ""
    quest_flags: int = 0
    quest_type: int = 0
    target_vnum: int = -1
    mob_vnum: int = -1
    value0: int = -1
    value1: int = -1
    value2: int = -1
    value3: int = -1
    reward_gold: int = 0
    reward_exp: int = 0
    reward_obj: int = -1
    next_quest: int = -1
    prev_quest: int = -1
    min_level: int = 0
    max_level: int = 0


# ── Command ─────────────────────────────────────────────────────────────

@dataclass
class Command:
    name: str = ""
    description: str = ""
    min_position: int = 0
    min_level: int = 0
    min_match: str = ""
    handler: str = ""
    subcmd: int = 0
    category: str = ""


# ── Social ─────────────────────────────────────────────────────────────

@dataclass
class Social:
    command: str = ""
    min_victim_position: int = 0
    flags: int = 0
    no_arg_to_char: str = ""
    no_arg_to_room: str = ""
    found_to_char: str = ""
    found_to_room: str = ""
    found_to_victim: str = ""
    not_found: str = ""
    self_to_char: str = ""
    self_to_room: str = ""


# ── Help Entry ─────────────────────────────────────────────────────────

@dataclass
class HelpEntry:
    keywords: list[str] = field(default_factory=list)
    min_level: int = 0
    text: str = ""


# ── Skill ──────────────────────────────────────────────────────────────

@dataclass
class Skill:
    id: int = 0
    name: str = ""
    spell_type: str = ""
    max_mana: int = 0
    min_mana: int = 0
    mana_change: int = 0
    min_position: int = 0
    targets: int = 0
    violent: bool = False
    routines: int = 0
    wearoff_msg: str = ""
    class_levels: dict[int, int] = field(default_factory=dict)
    extensions: dict[str, Any] = field(default_factory=dict)


# ── Race ───────────────────────────────────────────────────────────────

@dataclass
class Race:
    id: int = 0
    name: str = ""
    abbreviation: str = ""
    stat_modifiers: dict[str, int] = field(default_factory=dict)
    allowed_classes: list[int] = field(default_factory=list)
    extensions: dict[str, Any] = field(default_factory=dict)


# ── Top-level UIR ───────────────────────────────────────────────────────

@dataclass
class UIR:
    uir_version: str = "1.0"
    source_mud: SourceMudInfo | None = None
    metadata: GameMetadata = field(default_factory=GameMetadata)
    migration_stats: MigrationStats = field(default_factory=MigrationStats)
    rooms: list[Room] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)
    monsters: list[Monster] = field(default_factory=list)
    character_classes: list[CharacterClass] = field(default_factory=list)
    combat_system: CombatSystem = field(default_factory=CombatSystem)
    commands: list[Command] = field(default_factory=list)
    zones: list[Zone] = field(default_factory=list)
    shops: list[Shop] = field(default_factory=list)
    triggers: list[Trigger] = field(default_factory=list)
    quests: list[Quest] = field(default_factory=list)
    socials: list[Social] = field(default_factory=list)
    help_entries: list[HelpEntry] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    races: list[Race] = field(default_factory=list)
    extensions: dict[str, Any] = field(default_factory=dict)
