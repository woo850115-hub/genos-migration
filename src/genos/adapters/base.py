"""Base adapter interface for MUD source parsing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from genos.uir.schema import UIR


@dataclass
class AnalysisReport:
    mud_type: str = ""
    source_path: str = ""
    room_count: int = 0
    item_count: int = 0
    mob_count: int = 0
    zone_count: int = 0
    shop_count: int = 0
    trigger_count: int = 0
    quest_count: int = 0
    social_count: int = 0
    help_count: int = 0
    skill_count: int = 0
    command_count: int = 0
    race_count: int = 0
    estimated_conversion_rate: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"MUD Type: {self.mud_type}",
            f"Source: {self.source_path}",
            f"Rooms: {self.room_count}",
            f"Items: {self.item_count}",
            f"Mobs: {self.mob_count}",
            f"Zones: {self.zone_count}",
            f"Shops: {self.shop_count}",
            f"Triggers: {self.trigger_count}",
            f"Quests: {self.quest_count}",
            f"Socials: {self.social_count}",
            f"Help Entries: {self.help_count}",
            f"Skills: {self.skill_count}",
            f"Commands: {self.command_count}",
            f"Races: {self.race_count}",
            f"Estimated Conversion: {self.estimated_conversion_rate:.1%}",
        ]
        if self.warnings:
            lines.append(f"Warnings: {len(self.warnings)}")
        return "\n".join(lines)


class BaseAdapter(ABC):
    """Abstract base class for MUD source adapters."""

    def __init__(self, source_path: str | Path) -> None:
        self.source_path = Path(source_path)

    @abstractmethod
    def detect(self) -> bool:
        """Return True if this adapter can handle the source."""
        ...

    @abstractmethod
    def analyze(self) -> AnalysisReport:
        """Analyze the source without full parsing."""
        ...

    @abstractmethod
    def parse(self) -> UIR:
        """Parse the entire source into a UIR object."""
        ...
