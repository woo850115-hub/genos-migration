"""UIR → Lua script generator.

Generates Lua scripts for:
- Combat system (THAC0-based)
- DG Script → Lua conversion (basic patterns)
- Class level-up logic
"""

from __future__ import annotations

from typing import TextIO

from genos.uir.schema import UIR


def generate_combat_lua(uir: UIR, out: TextIO) -> None:
    """Generate combat system Lua script."""
    out.write("-- GenOS Combat System\n")
    out.write("-- Auto-generated from UIR\n\n")
    out.write("local Combat = {}\n\n")

    # Attack type names
    out.write("Combat.ATTACK_TYPES = {\n")
    for idx, name in enumerate(uir.combat_system.damage_types):
        out.write(f'    [{idx}] = "{name}",\n')
    out.write("}\n\n")

    # THAC0 calculation
    out.write("""\
-- Calculate hit roll (THAC0 system)
-- thac0: attacker's THAC0 value
-- ac: defender's armor class
-- hitroll: attacker's hitroll bonus
function Combat.calculate_hit(thac0, ac, hitroll)
    local roll = math.random(1, 20)
    local needed = thac0 - ac - hitroll
    return roll >= needed, roll
end

-- Calculate damage
-- dice_num: number of dice
-- dice_size: size of each die
-- bonus: flat bonus
function Combat.roll_damage(dice_num, dice_size, bonus)
    local total = bonus
    for i = 1, dice_num do
        total = total + math.random(1, dice_size)
    end
    return math.max(1, total)
end

-- Get THAC0 for class and level
function Combat.get_thac0(class_id, level)
    local thac0_table = {
""")

    for cls in uir.character_classes:
        base_thac0 = cls.extensions.get("base_thac0", 20)
        thac0_gain = cls.extensions.get("thac0_gain", 1.0)
        out.write(f'        [{cls.id}] = {{ base = {base_thac0}, ')
        out.write(f'gain = {thac0_gain} }},  -- {cls.name}\n')

    out.write("""\
    }
    local entry = thac0_table[class_id]
    if not entry then return 20 end
    return math.max(1, math.floor(entry.base - (level * entry.gain)))
end

""")

    out.write("return Combat\n")


def generate_trigger_lua(uir: UIR, out: TextIO) -> None:
    """Convert DG Script triggers to Lua (basic pattern matching)."""
    out.write("-- GenOS Trigger Scripts\n")
    out.write("-- Auto-generated from UIR (DG Script → Lua)\n\n")
    out.write("local Triggers = {}\n\n")

    for trigger in uir.triggers:
        lua_name = f"trigger_{trigger.vnum}"
        out.write(f"-- Trigger {trigger.vnum}: {trigger.name}\n")
        out.write(f"Triggers[{trigger.vnum}] = {{\n")
        out.write(f"    name = {_lua_str(trigger.name)},\n")
        out.write(f"    attach_type = {trigger.attach_type},\n")
        out.write(f"    trigger_type = {trigger.trigger_type},\n")
        out.write(f"    numeric_arg = {trigger.numeric_arg},\n")

        # Convert DG script to Lua (basic)
        lua_body = _convert_dg_to_lua(trigger.script)
        out.write(f"    execute = function(self, actor, extra)\n")
        for line in lua_body.split("\n"):
            if line.strip():
                out.write(f"        {line}\n")
        out.write(f"    end,\n")
        out.write(f"}}\n\n")

    out.write("return Triggers\n")


