"""Parse command .c files from 명령어/플레이어/ into UIR Command objects."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from genos.uir.schema import Command

from .lpc_parser import read_lpc_file

logger = logging.getLogger(__name__)


def parse_all_commands(
    cmd_dir: Path,
    encoding: str = "euc-kr",
) -> list[Command]:
    """Parse all command .c files in the player command directory."""
    commands: list[Command] = []

    if not cmd_dir.is_dir():
        return commands

    for c_file in sorted(cmd_dir.glob("*.c")):
        try:
            cmd = _parse_command_file(c_file, encoding)
            if cmd:
                commands.append(cmd)
        except Exception as e:
            logger.debug("Error parsing command %s: %s", c_file, e)

    return commands


def _parse_command_file(filepath: Path, encoding: str) -> Command | None:
    """Parse a single command .c file."""
    try:
        text = read_lpc_file(filepath, encoding)
    except Exception:
        return None

    # Extract getCMD() return array
    # Pattern: getCMD() { return ({ "cmd1", "cmd2" }); }
    m = re.search(
        r'getCMD\s*\(\s*\)\s*\{[^}]*return\s*\(\{(.*?)\}\)',
        text,
        re.DOTALL,
    )

    if not m:
        return None

    # Extract string elements from the array
    names = re.findall(r'"([^"]+)"', m.group(1))
    if not names:
        return None

    primary_name = names[0]
    aliases = names[1:] if len(names) > 1 else []

    handler = filepath.stem

    cmd = Command(
        name=primary_name,
        handler=handler,
    )

    if aliases:
        cmd.description = f"Aliases: {', '.join(aliases)}"

    return cmd
