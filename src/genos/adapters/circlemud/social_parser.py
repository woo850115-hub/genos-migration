"""Parser for CircleMUD/tbaMUD socials file (lib/misc/socials).

Format per entry:
    <command> <min_victim_position> <flags>
    <no_arg_to_char>
    <no_arg_to_room>          (may be '#' for empty)
    <found_to_char>           (may be '#' for empty / absent)
    <found_to_room>
    <found_to_victim>
    <not_found>
    <self_to_char>
    <self_to_room>
    <blank line>

'$' on its own line terminates the file.
'#' as a message line means "no message" (end of this social's messages).
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import Social

logger = logging.getLogger(__name__)


def parse_social_file(filepath: str | Path, encoding: str = "utf-8") -> list[Social]:
    """Parse a CircleMUD socials file into Social objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding=encoding, errors="replace")
    return _parse_socials_text(text)


def _parse_socials_text(text: str) -> list[Social]:
    """Parse socials from raw text content."""
    lines = text.split("\n")
    socials: list[Social] = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip blank lines
        if not line:
            i += 1
            continue

        # End of file marker
        if line == "$":
            break

        # Parse header: command min_victim_position flags
        parts = line.split()
        if len(parts) < 3:
            i += 1
            continue

        social = Social()
        social.command = parts[0]
        try:
            social.min_victim_position = int(parts[1])
            social.flags = int(parts[2])
        except ValueError:
            i += 1
            continue

        # Read message lines - up to 8 messages, terminated by '#' or blank line
        messages: list[str] = []
        i += 1
        while i < len(lines) and len(messages) < 8:
            msg_line = lines[i]
            stripped = msg_line.strip()

            # '#' means "no more messages for this social"
            if stripped == "#":
                i += 1
                break

            # Blank line also terminates
            if not stripped:
                i += 1
                break

            messages.append(stripped)
            i += 1

        # Assign messages to fields based on position
        if len(messages) >= 1:
            social.no_arg_to_char = messages[0]
        if len(messages) >= 2:
            social.no_arg_to_room = messages[1]
        if len(messages) >= 3:
            social.found_to_char = messages[2]
        if len(messages) >= 4:
            social.found_to_room = messages[3]
        if len(messages) >= 5:
            social.found_to_victim = messages[4]
        if len(messages) >= 6:
            social.not_found = messages[5]
        if len(messages) >= 7:
            social.self_to_char = messages[6]
        if len(messages) >= 8:
            social.self_to_room = messages[7]

        socials.append(social)

    return socials
