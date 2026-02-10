"""Auto-detect MUD type from source directory."""

from __future__ import annotations

from pathlib import Path

from .base import BaseAdapter


_ADAPTER_REGISTRY: list[type[BaseAdapter]] = []
_adapters_loaded: bool = False

# Adapters listed earlier have higher priority (checked first).
# More specific adapters should come before generic fallbacks.
_ADAPTER_ORDER: list[str] = [
    "LPMudAdapter",      # LP-MUD: LPC source files (FluffOS/MudOS)
    "ThreeEyesAdapter",  # 3eyes: binary C struct format (most specific)
    "SimoonAdapter",     # Simoon: specific (requires HANGUL.TXT)
    "CircleMudAdapter",  # CircleMUD/tbaMUD: generic fallback
]


def register_adapter(cls: type[BaseAdapter]) -> type[BaseAdapter]:
    """Decorator to register an adapter class for auto-detection."""
    if cls not in _ADAPTER_REGISTRY:
        _ADAPTER_REGISTRY.append(cls)
    return cls


def detect_mud_type(source_path: str | Path) -> BaseAdapter | None:
    """Try each registered adapter's detect() and return the first match.

    Adapters are checked in priority order defined by _ADAPTER_ORDER,
    so more specific adapters are tried before generic ones.
    """
    _ensure_adapters_loaded()
    source_path = Path(source_path)

    # Sort registry by priority order
    def _sort_key(cls: type[BaseAdapter]) -> int:
        name = cls.__name__
        try:
            return _ADAPTER_ORDER.index(name)
        except ValueError:
            return len(_ADAPTER_ORDER)

    ordered = sorted(_ADAPTER_REGISTRY, key=_sort_key)
    for cls in ordered:
        adapter = cls(source_path)
        if adapter.detect():
            return adapter
    return None


def _ensure_adapters_loaded() -> None:
    """Import adapter modules on first use so they self-register."""
    global _adapters_loaded
    if not _adapters_loaded:
        _adapters_loaded = True
        import genos.adapters.lpmud      # noqa: F401
        import genos.adapters.threeeyes  # noqa: F401
        import genos.adapters.simoon     # noqa: F401
        import genos.adapters.circlemud  # noqa: F401
