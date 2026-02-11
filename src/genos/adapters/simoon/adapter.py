"""Simoon (CircleMUD 3.0 Korean custom) adapter."""

from __future__ import annotations

import logging
from pathlib import Path

from genos.adapters.base import AnalysisReport, BaseAdapter
from genos.adapters.detector import register_adapter
from genos.adapters.circlemud.skill_parser import parse_skills
from genos.adapters.circlemud.social_parser import parse_social_file
from genos.uir.schema import (
    CharacterClass,
    CombatSystem,
    GameMetadata,
    MigrationStats,
    Race,
    SourceMudInfo,
    UIR,
)

from .cmd_parser import parse_cmd_file
from .config_parser import (
    parse_attribute_modifiers,
    parse_game_config,
    parse_practice_params,
    parse_simoon_titles,
    parse_train_params,
)
from .help_parser import parse_help_dir
from .mob_parser import parse_mob_file
from .obj_parser import parse_obj_file
from .qst_parser import parse_qst_file
from .shp_parser import parse_shp_file
from .wld_parser import parse_wld_file
from .zon_parser import parse_zon_file

logger = logging.getLogger(__name__)

_ENCODING = "euc-kr"


def _read_euckr(filepath: Path) -> str:
    """Read a file with EUC-KR encoding."""
    return filepath.read_text(encoding=_ENCODING, errors="replace")


