"""GenOS Compiler - transforms UIR to target platform artifacts."""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import UIR

from .db_generator import generate_ddl, generate_seed_data
from .lua_generator import generate_class_lua, generate_combat_lua, generate_trigger_lua

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

        logger.info("Compiled %d artifacts to %s", len(generated), self.output_dir)
        return generated
