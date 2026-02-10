"""CircleMUD .shp file parser.

Format per shop:
    #<vnum>~
    <item_vnum>     (repeated, -1 terminates)
    <profit_buy>
    <profit_sell>
    <accept_type>   (repeated, -1 terminates)
    <no_such_item1>~
    <no_such_item2>~
    <do_not_buy>~
    <missing_cash1>~
    <missing_cash2>~
    <message_buy>~
    <message_sell>~
    <temper>
    <bitvector>
    <keeper_vnum>
    <with_who>
    <shop_room>     (repeated, -1 terminates)
    <open1>
    <close1>
    <open2>
    <close2>
"""

from __future__ import annotations

import logging
from pathlib import Path

from genos.uir.schema import Shop

logger = logging.getLogger(__name__)


def parse_shp_file(filepath: str | Path) -> list[Shop]:
    """Parse a single .shp file and return a list of Shop objects."""
    filepath = Path(filepath)
    text = filepath.read_text(encoding="utf-8", errors="replace")
    return parse_shp_text(text, str(filepath))


def parse_shp_text(text: str, source: str = "<string>") -> list[Shop]:
    """Parse .shp format text into Shop objects."""
    shops: list[Shop] = []
    lines = text.split("\n")
    i = 0

    # Skip file header line
    if lines and lines[0].rstrip().startswith("CircleMUD"):
        i += 1

    while i < len(lines):
        line = lines[i].rstrip()

        if not line.startswith("#"):
            i += 1
            continue

        # Shop vnum: #<num>~
        vnum_str = line[1:].rstrip("~").strip()
        if vnum_str.startswith("$"):
            break

        try:
            vnum = int(vnum_str)
        except ValueError:
            i += 1
            continue

        i += 1
        shop, i = _parse_single_shop(vnum, lines, i, source)
        if shop:
            shops.append(shop)

    return shops


def _parse_single_shop(
    vnum: int, lines: list[str], i: int, source: str
) -> tuple[Shop | None, int]:
    """Parse a single shop block."""
    shop = Shop(vnum=vnum)

    # Item vnums (until -1)
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        try:
            val = int(line)
        except ValueError:
            continue
        if val == -1:
            break
        shop.selling_items.append(val)

    # Profit buy
    if i < len(lines):
        try:
            shop.profit_buy = float(lines[i].rstrip())
        except ValueError:
            pass
        i += 1

    # Profit sell
    if i < len(lines):
        try:
            shop.profit_sell = float(lines[i].rstrip())
        except ValueError:
            pass
        i += 1

    # Accepting types (until -1)
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        try:
            val = int(line)
        except ValueError:
            continue
        if val == -1:
            break
        shop.accepting_types.append(val)

    # 7 message strings (each ends with ~)
    messages = []
    for _ in range(7):
        msg, i = _read_tilde_string(lines, i)
        messages.append(msg)

    if len(messages) >= 7:
        shop.no_such_item1 = messages[0]
        shop.no_such_item2 = messages[1]
        shop.do_not_buy = messages[2]
        shop.missing_cash1 = messages[3]
        shop.missing_cash2 = messages[4]
        shop.message_buy = messages[5]
        shop.message_sell = messages[6]

    # temper
    if i < len(lines):
        try:
            shop.temper = int(lines[i].rstrip())
        except ValueError:
            pass
        i += 1

    # bitvector
    if i < len(lines):
        try:
            shop.bitvector = int(lines[i].rstrip())
        except ValueError:
            pass
        i += 1

    # keeper vnum
    if i < len(lines):
        try:
            shop.keeper_vnum = int(lines[i].rstrip())
        except ValueError:
            pass
        i += 1

    # with_who
    if i < len(lines):
        try:
            shop.with_who = int(lines[i].rstrip())
        except ValueError:
            pass
        i += 1

    # Shop rooms (until -1)
    first_room = True
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        try:
            val = int(line)
        except ValueError:
            continue
        if val == -1:
            break
        if first_room:
            shop.shop_room = val
            first_room = False

    # open1, close1, open2, close2
    for attr in ("open1", "close1", "open2", "close2"):
        if i < len(lines):
            try:
                setattr(shop, attr, int(lines[i].rstrip()))
            except ValueError:
                pass
            i += 1

    return shop, i


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
