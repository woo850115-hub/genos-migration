"""CircleMUD .trg file parser (DG Scripts).

Format per trigger:
    #<vnum>
    <name>~
    <attach_type> <trigger_type_flags> <numeric_arg>
    <arg_list>~
    <script body (multi-line)>
    ~
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import Trigger

from .constants import asciiflag_to_int

logger = logging.getLogger(__name__)


def parse_trg_file(filepath: str | Path) -> list[Trigger]:
    """Parse a single .trg file and return a list of Trigger objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding="utf-8", errors="replace")
    return parse_trg_text(text, str(filepath))


def parse_trg_text(text: str, source: str = "<string>") -> list[Trigger]:
    """Parse .trg format text into Trigger objects."""
    triggers: list[Trigger] = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if not line.startswith("#"):
            i += 1
            continue

        vnum_str = line[1:].strip()
        if vnum_str.startswith("$"):
            break

        try:
            vnum = int(vnum_str)
        except ValueError:
            i += 1
            continue

        i += 1
        trigger, i = _parse_single_trigger(vnum, lines, i, source)
        if trigger:
            triggers.append(trigger)

    return triggers


def _parse_single_trigger(
    vnum: int, lines: list[str], i: int, source: str
) -> tuple[Trigger | None, int]:
    """Parse a single trigger block."""
    trigger = Trigger(vnum=vnum)

    # Name~
    trigger.name, i = _read_tilde_string(lines, i)

    # Type line: attach_type trigger_type_flags numeric_arg
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 3:
            trigger.attach_type = int(parts[0])
            trigger.trigger_type = asciiflag_to_int(parts[1])
            trigger.numeric_arg = int(parts[2])

    # Arg list~
    trigger.arg_list, i = _read_tilde_string(lines, i)

    # Script body (until ~)
    trigger.script, i = _read_tilde_string(lines, i)

    return trigger, i


def _read_tilde_string(lines: list[str], i: int) -> tuple[str, int]:
    """Read lines until a line ending with ~ is found."""
    parts: list[str] = []
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.rstrip().endswith("~"):
            content = line.rstrip()[:-1]
            parts.append(content)
            break
        parts.append(line.rstrip("\n"))
    return "\n".join(parts).strip(), i
