"""Parse 기술.h (SkillData) header for skill definitions."""

from __future__ import annotations

import re
from pathlib import Path

from genos.uir.schema import Skill


def parse_skills(header_path: Path, encoding: str = "euc-kr") -> list[Skill]:
    """Parse 기술.h file into Skill list."""
    raw = header_path.read_bytes()
    text = raw.decode(encoding, errors="replace")

    skills: list[Skill] = []
    pattern = re.compile(r"\(\[\s*(.*?)\s*\]\)", re.DOTALL)

    for idx, m in enumerate(pattern.finditer(text)):
        block = m.group(1)
        skill = _parse_skill_block(block, idx + 1)
        if skill:
            skills.append(skill)

    return skills


def _parse_skill_block(block: str, index: int) -> Skill | None:
    """Parse a single SkillData mapping entry."""
    fields: dict[str, str] = {}
    for m in re.finditer(r'"([^"]+)"\s*:\s*("([^"]*)"|\d+)', block):
        key = m.group(1)
        val = m.group(3) if m.group(3) is not None else m.group(2)
        fields[key] = val

    name = fields.get("기술명", "")
    if not name:
        return None

    max_level = int(fields.get("최대", "1"))
    unit_cost = int(fields.get("단위", "0"))
    job_name = fields.get("직업", "")
    min_level = int(fields.get("레벨", "0"))

    # Parse job -> class_levels mapping
    # "직업" can be "투사", "모두", or "기사&사냥꾼"
    class_levels: dict[int, int] = {}
    if job_name and job_name != "모두":
        for job in job_name.split("&"):
            job = job.strip()
            if job:
                # We store job name as string key since class IDs
                # are not resolved here; adapter will resolve later
                class_levels[hash(job) & 0xFFFF] = min_level

    extensions: dict = {
        "korean_name": name,
        "max_level": max_level,
        "unit_cost": unit_cost,
        "job_name": job_name,
    }
    if min_level:
        extensions["min_level"] = min_level

    # Determine spell_type from name suffix pattern
    spell_type = "skill"

    return Skill(
        id=index,
        name=name,
        spell_type=spell_type,
        class_levels=class_levels,
        extensions=extensions,
    )
