"""Binary reading utilities for 3eyes MUD data files.

3eyes uses 32-bit Linux C structs with natural alignment:
  char=1, short=2, int=4, long=4, pointer=4.
All multi-byte values are little-endian.
Strings are EUC-KR encoded, null-terminated C strings.
"""

from __future__ import annotations

import struct


def read_byte(data: bytes, offset: int) -> int:
    """Read a signed byte (char)."""
    return struct.unpack_from("<b", data, offset)[0]


def read_ubyte(data: bytes, offset: int) -> int:
    """Read an unsigned byte (unsigned char)."""
    return struct.unpack_from("<B", data, offset)[0]


def read_short(data: bytes, offset: int) -> int:
    """Read a signed 16-bit short."""
    return struct.unpack_from("<h", data, offset)[0]


def read_ushort(data: bytes, offset: int) -> int:
    """Read an unsigned 16-bit short."""
    return struct.unpack_from("<H", data, offset)[0]


def read_int(data: bytes, offset: int) -> int:
    """Read a signed 32-bit int/long."""
    return struct.unpack_from("<i", data, offset)[0]


def read_cstring(data: bytes, offset: int, max_len: int) -> str:
    """Read a null-terminated C string with EUC-KR decoding.

    Extracts up to *max_len* bytes starting at *offset*, stops at the
    first null byte, and decodes as EUC-KR (with replacement for
    unmappable bytes).
    """
    raw = data[offset : offset + max_len]
    null_pos = raw.find(b"\x00")
    if null_pos >= 0:
        raw = raw[:null_pos]
    return raw.decode("euc-kr", errors="replace").strip()


def read_cstring_array(
    data: bytes, offset: int, count: int, item_len: int,
) -> list[str]:
    """Read an array of fixed-length C strings (e.g. ``char key[3][20]``)."""
    return [
        read_cstring(data, offset + i * item_len, item_len)
        for i in range(count)
    ]


def flags_to_bit_positions(flag_bytes: bytes) -> list[int]:
    """Convert a flags byte-array to a list of set bit positions.

    Mirrors the C macro ``F_ISSET(p, f) => p->flags[f/8] & (1<<(f%8))``.
    """
    positions: list[int] = []
    for byte_idx, byte_val in enumerate(flag_bytes):
        for bit in range(8):
            if byte_val & (1 << bit):
                positions.append(byte_idx * 8 + bit)
    return positions
