"""LPC source code parsing utilities.

Extracts setXxx() method calls, LPC mappings, arrays, and string literals
from FluffOS/LP-MUD .c source files encoded in EUC-KR.
"""

from __future__ import annotations

import re
from pathlib import Path


def read_lpc_file(filepath: Path, encoding: str = "euc-kr") -> str:
    """Read an LPC file with EUC-KR decoding, strip comments."""
    raw = filepath.read_bytes()
    text = raw.decode(encoding, errors="replace")
    return strip_lpc_comments(text)


def strip_lpc_comments(text: str) -> str:
    """Remove // and /* */ comments from LPC source."""
    # Remove block comments (non-greedy)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    # Remove line comments
    text = re.sub(r"//[^\n]*", "", text)
    return text


def extract_inherit(text: str) -> str | None:
    """Extract inherit target: 'inherit LIB_ROOM;' -> 'LIB_ROOM'."""
    m = re.search(r"inherit\s+(LIB_\w+)\s*;", text)
    return m.group(1) if m else None


def extract_string_call(text: str, method: str) -> str | None:
    """Extract string argument from setXxx("...") call.

    Handles multi-line concatenated strings like:
        setLong("line1 "
                "line2");
    """
    # Match method call with opening paren
    pattern = re.compile(
        rf"{re.escape(method)}\s*\(", re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        return None

    start = m.end()
    # Collect all consecutive string fragments
    result_parts: list[str] = []
    pos = start
    rest = text[pos:]

    while True:
        rest = rest.lstrip()
        if not rest or rest[0] == ")":
            break
        if rest[0] == '"':
            s, consumed = _parse_string_literal(rest)
            if s is not None:
                result_parts.append(s)
                rest = rest[consumed:]
                continue
            break
        # Skip non-string chars (like + or whitespace)
        if rest[0] in ("+", "\n", "\r", "\t", " "):
            rest = rest[1:]
            continue
        break

    if result_parts:
        return "".join(result_parts)
    return None


def extract_int_call(text: str, method: str) -> int | None:
    """Extract integer argument from setXxx(N) call."""
    pattern = re.compile(
        rf"{re.escape(method)}\s*\(\s*(-?\d+)\s*\)",
    )
    m = pattern.search(text)
    return int(m.group(1)) if m else None


def extract_float_call(text: str, method: str) -> float | None:
    """Extract float argument from setXxx(N.N) call."""
    pattern = re.compile(
        rf"{re.escape(method)}\s*\(\s*(-?\d+\.?\d*)\s*\)",
    )
    m = pattern.search(text)
    return float(m.group(1)) if m else None


def extract_void_call(text: str, method: str) -> bool:
    """Check if setXxx() (no args or with args) is called."""
    pattern = re.compile(rf"{re.escape(method)}\s*\(")
    return bool(pattern.search(text))


def extract_mapping(text: str, method: str) -> dict | None:
    """Extract LPC mapping from setXxx(([ ... ])) call.

    Returns dict of string->string or string->int.
    """
    pattern = re.compile(
        rf"{re.escape(method)}\s*\(\s*\(\[", re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        return None

    # Find matching ]))
    start = m.end()
    content = _extract_balanced(text, start - 2, "([", "])")
    if content is None:
        return None

    return _parse_mapping_content(content)


def extract_array(text: str, method: str) -> list | None:
    """Extract LPC array from setXxx(({ ... })) call.

    Returns list of strings.
    """
    pattern = re.compile(
        rf"{re.escape(method)}\s*\(\s*\(\{{", re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        return None

    start = m.end()
    content = _extract_balanced(text, start - 2, "({", "})")
    if content is None:
        return None

    return _parse_array_content(content)


def extract_string_pair_call(text: str, method: str) -> tuple[str, int] | None:
    """Extract (string, int) pair from setXxx("str", N) call."""
    pattern = re.compile(
        rf'{re.escape(method)}\s*\(\s*"([^"]*?)"\s*,\s*(-?\d+)\s*\)',
    )
    m = pattern.search(text)
    if m:
        return (m.group(1), int(m.group(2)))
    return None


def extract_all_string_pair_calls(text: str, method: str) -> list[tuple[str, int]]:
    """Extract all (string, int) pairs from repeated setXxx("str", N) calls."""
    pattern = re.compile(
        rf'{re.escape(method)}\s*\(\s*"([^"]*?)"\s*,\s*(-?\d+)\s*\)',
    )
    return [(m.group(1), int(m.group(2))) for m in pattern.finditer(text)]


def extract_clone_items(text: str) -> list[str]:
    """Extract all cloneItem("path") calls."""
    pattern = re.compile(r'cloneItem\s*\(\s*"([^"]+)"\s*\)')
    return [m.group(1) for m in pattern.finditer(text)]


def extract_prop_calls(text: str) -> dict[str, str | int]:
    """Extract all setProp("key", value) calls."""
    result: dict[str, str | int] = {}
    # String value
    for m in re.finditer(r'setProp\s*\(\s*"([^"]+)"\s*,\s*"([^"]*?)"\s*\)', text):
        result[m.group(1)] = m.group(2)
    # Int value
    for m in re.finditer(r'setProp\s*\(\s*"([^"]+)"\s*,\s*(-?\d+)\s*\)', text):
        result[m.group(1)] = int(m.group(2))
    return result


def strip_color_codes(text: str) -> str:
    """Remove FluffOS color codes: %^CYAN%^text%^RESET%^."""
    return re.sub(r"%\^[A-Z]+%\^", "", text)


def strip_help_color_codes(text: str) -> str:
    """Remove help file color codes: !C, !O, !@, !RR etc."""
    text = re.sub(r"![A-Z]+", "", text)
    text = re.sub(r"!@", "", text)
    return text


# ── Internal helpers ────────────────────────────────────────────────


def _parse_string_literal(text: str) -> tuple[str | None, int]:
    """Parse a quoted string literal starting at text[0]=='"'.

    Returns (string_value, chars_consumed) or (None, 0).
    """
    if not text or text[0] != '"':
        return None, 0

    pos = 1
    parts: list[str] = []
    while pos < len(text):
        ch = text[pos]
        if ch == "\\":
            if pos + 1 < len(text):
                esc = text[pos + 1]
                if esc == "n":
                    parts.append("\n")
                elif esc == "t":
                    parts.append("\t")
                elif esc == '"':
                    parts.append('"')
                elif esc == "\\":
                    parts.append("\\")
                else:
                    parts.append(esc)
                pos += 2
                continue
        if ch == '"':
            return "".join(parts), pos + 1
        parts.append(ch)
        pos += 1

    return None, 0


def _extract_balanced(text: str, start: int, open_tok: str, close_tok: str) -> str | None:
    """Extract content between balanced LPC delimiters like ([ ... ]).

    start should point to the opening delimiter.
    """
    depth = 0
    pos = start
    content_start = start + len(open_tok)

    while pos < len(text):
        if text[pos:pos + len(open_tok)] == open_tok:
            depth += 1
            pos += len(open_tok)
        elif text[pos:pos + len(close_tok)] == close_tok:
            depth -= 1
            if depth == 0:
                return text[content_start:pos]
            pos += len(close_tok)
        else:
            pos += 1

    return None


def _parse_mapping_content(content: str) -> dict:
    """Parse the inside of an LPC mapping ([ k:v, k:v ])."""
    result: dict[str, str | int] = {}

    # Split by comma, then parse key:value pairs
    # Handle nested structures by tracking brackets
    entries = _split_lpc_entries(content, ",")

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        # Split on first ':'
        colon_pos = entry.find(":")
        if colon_pos == -1:
            continue

        key_part = entry[:colon_pos].strip()
        val_part = entry[colon_pos + 1:].strip()

        key = _parse_lpc_value(key_part)
        val = _parse_lpc_value(val_part)

        if key is not None:
            result[str(key)] = val

    return result


def _parse_array_content(content: str) -> list:
    """Parse the inside of an LPC array ({ elem, elem })."""
    entries = _split_lpc_entries(content, ",")
    result: list = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        val = _parse_lpc_value(entry)
        if val is not None:
            result.append(val)
    return result


def _split_lpc_entries(text: str, sep: str) -> list[str]:
    """Split LPC entries respecting nested brackets and strings."""
    entries: list[str] = []
    depth = 0
    current: list[str] = []
    in_string = False
    i = 0

    while i < len(text):
        ch = text[i]

        if in_string:
            current.append(ch)
            if ch == "\\" and i + 1 < len(text):
                current.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            current.append(ch)
            i += 1
            continue

        if ch == "(" and i + 1 < len(text) and text[i + 1] in ("[", "{"):
            depth += 1
            current.append(ch)
            i += 1
            continue

        if ch in ("]", "}") and i + 1 < len(text) and text[i + 1] == ")":
            depth -= 1
            current.append(ch)
            i += 1
            continue

        if ch == sep and depth == 0:
            entries.append("".join(current))
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    if current:
        entries.append("".join(current))

    return entries


def _parse_lpc_value(text: str) -> str | int | None:
    """Parse a single LPC literal value (string or int)."""
    text = text.strip()
    if not text:
        return None

    # String literal
    if text.startswith('"'):
        val, _ = _parse_string_literal(text)
        return val

    # Integer literal
    m = re.match(r"^-?\d+$", text)
    if m:
        return int(text)

    # Path reference (unquoted, starts with /)
    if text.startswith("/"):
        return text.strip()

    # Variable or expression - return as string
    return text
