"""3eyes MUD adapter — binary C struct format.

3eyes is a Korean custom MUD based on Mordor/CircleMUD lineage.
Unlike text-based CircleMUD formats, 3eyes stores all game data
as raw C struct binary files.

Directory structure:
  rooms/r{nn}/r{nnnnn}  — individual room binary files
  objmon/o{nn}           — object files (100 records × 352 bytes)
  objmon/m{nn}           — monster files (100 records × 1184 bytes)
  objmon/talk/{name}-{level}  — monster talk text files
  objmon/ddesc/{name}_{level} — monster detailed descriptions
  help/help.{n}          — help text files
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.adapters.base import AnalysisReport, BaseAdapter
from genos.adapters.detector import register_adapter
from genos.uir.schema import (
    CharacterClass,
    CombatSystem,
    GameMetadata,
    HelpEntry,
    MigrationStats,
    Monster,
    Race,
    Skill,
    SourceMudInfo,
    UIR,
)

from .constants import CLASSES, RACES, SIZEOF_CREATURE, SIZEOF_OBJECT, RECORDS_PER_FILE, SPELL_NAMES
from .help_parser import parse_all_help
from .mob_parser import parse_all_monsters
from .obj_parser import parse_all_objects
from .room_parser import parse_all_rooms
from .talk_parser import (
    load_all_ddescs,
    load_all_talks,
    parse_ddesc_filename,
    parse_talk_filename,
)

logger = logging.getLogger(__name__)


@register_adapter
class ThreeEyesAdapter(BaseAdapter):
    """Adapter for 3eyes MUD (binary C struct format)."""

    def __init__(self, source_path: str | Path) -> None:
        super().__init__(source_path)
        self._rooms_dir = self.source_path / "rooms"
        self._objmon_dir = self.source_path / "objmon"
        self._help_dir = self.source_path / "help"

    def detect(self) -> bool:
        """Detect 3eyes by checking for its unique directory structure.

        3eyes has: rooms/r{nn}/r{nnnnn} + objmon/m{nn} + objmon/o{nn}.
        This pattern is unique — no other MUD uses numbered binary room files.
        """
        if not self._rooms_dir.is_dir():
            return False
        if not self._objmon_dir.is_dir():
            return False

        # Check for room subdirectories
        has_room_dirs = any(self._rooms_dir.glob("r[0-9][0-9]"))
        if not has_room_dirs:
            return False

        # Check for monster/object binary files with correct size
        has_monsters = any(self._objmon_dir.glob("m[0-9][0-9]"))
        has_objects = any(self._objmon_dir.glob("o[0-9][0-9]"))
        if not (has_monsters and has_objects):
            return False

        # Verify at least one file's size is a multiple of the record size
        for mfile in sorted(self._objmon_dir.glob("m[0-9][0-9]")):
            size = mfile.stat().st_size
            if size > 0 and size % SIZEOF_CREATURE == 0:
                return True

        return False

    def analyze(self) -> AnalysisReport:
        """Quick analysis without full parsing."""
        report = AnalysisReport(
            mud_type="3eyes MUD (Binary C Struct)",
            source_path=str(self.source_path),
        )

        # Count rooms
        report.room_count = sum(
            1
            for zone_dir in self._rooms_dir.glob("r[0-9][0-9]")
            if zone_dir.is_dir()
            for _ in zone_dir.glob("r[0-9][0-9][0-9][0-9][0-9]")
        )

        # Count objects (non-empty records)
        report.item_count = self._count_binary_records(
            "o", SIZEOF_OBJECT,
        )

        # Count monsters (non-empty records with type==MONSTER)
        report.mob_count = self._count_binary_records(
            "m", SIZEOF_CREATURE,
        )

        # Zones = number of room subdirectories
        report.zone_count = sum(
            1
            for d in self._rooms_dir.glob("r[0-9][0-9]")
            if d.is_dir()
        )

        # Help entries
        report.help_count = sum(1 for _ in self._help_dir.glob("help.*"))

        # Race/class counts (hardcoded)
        report.race_count = len(RACES)
        report.skill_count = len(SPELL_NAMES)

        total = (
            report.room_count + report.item_count + report.mob_count
        )
        report.estimated_conversion_rate = 1.0 if total > 0 else 0.0

        return report

    def parse(self) -> UIR:
        """Parse all 3eyes data into a UIR."""
        uir = UIR()
        uir.source_mud = SourceMudInfo(
            name="3eyes",
            version="unknown",
            codebase="Mordor (CircleMUD variant)",
            source_path=str(self.source_path),
        )

        stats = MigrationStats()

        # Core data
        uir.rooms = self._parse_rooms(stats)
        uir.items = self._parse_objects(stats)
        uir.monsters = self._parse_monsters(stats)

        # Merge talk/ddesc files into monsters
        self._merge_talk_files(uir.monsters)

        # Help entries
        uir.help_entries = self._parse_help(stats)

        # Hardcoded data
        uir.character_classes = _threeeyes_classes()
        uir.races = _threeeyes_races()
        uir.skills = _threeeyes_spells()

        # Stats
        stats.total_rooms = len(uir.rooms)
        stats.total_items = len(uir.items)
        stats.total_monsters = len(uir.monsters)
        stats.total_zones = len({r.zone_number for r in uir.rooms})
        stats.total_help_entries = len(uir.help_entries)
        stats.total_skills = len(uir.skills)
        stats.total_races = len(uir.races)
        uir.migration_stats = stats

        uir.combat_system = CombatSystem(
            type="thac0",
            parameters={"base_thac0": 20, "ac_range": [-10, 10]},
            damage_types=[
                "hit", "slash", "crush", "pierce", "pound",
                "claw", "maul", "bite",
            ],
        )

        uir.metadata = GameMetadata(
            game_name="3eyes",
            num_classes=len(CLASSES),
            num_directions=6,
            num_item_types=15,
            num_equip_slots=20,
        )

        return uir

    # ── Parse helpers ──────────────────────────────────────────────

    def _parse_rooms(self, stats: MigrationStats) -> list:
        try:
            return parse_all_rooms(self._rooms_dir)
        except Exception as e:
            msg = f"Error parsing rooms: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _parse_objects(self, stats: MigrationStats) -> list:
        try:
            return parse_all_objects(self._objmon_dir)
        except Exception as e:
            msg = f"Error parsing objects: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _parse_monsters(self, stats: MigrationStats) -> list:
        try:
            return parse_all_monsters(self._objmon_dir)
        except Exception as e:
            msg = f"Error parsing monsters: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _parse_help(self, stats: MigrationStats) -> list[HelpEntry]:
        try:
            return parse_all_help(self._help_dir)
        except Exception as e:
            msg = f"Error parsing help: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _merge_talk_files(self, monsters: list[Monster]) -> None:
        """Merge talk and ddesc files into parsed monsters."""
        talk_dir = self._objmon_dir / "talk"
        ddesc_dir = self._objmon_dir / "ddesc"

        talks = load_all_talks(talk_dir)
        ddescs = load_all_ddescs(ddesc_dir)

        # Build lookup: (name, level) → monster
        mob_lookup: dict[tuple[str, int], Monster] = {}
        for m in monsters:
            mob_lookup[(m.short_description, m.level)] = m

        # Merge talk files
        for filename, talk_dict in talks.items():
            name, level = parse_talk_filename(filename)
            mob = mob_lookup.get((name, level))
            if mob is not None:
                mob.extensions["talk_responses"] = talk_dict
            else:
                logger.debug("No monster match for talk file: %s", filename)

        # Merge ddesc files
        for filename, desc in ddescs.items():
            name, level = parse_ddesc_filename(filename)
            # ddesc uses underscore separators in name
            name_display = name.replace("_", " ")
            mob = mob_lookup.get((name_display, level))
            if mob is None:
                # Try with original name (underscores kept)
                mob = mob_lookup.get((name, level))
            if mob is not None:
                mob.detailed_description = desc
            else:
                logger.debug("No monster match for ddesc file: %s", filename)

    def _count_binary_records(
        self, prefix: str, record_size: int,
    ) -> int:
        """Count non-empty records in binary files."""
        count = 0
        for fpath in self._objmon_dir.glob(f"{prefix}[0-9][0-9]"):
            try:
                data = fpath.read_bytes()
                n_records = min(len(data) // record_size, RECORDS_PER_FILE)
                for i in range(n_records):
                    offset = i * record_size
                    # Check if name field (first bytes) is non-empty
                    if prefix == "m":
                        # Monster: type at offset 3 must be MONSTER(1)
                        # name at offset 44
                        if data[offset + 3] != 1:
                            continue
                        if data[offset + 44 : offset + 124].rstrip(b"\x00"):
                            count += 1
                    else:
                        # Object: name at offset 0
                        if data[offset : offset + 70].rstrip(b"\x00"):
                            count += 1
            except Exception:
                pass
        return count


def _threeeyes_classes() -> list[CharacterClass]:
    """Return the 8 player classes from 3eyes."""
    # Based on class_stats arrays in the C source
    class_data = [
        (1, "Assassin", "As", 8, 12, 2, 6),
        (2, "Barbarian", "Ba", 12, 18, 0, 0),
        (3, "Cleric", "Cl", 6, 10, 4, 8),
        (4, "Fighter", "Fi", 10, 15, 0, 0),
        (5, "Mage", "Ma", 4, 8, 6, 12),
        (6, "Paladin", "Pa", 8, 14, 2, 6),
        (7, "Ranger", "Ra", 9, 14, 1, 4),
        (8, "Thief", "Th", 7, 11, 1, 3),
    ]
    return [
        CharacterClass(
            id=cid,
            name=name,
            abbreviation=abbr,
            hp_gain_min=hp_min,
            hp_gain_max=hp_max,
            mana_gain_min=mp_min,
            mana_gain_max=mp_max,
        )
        for cid, name, abbr, hp_min, hp_max, mp_min, mp_max in class_data
    ]


def _threeeyes_races() -> list[Race]:
    """Return the 8 player races from 3eyes."""
    race_data = [
        (1, "Dwarf", "Dw", {"strength": 2, "constitution": 1, "intelligence": -1}),
        (2, "Elf", "El", {"dexterity": 2, "intelligence": 1, "constitution": -1}),
        (3, "Half-Elf", "He", {"dexterity": 1, "intelligence": 1}),
        (4, "Hobbit", "Ho", {"dexterity": 2, "strength": -1}),
        (5, "Human", "Hu", {}),
        (6, "Orc", "Or", {"strength": 2, "constitution": 1, "intelligence": -2}),
        (7, "Half-Giant", "Hg", {"strength": 3, "constitution": 2, "intelligence": -2, "dexterity": -1}),
        (8, "Gnome", "Gn", {"intelligence": 2, "dexterity": 1, "strength": -1}),
    ]
    return [
        Race(
            id=rid,
            name=name,
            abbreviation=abbr,
            stat_modifiers=mods,
            allowed_classes=list(range(1, 9)),
        )
        for rid, name, abbr, mods in race_data
    ]


def _threeeyes_spells() -> list[Skill]:
    """Return spell definitions from SPELL_NAMES constants."""
    return [
        Skill(
            id=spell_id,
            name=name,
            spell_type="spell",
        )
        for spell_id, name in sorted(SPELL_NAMES.items())
    ]