@register_adapter
class SimoonAdapter(BaseAdapter):
    """Adapter for Simoon (CircleMUD 3.0 Korean custom) codebases."""

    def __init__(self, source_path: str | Path) -> None:
        super().__init__(source_path)
        self._world_dir = self.source_path / "lib" / "world"

    def detect(self) -> bool:
        """Detect Simoon by checking for HANGUL.TXT + CircleMUD world structure."""
        if not self._world_dir.is_dir():
            return False
        has_dirs = (
            (self._world_dir / "wld").is_dir()
            and (self._world_dir / "mob").is_dir()
        )
        if not has_dirs:
            return False
        # Simoon-specific: HANGUL.TXT in the root
        return (self.source_path / "HANGUL.TXT").exists()

    def analyze(self) -> AnalysisReport:
        """Quick scan to count entities without full parsing."""
        report = AnalysisReport(
            mud_type="Simoon (CircleMUD 3.0 Korean)",
            source_path=str(self.source_path),
        )

        report.room_count = self._count_entries("wld")
        report.item_count = self._count_entries("obj")
        report.mob_count = self._count_entries("mob")
        report.zone_count = len(self._get_data_files("zon"))
        report.shop_count = self._count_shop_entries()
        report.quest_count = self._count_entries("qst")

        # Phase 2 counts
        report.social_count = self._count_socials()
        report.help_count = self._count_help_entries()
        report.command_count = self._count_commands()
        report.skill_count = self._count_skill_defines()
        report.race_count = 5  # Simoon hardcoded races

        total = (
            report.room_count + report.item_count + report.mob_count
            + report.zone_count + report.shop_count + report.quest_count
        )
        report.estimated_conversion_rate = 1.0 if total > 0 else 0.0

        return report

    def parse(self) -> UIR:
        """Parse all Simoon data files into a UIR."""
        uir = UIR()
        uir.source_mud = SourceMudInfo(
            name="Simoon",
            version="unknown",
            codebase="CircleMUD 3.0",
            source_path=str(self.source_path),
        )

        stats = MigrationStats()

        uir.rooms = self._parse_all("wld", parse_wld_file, stats)
        uir.items = self._parse_all("obj", parse_obj_file, stats)
        uir.monsters = self._parse_all("mob", parse_mob_file, stats)
        uir.zones = self._parse_all("zon", parse_zon_file, stats)
        uir.shops = self._parse_all("shp", parse_shp_file, stats)
        uir.quests = self._parse_all("qst", parse_qst_file, stats)

        # Phase 2: extended data
        uir.socials = self._parse_socials(stats)
        uir.help_entries = self._parse_help(stats)
        uir.commands = self._parse_commands(stats)
        uir.skills = self._parse_skills(stats)
        uir.races = _default_races()

        # Phase 3: game system config
        uir.game_configs = self._parse_game_config(stats)
        uir.attribute_modifiers = self._parse_attribute_modifiers(stats)
        uir.practice_params = self._parse_practice_params(stats)
        titles, exp_entries = self._parse_titles_and_exp(stats)
        uir.level_titles = titles
        uir.experience_table = exp_entries
        # Merge train_params into practice_params extensions
        train = self._parse_train_params(stats)
        for tp in train:
            for pp in uir.practice_params:
                if pp.class_id == tp.class_id:
                    pp.extensions.update(tp.extensions)
                    break

        stats.total_rooms = len(uir.rooms)
        stats.total_items = len(uir.items)
        stats.total_monsters = len(uir.monsters)
        stats.total_zones = len(uir.zones)
        stats.total_shops = len(uir.shops)
        stats.total_triggers = 0
        stats.total_quests = len(uir.quests)
        stats.total_socials = len(uir.socials)
        stats.total_help_entries = len(uir.help_entries)
        stats.total_commands = len(uir.commands)
        stats.total_skills = len(uir.skills)
        stats.total_races = len(uir.races)
        stats.total_game_configs = len(uir.game_configs)
        stats.total_exp_entries = len(uir.experience_table)
        stats.total_level_titles = len(uir.level_titles)
        stats.total_attribute_modifiers = len(uir.attribute_modifiers)
        uir.migration_stats = stats

        uir.character_classes = _simoon_classes()

        uir.combat_system = CombatSystem(
            type="thac0",
            parameters={"base_thac0": 20, "ac_range": [-10, 10]},
            damage_types=[
                "hit", "sting", "whip", "slash", "bite", "bludgeon",
                "crush", "pound", "claw", "maul", "thrash", "pierce",
                "blast", "punch", "stab",
            ],
        )

        uir.metadata = GameMetadata(
            game_name="Simoon",
            num_classes=7,
            num_directions=6,
            num_item_types=24,
            num_equip_slots=18,
        )

        return uir

    # ── Internals ───────────────────────────────────────────────────────

    def _get_data_files(self, subdir: str) -> list[Path]:
        """Get data files listed in the index file for a world sub-directory.

        CircleMUD/Simoon uses an 'index' file in each world sub-directory
        to list which data files should be loaded. Files on disk but not
        in the index (e.g. orphaned backups) are excluded.
        """
        data_dir = self._world_dir / subdir
        if not data_dir.is_dir():
            return []
        index_file = data_dir / "index"
        if index_file.exists():
            files = []
            seen: set[str] = set()
            for line in _read_euckr(index_file).splitlines():
                fname = line.strip()
                if not fname or fname.startswith("$"):
                    break
                if fname in seen:
                    continue
                seen.add(fname)
                fpath = data_dir / fname
                if fpath.is_file():
                    files.append(fpath)
            return files
        # Fallback: glob all matching files if no index exists
        ext = f".{subdir}"
        return sorted(data_dir.glob(f"*{ext}"))

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
                text = _read_euckr(fpath)
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
        """Count shop entries (format: #<vnum>~)."""
        count = 0
        for fpath in self._get_data_files("shp"):
            try:
                text = _read_euckr(fpath)
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
        """Parse socials from lib/misc/socials (EUC-KR)."""
        socials_file = self.source_path / "lib" / "misc" / "socials"
        if not socials_file.exists():
            return []
        try:
            return parse_social_file(socials_file, encoding=_ENCODING)
        except Exception as e:
            msg = f"Error parsing socials: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _parse_help(self, stats):
        """Parse help entries from lib/text/help/ (EUC-KR)."""
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
        """Parse commands from src/interpreter.c (EUC-KR, no min_match)."""
        interp_file = self.source_path / "src" / "interpreter.c"
        if not interp_file.exists():
            return []
        try:
            return parse_cmd_file(interp_file)
        except Exception as e:
            msg = f"Error parsing commands: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _parse_skills(self, stats):
        """Parse skills from src/ (EUC-KR, no spell name in spello)."""
        src_dir = self.source_path / "src"
        if not src_dir.is_dir():
            return []
        try:
            return parse_skills(
                src_dir, encoding=_ENCODING, has_spell_name=False,
            )
        except Exception as e:
            msg = f"Error parsing skills: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    # ── Phase 3 parsing ───────────────────────────────────────────────

    def _parse_game_config(self, stats):
        src_dir = self.source_path / "src"
        if not src_dir.is_dir():
            return []
        try:
            return parse_game_config(src_dir)
        except Exception as e:
            msg = f"Error parsing game config: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _parse_attribute_modifiers(self, stats):
        src_dir = self.source_path / "src"
        if not src_dir.is_dir():
            return []
        try:
            return parse_attribute_modifiers(src_dir)
        except Exception as e:
            msg = f"Error parsing attribute modifiers: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _parse_practice_params(self, stats):
        src_dir = self.source_path / "src"
        if not src_dir.is_dir():
            return []
        try:
            return parse_practice_params(src_dir)
        except Exception as e:
            msg = f"Error parsing practice params: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return []

    def _parse_titles_and_exp(self, stats):
        src_dir = self.source_path / "src"
        if not src_dir.is_dir():
            return [], []
        try:
            return parse_simoon_titles(src_dir)
        except Exception as e:
            msg = f"Error parsing titles/exp: {e}"
            logger.warning(msg)
            stats.warnings.append(msg)
            return [], []

    def _parse_train_params(self, stats):
        src_dir = self.source_path / "src"
        if not src_dir.is_dir():
            return []
        try:
            return parse_train_params(src_dir)
        except Exception as e:
            msg = f"Error parsing train params: {e}"
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
            text = _read_euckr(socials_file)
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
            return len(parse_help_dir(help_dir))
        except Exception:
            return 0

    def _count_commands(self) -> int:
        """Count commands in src/interpreter.c."""
        interp_file = self.source_path / "src" / "interpreter.c"
        if not interp_file.exists():
            return 0
        try:
            import re
            text = _read_euckr(interp_file)
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
            text = _read_euckr(spells_h)
            return len(re.findall(
                r'#define\s+(?:SPELL|SKILL)_(?!RESERVED|TYPE|DG)\w+\s+\d+', text
            ))
        except Exception:
            return 0


