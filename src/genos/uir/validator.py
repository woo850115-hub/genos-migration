"""UIR validation utilities."""

from __future__ import annotations

from dataclasses import dataclass, field

from .schema import UIR

# Default command-to-reference-type mapping.
# Adapters may provide an alternative mapping for their reset commands.
DEFAULT_CMD_REF_MAP: dict[str, str] = {
    "M": "mob",   # arg1 references a mob vnum
    "O": "item",  # arg1 references an item vnum
}


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


def validate_uir(
    uir: UIR,
    cmd_ref_map: dict[str, str] | None = None,
) -> ValidationResult:
    """Validate a UIR instance for internal consistency."""
    result = ValidationResult()

    room_vnums = {r.vnum for r in uir.rooms}
    item_vnums = {i.vnum for i in uir.items}
    mob_vnums = {m.vnum for m in uir.monsters}
    trigger_vnums = {t.vnum for t in uir.triggers}

    # Check room exits point to valid rooms
    for room in uir.rooms:
        for exit_ in room.exits:
            if exit_.destination > 0 and exit_.destination not in room_vnums:
                result.add_warning(
                    f"Room {room.vnum}: exit dir {exit_.direction} "
                    f"points to non-existent room {exit_.destination}"
                )
        for tv in room.trigger_vnums:
            if tv not in trigger_vnums:
                result.add_warning(
                    f"Room {room.vnum}: trigger {tv} not found"
                )

    # Check item triggers
    for item in uir.items:
        for tv in item.trigger_vnums:
            if tv not in trigger_vnums:
                result.add_warning(
                    f"Item {item.vnum}: trigger {tv} not found"
                )

    # Check monster triggers
    for mob in uir.monsters:
        for tv in mob.trigger_vnums:
            if tv not in trigger_vnums:
                result.add_warning(
                    f"Monster {mob.vnum}: trigger {tv} not found"
                )

    # Check zone reset commands reference valid entities
    ref_map = cmd_ref_map or DEFAULT_CMD_REF_MAP
    vnum_sets = {"mob": mob_vnums, "item": item_vnums}
    for zone in uir.zones:
        for cmd in zone.reset_commands:
            ref_type = ref_map.get(cmd.command)
            if ref_type and ref_type in vnum_sets:
                if cmd.arg1 not in vnum_sets[ref_type]:
                    result.add_warning(
                        f"Zone {zone.vnum}: {cmd.command} cmd references "
                        f"non-existent {ref_type} {cmd.arg1}"
                    )

    # Check shops reference valid mobs
    for shop in uir.shops:
        if shop.keeper_vnum >= 0 and shop.keeper_vnum not in mob_vnums:
            result.add_warning(
                f"Shop {shop.vnum}: keeper mob {shop.keeper_vnum} not found"
            )

    # Basic sanity checks
    if not uir.rooms:
        result.add_warning("UIR has no rooms")
    if not uir.source_mud:
        result.add_error("UIR missing source_mud info")

    return result
