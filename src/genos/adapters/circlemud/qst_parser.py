"""CircleMUD .qst file parser (tbaMUD quest system).

Format per quest:
    #<vnum>
    <name>~
    <keywords>~
    <description (multi-line)>
    ~
    <completion_message (multi-line)>
    ~
    <quit_message (multi-line)>
    ~
    <flags> <type> <target_vnum> <mob_vnum> <value0> <value1> <value2> <value3>
    <reward_gold> <reward_exp> <reward_obj> <next_quest> <prev_quest> <min_level> <max_level>
    S
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import Quest

logger = logging.getLogger(__name__)


def parse_qst_file(filepath: str | Path) -> list[Quest]:
    """Parse a single .qst file and return a list of Quest objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding="utf-8", errors="replace")
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
    # Quit message~
    quest.quit_message, i = _read_tilde_string(lines, i)

    # Params line: flags type target_vnum mob_vnum value0 value1 value2 value3
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 4:
            quest.quest_flags = int(parts[0])
            quest.quest_type = int(parts[1])
            quest.target_vnum = int(parts[2])
            quest.mob_vnum = int(parts[3])
        if len(parts) >= 5:
            quest.value0 = int(parts[4])
        if len(parts) >= 6:
            quest.value1 = int(parts[5])
        if len(parts) >= 7:
            quest.value2 = int(parts[6])
        if len(parts) >= 8:
            quest.value3 = int(parts[7])

    # Rewards line: gold exp obj next_quest prev_quest min_level max_level
    if i < len(lines):
        parts = lines[i].rstrip().split()
        i += 1
        if len(parts) >= 3:
            quest.reward_gold = int(parts[0])
            quest.reward_exp = int(parts[1])
            quest.reward_obj = int(parts[2])
        if len(parts) >= 4:
            quest.next_quest = int(parts[3])
        if len(parts) >= 5:
            quest.prev_quest = int(parts[4])
        if len(parts) >= 6:
            quest.min_level = int(parts[5])
        if len(parts) >= 7:
            quest.max_level = int(parts[6])

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