def _simoon_classes() -> list[CharacterClass]:
    """Return the 7 Simoon character classes (4 base + 3 extended)."""
    return [
        CharacterClass(
            id=0, name="Magic User", abbreviation="Mu",
            hp_gain_min=3, hp_gain_max=8,
            mana_gain_min=5, mana_gain_max=10,
            extensions={"base_thac0": 20, "thac0_gain": 0.66,
                         "korean_name": "\ub9c8\ubc95\uc0ac"},
        ),
        CharacterClass(
            id=1, name="Cleric", abbreviation="Cl",
            hp_gain_min=5, hp_gain_max=10,
            mana_gain_min=3, mana_gain_max=8,
            extensions={"base_thac0": 20, "thac0_gain": 0.66,
                         "korean_name": "\uc131\uc9c1\uc790"},
        ),
        CharacterClass(
            id=2, name="Thief", abbreviation="Th",
            hp_gain_min=6, hp_gain_max=11,
            extensions={"base_thac0": 20, "thac0_gain": 0.75,
                         "korean_name": "\ub3c4\uc801"},
        ),
        CharacterClass(
            id=3, name="Warrior", abbreviation="Wa",
            hp_gain_min=10, hp_gain_max=15,
            extensions={"base_thac0": 20, "thac0_gain": 1.0,
                         "korean_name": "\uc804\uc0ac"},
        ),
        CharacterClass(
            id=4, name="Dark Mage", abbreviation="Dk",
            hp_gain_min=3, hp_gain_max=8,
            mana_gain_min=5, mana_gain_max=10,
            extensions={"base_thac0": 20, "thac0_gain": 0.66,
                         "korean_name": "\ud751\ub9c8\ubc95\uc0ac"},
        ),
        CharacterClass(
            id=5, name="Berserker", abbreviation="Be",
            hp_gain_min=12, hp_gain_max=18,
            extensions={"base_thac0": 20, "thac0_gain": 1.0,
                         "korean_name": "\uad11\uc804\uc0ac"},
        ),
        CharacterClass(
            id=6, name="Summoner", abbreviation="Su",
            hp_gain_min=4, hp_gain_max=9,
            mana_gain_min=4, mana_gain_max=9,
            extensions={"base_thac0": 20, "thac0_gain": 0.66,
                         "korean_name": "\uc18c\ud658\uc0ac"},
        ),
    ]


def _default_races() -> list[Race]:
    """Return the 5 Simoon races."""
    return [
        Race(
            id=0, name="Human", abbreviation="Hu",
            stat_modifiers={"charisma": 3},
            allowed_classes=[0, 1, 2, 3, 4, 5, 6],
            extensions={"korean_name": "\uc778\uac04"},
        ),
        Race(
            id=1, name="Dwarf", abbreviation="Dw",
            stat_modifiers={"strength": 2, "constitution": 1, "dexterity": -1},
            allowed_classes=[1, 2, 3, 5],
            extensions={"korean_name": "\ub4dc\uc6cc\ud504"},
        ),
        Race(
            id=2, name="Elf", abbreviation="El",
            stat_modifiers={"strength": -1, "dexterity": 2, "intelligence": 2,
                            "charisma": 3},
            allowed_classes=[0, 1, 2, 4, 6],
            extensions={"korean_name": "\uc5d8\ud504"},
        ),
        Race(
            id=3, name="Hobbit", abbreviation="Ho",
            stat_modifiers={"strength": -1, "dexterity": 1},
            allowed_classes=[1, 2, 3],
            extensions={"korean_name": "\ud638\ube57"},
        ),
        Race(
            id=4, name="Half-Elf", abbreviation="He",
            stat_modifiers={},
            allowed_classes=[0, 1, 2, 3, 4, 5, 6],
            extensions={"korean_name": "\ud558\ud504\uc5d8\ud504"},
        ),
    ]
