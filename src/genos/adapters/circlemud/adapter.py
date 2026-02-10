"""CircleMUD/tbaMUD adapter - orchestrates all parsers into a UIR."""

from __future__ import annotations

import logging
from pathlib import Path

from genos.adapters.base import AnalysisReport, BaseAdapter
from genos.adapters.detector import register_adapter
from genos.uir.schema import (
    CharacterClass,
    CombatSystem,
    GameMetadata,
    MigrationStats,
    SourceMudInfo,
    UIR,
)

from .cmd_parser import parse_cmd_file
from .help_parser import parse_help_dir
from .mob_parser import parse_mob_file
from .obj_parser import parse_obj_file
from .qst_parser import parse_qst_file
from .shp_parser import parse_shp_file
from .skill_parser import parse_skills
from .social_parser import parse_social_file
from .trg_parser import parse_trg_file
from .wld_parser import parse_wld_file
from .zon_parser import parse_zon_file

logger = logging.getLogger(__name__)


@register_adapter
class CircleMudAdapter(BaseAdapter):
    """Adapter for CircleMUD / tbaMUD codebases."""

    def __init__(self, source_path: str | Path) -> None:
        super().__init__(source_path)
        self._world_dir = self.source_path / "lib" / "world"

    def detect(self) -> bool:
        """Detect CircleMUD by looking for lib/world/ structure."""
        if not self._world_dir.is_dir():
            return False
        # Check for at least wld and mob directories
        return (
            (self._world_dir / "wld").is_dir()
            and (self._world_dir / "mob").is_dir()
        )

    def analyze(self) -> AnalysisReport:
        """Quick scan to count entities without full parsing."""
        report = AnalysisReport(
            mud_type="CircleMUD/tbaMUD",
            source_path=str(self.source_path),
        )

        report.room_count = self._count_entries("wld")
        report.item_count = self._count_entries("obj")
        report.mob_count = self._count_entries("mob")
        report.zone_count = len(self._get_data_files("zon"))
        report.shop_count = self._count_shop_entries()
        report.trigger_count = self._count_entries("trg")
        report.quest_count = self._count_entries("qst")

        # Phase 2 counts
        report.social_count = self._count_socials()
        report.help_count = self._count_help_entries()
        report.command_count = self._count_commands()
        report.skill_count = self._count_skill_defines()

        total = (
            report.room_count + report.item_count + report.mob_count
            + report.zone_count + report.shop_count
            + report.trigger_count + report.quest_count
        )
        supported = (
            report.room_count + report.item_count + report.mob_count
            + report.zone_count + report.shop_count + report.trigger_count
            + report.quest_count
        )
        report.estimated_conversion_rate = supported / total if total > 0 else 0.0

        return report

    def parse(self) -> UIR:
        """Parse all CircleMUD data files into a UIR."""
        uir = UIR()
        uir.source_mud = SourceMudInfo(
            name="tbaMUD",
            version="unknown",
            codebase="CircleMUD",
            source_path=str(self.source_path),
        )

        stats = MigrationStats()

        # Parse each data type
        uir.rooms = self._parse_all("wld", parse_wld_file, stats)
        uir.items = self._parse_all("obj", parse_obj_file, stats)
        uir.monsters = self._parse_all("mob", parse_mob_file, stats)
        uir.zones = self._parse_all("zon", parse_zon_file, stats)
        uir.triggers = self._parse_all("trg", parse_trg_file, stats)
        uir.shops = self._parse_all("shp", parse_shp_file, stats)
        uir.quests = self._parse_all("qst", parse_qst_file, stats)

        # Phase 2: extended data
        uir.socials = self._parse_socials(stats)
        uir.help_entries = self._parse_help(stats)
        uir.commands = self._parse_commands(stats)
        uir.skills = self._parse_skills(stats)

        # Set stats
        stats.total_rooms = len(uir.rooms)
        stats.total_items = len(uir.items)
        stats.total_monsters = len(uir.monsters)
        stats.total_zones = len(uir.zones)
        stats.total_shops = len(uir.shops)
        stats.total_triggers = len(uir.triggers)
        stats.total_quests = len(uir.quests)
        stats.total_socials = len(uir.socials)
        stats.total_help_entries = len(uir.help_entries)
        stats.total_commands = len(uir.commands)
        stats.total_skills = len(uir.skills)
        uir.migration_stats = stats

        # Add standard CircleMUD classes
        uir.character_classes = _default_classes()

        # Combat system
        uir.combat_system = CombatSystem(
            type="thac0",
            parameters={"base_thac0": 20, "ac_range": [-10, 10]},
            damage_types=[
                "hit", "sting", "whip", "slash", "bite", "bludgeon",
                "crush", "pound", "claw", "maul", "thrash", "pierce",
                "blast", "punch", "stab",
            ],
        )

        # Metadata
        uir.metadata = GameMetadata(
            game_name="tbaMUD",
            num_classes=4,
            num_directions=10,
            num_item_types=24,
            num_equip_slots=18,
        )

        return uir

    # ── Internals ───────────────────────────────────────────────────────

    def _get_data_files(self, subdir: str) -> list[Path]:
        """Get all data files in a world sub-directory, sorted."""
        data_dir = self._world_dir / subdir
        if not data_dir.is_dir():
            return []
        ext = f".{subdir}"
        files = sorted(data_dir.glob(f"*{ext}"))
        return files

    def _parse_all(self, subdir, parser_func, stats):
        """Parse all files in a sub-directory using the given parser."""
        results = []
        for fpath in self._get_data_files(subdir):
            try:
                items = parser_func(fpath)
                results.extend(items)
            except Exception as e:
                msg = f"Error parsing {fpath}: {e}"
                logger.warning(msg)
                stats.warnings.append(msg)
        return results

    def _count_entries(self, subdir: str) -> int:
        """Count #vnum entries across all files in a sub-directory."""
        count = 0
        for fpath in self._get_data_files(subdir):
            try:
                text = fpath.read_text(encoding="utf-8", errors="replace")
                for line in text.split("\n"):
                    stripped = line.strip()
                    if stripped.startswith("#") and not stripped.startswith("#$"):
                        vnum_part = stripped[1:]
                        if vnum_part and not vnum_part.startswith("$"):
                            try:
                                int(vnum_part.rstrip("~").strip())
                                count += 1
                            except ValueError:
                                pass
            except Exception:
                pass
        return count

    def _count_shop_entries(self) -> int:
        """Count shop entries (format differs: #<vnum>~)."""
        count = 0
        for fpath in self._get_data_files("shp"):
            try:
                text = fpath.read_text(encoding="utf-8", errors="replace")
                for line in text.split("\n"):
                    stripped = line.strip()
                    if stripped.startswith("#") and stripped.endswith("~"):
                        vnum_str = stripped[1:-1].strip()
                        if vnum_str and not vnum_str.startswith("$"):
                            try:
                                int(vnum_str)
                                count += 1
                            except ValueError:
                                pass
            except Exception:
                pass
        return count

    # ── Phase 2 parsing ──────────────────────────────────────────────

    def _parse_socials(self, stats):
        """Parse socials from lib/misc/socials."""
        socials_file = self.source_path / "lib" / "misc" / "socials"
        if not socials_file.exists():
            return []
        try:
            return parse_social_file(socials_file)
        except Exception as e:
            msg = f"Error parsing socials: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _parse_help(self, stats):
        """Parse help entries from lib/text/help/."""
        help_dir = self.source_path / "lib" / "text" / "help"
        if not help_dir.is_dir():
            return []
        try:
            return parse_help_dir(help_dir)
        except Exception as e:
            msg = f"Error parsing help: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _parse_commands(self, stats):
        """Parse commands from src/interpreter.c."""
        interp_file = self.source_path / "src" / "interpreter.c"
        if not interp_file.exists():
            return []
        try:
            return parse_cmd_file(interp_file, has_min_match=True)
        except Exception as e:
            msg = f"Error parsing commands: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _parse_skills(self, stats):
        """Parse skills from src/ (spells.h + spell_parser.c + class.c)."""
        src_dir = self.source_path / "src"
        if not src_dir.is_dir():
            return []
        try:
            return parse_skills(src_dir, has_spell_name=True)
        except Exception as e:
            msg = f"Error parsing skills: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    # ── Phase 2 analysis counts ──────────────────────────────────────

    def _count_socials(self) -> int:
        """Count socials in lib/misc/socials."""
        socials_file = self.source_path / "lib" / "misc" / "socials"
        if not socials_file.exists():
            return 0
        try:
            text = socials_file.read_text(encoding="utf-8", errors="replace")
            count = 0
            for line in text.split("\n"):
                parts = line.strip().split()
                if len(parts) == 3 and line[0].isalpha():
                    try:
                        int(parts[1])
                        int(parts[2])
                        count += 1
                    except ValueError:
                        pass
            return count
        except Exception:
            return 0

    def _count_help_entries(self) -> int:
        """Count help entries in lib/text/help/."""
        help_dir = self.source_path / "lib" / "text" / "help"
        if not help_dir.is_dir():
            return 0
        try:
            entries = parse_help_dir(help_dir)
            return len(entries)
        except Exception:
            return 0

    def _count_commands(self) -> int:
        """Count commands in src/interpreter.c."""
        interp_file = self.source_path / "src" / "interpreter.c"
        if not interp_file.exists():
            return 0
        try:
            import re
            text = interp_file.read_text(encoding="utf-8", errors="replace")
            return len(re.findall(r'\{\s*"[^"]+"\s*,', text))
        except Exception:
            return 0

    def _count_skill_defines(self) -> int:
        """Count SPELL_* and SKILL_* defines in src/spells.h."""
        spells_h = self.source_path / "src" / "spells.h"
        if not spells_h.exists():
            return 0
        try:
            import re
            text = spells_h.read_text(encoding="utf-8", errors="replace")
            return len(re.findall(
                r'#define\s+(?:SPELL|SKILL)_(?!RESERVED|TYPE|DG)\w+\s+\d+', text
            ))
        except Exception:
            return 0


def _default_classes() -> list[CharacterClass]:
    """Return the 4 standard CircleMUD character classes."""
    return [
        CharacterClass(
            id=0, name="Magic User", abbreviation="Mu",
            hp_gain_min=3, hp_gain_max=8,
            mana_gain_min=5, mana_gain_max=10,
            extensions={"base_thac0": 20, "thac0_gain": 0.66},
        ),
        CharacterClass(
            id=1, name="Cleric", abbreviation="Cl",
            hp_gain_min=5, hp_gain_max=10,
            mana_gain_min=3, mana_gain_max=8,
            extensions={"base_thac0": 20, "thac0_gain": 0.66},
        ),
        CharacterClass(
            id=2, name="Thief", abbreviation="Th",
            hp_gain_min=6, hp_gain_max=11,
            extensions={"base_thac0": 20, "thac0_gain": 0.75},
        ),
        CharacterClass(
            id=3, name="Warrior", abbreviation="Wa",
            hp_gain_min=10, hp_gain_max=15,
            extensions={"base_thac0": 20, "thac0_gain": 1.0},
        ),
    ]
