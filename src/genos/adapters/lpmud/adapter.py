"""LP-MUD/FluffOS adapter — LPC source file format.

Handles Korean LP-MUD games based on FluffOS/MudOS, where all game data
is defined as individual .c (LPC) source files with setXxx() calls.

Directory structure:
  lib/방/          — room .c files (subdirectories = zones)
  lib/물체/        — object/monster .c files
  lib/명령어/플레이어/ — player command .c files
  lib/도움말/       — .help files
  lib/삽입파일/     — header files (직업.h, 기술.h, etc.)
  lib/구조/         — library base classes (room.c, monster.c, etc.)
  bin/driver or bin/fluffos* — FluffOS driver binary
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.adapters.base import AnalysisReport, BaseAdapter
from genos.adapters.detector import register_adapter
from genos.uir.schema import (
    CombatSystem,
    GameMetadata,
    MigrationStats,
    SourceMudInfo,
    UIR,
    Zone,
    ZoneResetCommand,
)

from .class_parser import parse_classes
from .command_parser import parse_all_commands
from .config_parser import (
    parse_combat_header,
    parse_driver_config,
    parse_settings_header,
    parse_stat_formulas,
)
from .help_parser import parse_all_help
from .mob_parser import parse_all_monsters
from .obj_parser import parse_all_items
from .room_parser import parse_all_rooms, resolve_exits
from .skill_parser import parse_skills
from .vnum_generator import VnumGenerator

logger = logging.getLogger(__name__)

# Room directory names to scan (방, 방0~방5)
# Only use the primary "방" directory, skip backups (방0~방5)
ROOM_DIRS = ["방"]


@register_adapter
class LPMudAdapter(BaseAdapter):
    """Adapter for LP-MUD/FluffOS (LPC source code format)."""

    def __init__(self, source_path: str | Path) -> None:
        super().__init__(source_path)
        self._lib_dir = self.source_path / "lib"
        self._bin_dir = self.source_path / "bin"

    def detect(self) -> bool:
        """Detect LP-MUD by checking for FluffOS driver and LPC structure.

        Requires:
        1. bin/driver OR bin/fluffos* exists
        2. lib/구조/ OR lib/삽입파일/ directory exists
        3. At least one .c file with 'inherit LIB_' pattern in lib/
        """
        if not self._lib_dir.is_dir():
            return False

        # Check for driver binary
        has_driver = False
        if self._bin_dir.is_dir():
            has_driver = (
                (self._bin_dir / "driver").exists()
                or any(self._bin_dir.glob("fluffos*"))
            )

        if not has_driver:
            return False

        # Check for LPC structure directories
        has_structure = (
            (self._lib_dir / "구조").is_dir()
            or (self._lib_dir / "삽입파일").is_dir()
        )
        if not has_structure:
            return False

        # Check for LPC inherit pattern in at least one .c file
        for c_file in self._lib_dir.rglob("*.c"):
            try:
                raw = c_file.read_bytes()
                if b"inherit LIB_" in raw:
                    return True
            except Exception:
                continue
            # Only check first 20 files for speed
            break

        return True

    def analyze(self) -> AnalysisReport:
        """Quick analysis without full parsing."""
        report = AnalysisReport(
            mud_type="LP-MUD/FluffOS (LPC Source)",
            source_path=str(self.source_path),
        )

        # Count rooms (方/ only, excluding mob/ and obj/ subdirs)
        room_base = self._lib_dir / "방"
        if room_base.is_dir():
            report.room_count = sum(
                1 for f in room_base.rglob("*.c")
                if not any(p in f.relative_to(room_base).parts for p in ("mob", "obj"))
            )

        # Count mob files in 방/*/mob/ dirs
        if room_base.is_dir():
            report.mob_count = sum(
                1 for d in room_base.rglob("mob")
                if d.is_dir()
                for _ in d.glob("*.c")
            )

        # Count items in 물체/
        obj_dir = self._lib_dir / "물체"
        if obj_dir.is_dir():
            report.item_count = sum(1 for _ in obj_dir.rglob("*.c"))

        # Zone count = number of subdirectories in 방/
        if room_base.is_dir():
            report.zone_count = sum(
                1 for d in room_base.iterdir()
                if d.is_dir()
            )

        # Help count
        help_dir = self._lib_dir / "도움말"
        if help_dir.is_dir():
            report.help_count = sum(1 for _ in help_dir.glob("*.help"))

        # Command count
        cmd_dir = self._lib_dir / "명령어" / "플레이어"
        if cmd_dir.is_dir():
            report.command_count = sum(1 for _ in cmd_dir.glob("*.c"))

        # Skill count from header
        skill_header = self._lib_dir / "삽입파일" / "기술.h"
        if skill_header.exists():
            try:
                skills = parse_skills(skill_header)
                report.skill_count = len(skills)
            except Exception:
                pass

        # Class count from header
        class_header = self._lib_dir / "삽입파일" / "직업.h"
        if class_header.exists():
            try:
                classes = parse_classes(class_header)
                report.race_count = len(classes)  # Using race_count for classes
            except Exception:
                pass

        total = report.room_count + report.item_count + report.mob_count
        report.estimated_conversion_rate = 1.0 if total > 0 else 0.0

        return report

    def parse(self) -> UIR:
        """Parse all LP-MUD data into a UIR."""
        uir = UIR()
        uir.source_mud = SourceMudInfo(
            name="10woongi",
            version="FluffOS",
            codebase="LP-MUD (FluffOS/MudOS)",
            source_path=str(self.source_path),
        )

        stats = MigrationStats()
        vnum_gen = VnumGenerator()

        # Phase 1: Header files (classes, skills)
        uir.character_classes = self._parse_classes(stats)
        uir.skills = self._parse_skills(stats)

        # Phase 2: Rooms (2-pass for exit resolution)
        uir.rooms, pending_exits = self._parse_rooms(stats, vnum_gen)
        resolve_exits(uir.rooms, pending_exits, vnum_gen)

        # Phase 3: Monsters and Items
        uir.monsters = self._parse_monsters(stats, vnum_gen)
        uir.items = self._parse_items(stats, vnum_gen)

        # Phase 4: Help and Commands
        uir.help_entries = self._parse_help(stats)
        uir.commands = self._parse_commands(stats)

        # Phase 5: Infer zones from room directories
        uir.zones = self._infer_zones(uir.rooms, vnum_gen)

        # Phase 5b: Generate zone reset commands from room inventories
        self._build_reset_commands(uir, vnum_gen)

        # Phase 6: Game configuration (settings, driver config, combat, formulas)
        uir.game_configs = self._parse_configs(stats)

        # Stats
        stats.total_rooms = len(uir.rooms)
        stats.total_items = len(uir.items)
        stats.total_monsters = len(uir.monsters)
        stats.total_zones = len(uir.zones)
        stats.total_help_entries = len(uir.help_entries)
        stats.total_skills = len(uir.skills)
        stats.total_commands = len(uir.commands)
        stats.total_game_configs = len(uir.game_configs)
        uir.migration_stats = stats

        uir.combat_system = CombatSystem(
            type="stat_based",
            parameters={
                "stats": ["힘", "민첩", "지혜", "기골", "내공", "투지"],
                "damage_types": ["slash", "pierce", "bludgeon", "shoot"],
            },
            damage_types=["slash", "pierce", "bludgeon", "shoot"],
        )

        uir.metadata = GameMetadata(
            game_name="십웅이 (10woongi)",
            description="Korean wuxia LP-MUD",
            num_classes=len(uir.character_classes),
            num_directions=10,
            num_item_types=20,
            num_equip_slots=22,
        )

        # Store vnum path map in extensions for debugging
        uir.extensions["vnum_path_map_size"] = len(vnum_gen.get_path_map())

        return uir

    # ── Parse helpers ──────────────────────────────────────────────

    def _parse_classes(self, stats: MigrationStats) -> list:
        header = self._lib_dir / "삽입파일" / "직업.h"
        if not header.exists():
            return []
        try:
            return parse_classes(header)
        except Exception as e:
            stats.warnings.append(f"Error parsing classes: {e}")
            return []

    def _parse_skills(self, stats: MigrationStats) -> list:
        header = self._lib_dir / "삽입파일" / "기술.h"
        if not header.exists():
            return []
        try:
            return parse_skills(header)
        except Exception as e:
            stats.warnings.append(f"Error parsing skills: {e}")
            return []

    def _parse_rooms(self, stats: MigrationStats, vnum_gen: VnumGenerator) -> tuple:
        try:
            return parse_all_rooms(self._lib_dir, ROOM_DIRS, vnum_gen)
        except Exception as e:
            stats.warnings.append(f"Error parsing rooms: {e}")
            return [], {}

    def _parse_monsters(self, stats: MigrationStats, vnum_gen: VnumGenerator) -> list:
        try:
            return parse_all_monsters(self._lib_dir, ROOM_DIRS, vnum_gen)
        except Exception as e:
            stats.warnings.append(f"Error parsing monsters: {e}")
            return []

    def _parse_items(self, stats: MigrationStats, vnum_gen: VnumGenerator) -> list:
        try:
            return parse_all_items(self._lib_dir, ROOM_DIRS, vnum_gen)
        except Exception as e:
            stats.warnings.append(f"Error parsing items: {e}")
            return []

    def _parse_help(self, stats: MigrationStats) -> list:
        help_dir = self._lib_dir / "도움말"
        try:
            return parse_all_help(help_dir)
        except Exception as e:
            stats.warnings.append(f"Error parsing help: {e}")
            return []

    def _parse_commands(self, stats: MigrationStats) -> list:
        cmd_dir = self._lib_dir / "명령어" / "플레이어"
        try:
            return parse_all_commands(cmd_dir)
        except Exception as e:
            stats.warnings.append(f"Error parsing commands: {e}")
            return []

    def _parse_configs(self, stats: MigrationStats) -> list:
        """Parse game configuration from headers, driver config, and formulas."""
        configs = []

        # 세팅.h
        settings_h = self._lib_dir / "삽입파일" / "세팅.h"
        if settings_h.exists():
            try:
                configs.extend(parse_settings_header(settings_h))
            except Exception as e:
                stats.warnings.append(f"Error parsing 세팅.h: {e}")

        # Driver config (woong.cfg)
        for cfg_name in ("woong.cfg", "config.HanLP"):
            cfg_path = self._bin_dir / cfg_name
            if cfg_path.exists():
                try:
                    configs.extend(parse_driver_config(cfg_path))
                except Exception as e:
                    stats.warnings.append(f"Error parsing {cfg_name}: {e}")
                break  # Use first found

        # 전투.h
        combat_h = self._lib_dir / "삽입파일" / "전투.h"
        if combat_h.exists():
            try:
                configs.extend(parse_combat_header(combat_h))
            except Exception as e:
                stats.warnings.append(f"Error parsing 전투.h: {e}")

        # monster.c stat formulas
        monster_c = self._lib_dir / "구조" / "monster.c"
        if monster_c.exists():
            try:
                configs.extend(parse_stat_formulas(monster_c))
            except Exception as e:
                stats.warnings.append(f"Error parsing monster.c formulas: {e}")

        # Deduplicate by key (keep first occurrence)
        seen: dict[str, int] = {}
        unique: list = []
        for gc in configs:
            if gc.key in seen:
                logger.debug("Duplicate game_config key=%r, keeping first", gc.key)
                continue
            seen[gc.key] = len(unique)
            unique.append(gc)
        return unique

    def _infer_zones(self, rooms: list, vnum_gen: VnumGenerator) -> list[Zone]:
        """Infer zones from room directory structure."""
        zone_rooms: dict[int, list] = {}
        zone_names: dict[int, str] = {}

        for room in rooms:
            znum = room.zone_number
            if znum not in zone_rooms:
                zone_rooms[znum] = []
            zone_rooms[znum].append(room)

        zones: list[Zone] = []
        for znum, z_rooms in sorted(zone_rooms.items()):
            if not z_rooms:
                continue

            # Try to extract zone name from extensions or first room
            zone_name = z_rooms[0].name if z_rooms else f"Zone {znum}"

            # Calculate room vnum range
            vnums = [r.vnum for r in z_rooms]
            bot = min(vnums)
            top = max(vnums)

            zones.append(Zone(
                vnum=znum,
                name=zone_name,
                bot=bot,
                top=top,
                reset_mode=2,
            ))

        return zones

    def _build_reset_commands(self, uir: UIR, vnum_gen: VnumGenerator) -> None:
        """Generate zone reset commands from room_inventory/limit_mob extensions."""
        mob_vnums = {m.vnum for m in uir.monsters}
        item_vnums = {i.vnum for i in uir.items}
        zone_map = {z.vnum: z for z in uir.zones}

        for room in uir.rooms:
            room_inv = room.extensions.get("room_inventory", {})
            limit_mob = room.extensions.get("limit_mob", {})

            for path, count in room_inv.items():
                entity_vnum = vnum_gen.path_to_vnum(path)
                if entity_vnum in mob_vnums:
                    max_existing = count
                    # Override with limit_mob value if available
                    if path in limit_mob:
                        max_existing = limit_mob[path]
                    cmd = ZoneResetCommand(
                        command="M",
                        arg1=entity_vnum,
                        arg2=max_existing,
                        arg3=room.vnum,
                    )
                elif entity_vnum in item_vnums:
                    cmd = ZoneResetCommand(
                        command="O",
                        arg1=entity_vnum,
                        arg2=count,
                        arg3=room.vnum,
                    )
                else:
                    logger.debug(
                        "room_inventory path %s (vnum=%d) not found in mobs or items",
                        path, entity_vnum,
                    )
                    continue

                zone = zone_map.get(room.zone_number)
                if zone:
                    zone.reset_commands.append(cmd)
