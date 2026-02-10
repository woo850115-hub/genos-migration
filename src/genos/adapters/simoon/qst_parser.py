"""Simoon .qst file parser.

Format per quest:
    #<vnum>
    <name>~
    <keywords>~
    <description (multi-line)>
    ~
    <completion_message (multi-line)>
    ~
    <quest_type> <mob_vnum> <obj_vnum> <target_vnum> <reward_exp> <next_quest> <min_level>
    <value0> <value1> <value2> <value3>
    S

Differences from tbaMUD:
  - Only 4 tilde strings (no quit_message)
  - params line 1: 7 fields (quest_type mob_vnum obj_vnum target_vnum reward_exp next_quest min_level)
  - params line 2: 4 fields (value0 value1 value2 value3)
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import Quest

logger = logging.getLogger(__name__)

_ENCODING = "euc-kr"


def parse_qst_file(filepath: str | Path) -> list[Quest]:
    """Parse a single .qst file and return a list of Quest objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding=_ENCODING, errors="replace")
    return parse_qst_text(text, str(filepath))


def parse_qst_text(text: str, source: str = "<string>") -> list[Quest]:
    """Parse .qst format text into Quest objects."""
    quests: list[Quest] = []
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
        quest, i = _parse_single_quest(vnum, lines, i, source)
        if quest:
            quests.append(quest)

    return quests


def _parse_single_quest(
    vnum: int, lines: list[str], i: int, source: str
) -> tuple[Quest | None, int]:
    """Parse a single quest block."""
    quest = Quest(vnum=vnum)

    # Name~
    quest.name, i = _read_tilde_string(lines, i)
    # Keywords~
    quest.keywords, i = _read_tilde_string(lines, i)
    # Description~
    quest.description, i = _read_tilde_string(lines, i)
    # Completion message~
    quest.completion_message, i = _read_tilde_string(lines, i)
    # No quit_message in Simoon format

    # Params line 1: quest_type mob_vnum obj_vnum target_vnum reward_exp next_quest min_level
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 1:
            quest.quest_type = int(parts[0])
        if len(parts) >= 2:
            quest.mob_vnum = int(parts[1])
        if len(parts) >= 3:
            quest.quest_flags = int(parts[2])  # obj_vnum reused as flags
        if len(parts) >= 4:
            quest.target_vnum = int(parts[3])
        if len(parts) >= 5:
            quest.reward_exp = int(parts[4])
        if len(parts) >= 6:
            quest.next_quest = int(parts[5])
        if len(parts) >= 7:
            quest.min_level = int(parts[6])

    # Params line 2: value0 value1 value2 value3
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 1:
            quest.value0 = int(parts[0])
        if len(parts) >= 2:
            quest.value1 = int(parts[1])
        if len(parts) >= 3:
            quest.value2 = int(parts[2])
        if len(parts) >= 4:
            quest.value3 = int(parts[3])

    # Skip until 'S' or next entry
    while i < len(lines):
        line = lines[i].rstrip()
        if line == "S":
            i += 1
            break
        if line.startswith("#") or line.startswith("$"):
            break
        i += 1

    return quest, i


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
