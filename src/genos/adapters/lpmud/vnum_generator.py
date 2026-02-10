"""File path to stable integer VNUM mapping for LP-MUD.

LP-MUD/FluffOS uses file paths as identity instead of numeric VNUMs.
This module generates deterministic integer IDs from relative paths.
"""

from __future__ import annotations

import hashlib


class VnumGenerator:
    """Maps file paths to stable integer VNUMs with collision resolution."""

    def __init__(self) -> None:
        self._path_to_vnum: dict[str, int] = {}
        self._vnum_to_path: dict[int, str] = {}

    @staticmethod
    def _normalize_path(filepath: str) -> str:
        """Normalize path: strip .c extension and leading /."""
        normalized = filepath.rstrip("/")
        if normalized.endswith(".c"):
            normalized = normalized[:-2]
        return normalized.lstrip("/")

    def path_to_vnum(self, filepath: str) -> int:
        """Convert a relative file path to a stable integer VNUM.

        Uses SHA-256 hash of the path, taking upper 31 bits.
        Collisions are resolved by linear probing.
        """
        normalized = self._normalize_path(filepath)

        if normalized in self._path_to_vnum:
            return self._path_to_vnum[normalized]

        vnum = self._hash_to_int(normalized)

        # Collision resolution
        while vnum in self._vnum_to_path and self._vnum_to_path[vnum] != normalized:
            vnum += 1

        self._path_to_vnum[normalized] = vnum
        self._vnum_to_path[vnum] = normalized
        return vnum

    def zone_id(self, dirpath: str) -> int:
        """Convert a directory path to a zone VNUM."""
        normalized = dirpath.strip("/")
        return self._hash_to_int(f"zone:{normalized}") // 100

    def get_path_map(self) -> dict[int, str]:
        """Return VNUM -> original path reverse mapping."""
        return dict(self._vnum_to_path)

    @staticmethod
    def _hash_to_int(text: str) -> int:
        """SHA-256 hash -> upper 31-bit positive integer."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        val = int.from_bytes(digest[:4], "big")
        return val & 0x7FFF_FFFF  # 31-bit positive
