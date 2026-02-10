"""GenOS Compiler - transforms UIR to target platform artifacts."""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import UIR

from .db_generator import generate_ddl, generate_seed_data
from .korean_nlp_generator import (
    generate_korean_commands_lua,
    generate_korean_nlp_lua,
)
from .lua_generator import (
    generate_class_lua,
    generate_combat_lua,
    generate_config_lua,
    generate_exp_table_lua,
    generate_stat_tables_lua,
    generate_trigger_lua,
)

logger = logging.getLogger(__name__)


class GenosCompiler:
    """Compiles UIR into GenOS project artifacts."""

    def __init__(self, uir: UIR, output_dir: str | Path) -> None:
        self.uir = uir
        self.output_dir = Path(output_dir)

    def compile(self) -> dict[str, str]:
        """Generate all artifacts. Returns a dict of filepath → description."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        generated: dict[str, str] = {}

        # SQL files
        sql_dir = self.output_dir / "sql"
        sql_dir.mkdir(exist_ok=True)

        ddl_path = sql_dir / "schema.sql"
        with open(ddl_path, "w") as f:
            generate_ddl(self.uir, f)
        generated[str(ddl_path)] = "Database schema DDL"

        seed_path = sql_dir / "seed_data.sql"
        with open(seed_path, "w") as f:
            generate_seed_data(self.uir, f)
        generated[str(seed_path)] = "Seed data INSERT statements"

        # Lua files
        lua_dir = self.output_dir / "lua"
        lua_dir.mkdir(exist_ok=True)

        combat_path = lua_dir / "combat.lua"
        with open(combat_path, "w") as f:
            generate_combat_lua(self.uir, f)
        generated[str(combat_path)] = "Combat system"

        classes_path = lua_dir / "classes.lua"
        with open(classes_path, "w") as f:
            generate_class_lua(self.uir, f)
        generated[str(classes_path)] = "Character classes"

        if self.uir.triggers:
            triggers_path = lua_dir / "triggers.lua"
            with open(triggers_path, "w") as f:
                generate_trigger_lua(self.uir, f)
            generated[str(triggers_path)] = "DG Script triggers (Lua)"

        # Phase 3: game system Lua files
        if self.uir.game_configs:
            config_path = lua_dir / "config.lua"
            with open(config_path, "w") as f:
                generate_config_lua(self.uir, f)
            generated[str(config_path)] = "Game configuration"

        if self.uir.experience_table:
            exp_path = lua_dir / "exp_tables.lua"
            with open(exp_path, "w") as f:
                generate_exp_table_lua(self.uir, f)
            generated[str(exp_path)] = "Experience tables"

        if self.uir.thac0_table or self.uir.saving_throws or self.uir.attribute_modifiers:
            stat_path = lua_dir / "stat_tables.lua"
            with open(stat_path, "w") as f:
                generate_stat_tables_lua(self.uir, f)
            generated[str(stat_path)] = "Stat modifier tables"

        # Phase 4: Korean NLP (always generated)
        nlp_path = lua_dir / "korean_nlp.lua"
        with open(nlp_path, "w") as f:
            generate_korean_nlp_lua(f)
        generated[str(nlp_path)] = "Korean NLP utilities"

        cmd_path = lua_dir / "korean_commands.lua"
        with open(cmd_path, "w") as f:
            generate_korean_commands_lua(self.uir, f)
        generated[str(cmd_path)] = "Korean command interpreter"

        logger.info("Compiled %d artifacts to %s", len(generated), self.output_dir)
        return generated