def generate_class_lua(uir: UIR, out: TextIO) -> None:
    """Generate class definitions and level-up logic."""
    out.write("-- GenOS Character Classes\n")
    out.write("-- Auto-generated from UIR\n\n")
    out.write("local Classes = {}\n\n")

    for cls in uir.character_classes:
        base_thac0 = cls.extensions.get("base_thac0", 20)
        thac0_gain = cls.extensions.get("thac0_gain", 1.0)
        out.write(f"Classes[{cls.id}] = {{\n")
        out.write(f"    name = {_lua_str(cls.name)},\n")
        out.write(f"    abbrev = {_lua_str(cls.abbreviation)},\n")
        out.write(f"    base_thac0 = {base_thac0},\n")
        out.write(f"    thac0_gain = {thac0_gain},\n")
        out.write(f"    hp_gain = {{ {cls.hp_gain_min}, {cls.hp_gain_max} }},\n")
        out.write(f"    mana_gain = {{ {cls.mana_gain_min}, {cls.mana_gain_max} }},\n")
        out.write(f"    move_gain = {{ {cls.move_gain_min}, {cls.move_gain_max} }},\n")
        out.write(f"}}\n\n")

    out.write("""\
-- Level up a character
function Classes.level_up(character)
    local cls = Classes[character.class_id]
    if not cls then return end

    character.level = character.level + 1
    local hp_gain = math.random(cls.hp_gain[1], cls.hp_gain[2])
    local mana_gain = math.random(cls.mana_gain[1], cls.mana_gain[2])
    local move_gain = math.random(cls.move_gain[1], cls.move_gain[2])

    character.max_hp = character.max_hp + hp_gain
    character.max_mana = character.max_mana + mana_gain
    character.max_move = character.max_move + move_gain

    return hp_gain, mana_gain, move_gain
end

""")

    out.write("return Classes\n")


def _convert_dg_to_lua(dg_script: str) -> str:
    """Basic DG Script to Lua conversion.

    Handles simple patterns; complex scripts get a TODO comment.
    """
    if not dg_script.strip():
        return "-- empty trigger\n"

    lines = []
    for raw_line in dg_script.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        # Comments
        if line.startswith("*"):
            lines.append(f"-- {line[1:].strip()}")
            continue

        # if/elseif/else/end
        if line.startswith("if "):
            condition = line[3:].strip()
            condition = _convert_dg_condition(condition)
            lines.append(f"if {condition} then")
        elif line.startswith("elseif "):
            condition = line[7:].strip()
            condition = _convert_dg_condition(condition)
            lines.append(f"elseif {condition} then")
        elif line == "else":
            lines.append("else")
        elif line == "end":
            lines.append("end")
        elif line.startswith("wait "):
            # wait 1 sec → coroutine.yield(1)
            parts = line.split()
            if len(parts) >= 2:
                try:
                    secs = int(parts[1])
                    lines.append(f"coroutine.yield({secs})")
                except ValueError:
                    lines.append(f"-- TODO: {line}")
        elif line.startswith("say "):
            msg = line[4:]
            lines.append(f'self:say({_lua_str(msg)})')
        elif line.startswith("emote "):
            msg = line[6:]
            lines.append(f'self:emote({_lua_str(msg)})')
        elif line.startswith("%send%"):
            lines.append(f"-- TODO: {line}")
        elif line.startswith("%echoaround%"):
            lines.append(f"-- TODO: {line}")
        elif line.startswith("%load%"):
            lines.append(f"-- TODO: {line}")
        elif line.startswith("%purge%"):
            lines.append(f"-- TODO: {line}")
        elif line.startswith("nop "):
            lines.append(f"-- nop: {line[4:]}")
        elif line.startswith("return "):
            lines.append(f"return {line[7:]}")
        elif line.startswith("eval "):
            lines.append(f"-- TODO eval: {line}")
        elif line.startswith("give "):
            lines.append(f"-- TODO: {line}")
        elif line.startswith("unlock "):
            lines.append(f"-- TODO: {line}")
        elif line.startswith("open "):
            lines.append(f"-- TODO: {line}")
        elif line.startswith("close "):
            lines.append(f"-- TODO: {line}")
        elif line.startswith("lock "):
            lines.append(f"-- TODO: {line}")
        else:
            lines.append(f"-- TODO: {line}")

    return "\n".join(lines) if lines else "-- empty trigger\n"


def _convert_dg_condition(condition: str) -> str:
    """Convert a DG Script condition to Lua."""
    # Replace %actor.is_pc% → actor.is_pc
    result = condition
    result = result.replace("&&", "and")
    result = result.replace("||", "or")
    result = result.replace("==", "==")
    result = result.replace("!=", "~=")
    # %variable% → variable
    while "%" in result:
        start = result.index("%")
        end = result.index("%", start + 1) if "%" in result[start + 1:] else -1
        if end == -1:
            break
        var = result[start + 1:end]
        # Convert dotted variable reference
        var = var.replace(".", "_")
        result = result[:start] + var + result[end + 1:]
    return result


def _lua_str(s: str) -> str:
    """Escape a string for Lua."""
    escaped = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'
