"""Tests for skill (기술) parser."""

import tempfile
from pathlib import Path

import pytest

from genos.adapters.lpmud.skill_parser import parse_skills

SAMPLE_SKILL_H = """\
#ifndef __SKILLH__
#define __SKILLH__

static mapping *SkillData = ({
([ "기술명" : "패리L1", "최대" : 20, "단위" : 2, "직업" : "투사", "레벨" : 8 ]),
([ "기술명" : "치료L1", "최대" : 50, "단위" : 2, "직업" : "사제", "레벨" : 0 ]),
([ "기술명" : "방패방어L1", "최대" : 20, "단위" : 3, "직업" : "모두", "레벨" : 0 ]),
([ "기술명" : "연타L1", "최대" : 16, "단위" : 0, "직업" : "기사&사냥꾼", "레벨" : 0 ]),
});

#endif
"""


class TestSkillParser:
    def test_parse_sample(self):
        with tempfile.NamedTemporaryFile(suffix=".h", delete=False) as f:
            f.write(SAMPLE_SKILL_H.encode("euc-kr"))
            f.flush()
            skills = parse_skills(Path(f.name))

        assert len(skills) == 4

        s1 = skills[0]
        assert s1.id == 1
        assert s1.name == "패리L1"
        assert s1.extensions["max_level"] == 20
        assert s1.extensions["unit_cost"] == 2
        assert s1.extensions["job_name"] == "투사"
        assert s1.extensions["min_level"] == 8

        # 모두 = all classes, no specific class_levels
        s3 = skills[2]
        assert s3.name == "방패방어L1"
        assert s3.class_levels == {}

        # Multi-class skill
        s4 = skills[3]
        assert s4.name == "연타L1"
        assert s4.extensions["job_name"] == "기사&사냥꾼"

    def test_real_file(self):
        real_path = Path("/home/genos/workspace/10woongi/lib/삽입파일/기술.h")
        if not real_path.exists():
            pytest.skip("10woongi data not available")
        skills = parse_skills(real_path)
        assert len(skills) >= 48
        names = [s.name for s in skills]
        assert "패리L1" in names
        assert "소환L1" in names
