"""Tests for class (직업) parser."""

import tempfile
from pathlib import Path

from genos.adapters.lpmud.class_parser import parse_classes

SAMPLE_JOB_H = """\
#ifndef __JOBH__
#define __JOBH__

static mapping *JobData = ({
([ "직업명" : "투사",     "선행능력" : ({  0, 0, 0, 0, 0, 0 }),
   "주요능력" : ({ 1,1,0,0,0,0 }), "기본유닛" :  6, "증가유닛" :  2,
   "증가멈춤" : 10, "직결직업" : ({ "전사" }),
   "관계직업" : ({ "기사", "상급기사", "신관기사", "아바타" }),
   "선행직업" : ({ }) ]),
([ "직업명" : "전사",     "선행능력" : ({  0, 0, 0, 0, 0, 0 }),
   "주요능력" : ({ 1,1,0,0,0,0 }), "기본유닛" : 10, "증가유닛" :  2,
   "증가멈춤" : 10, "직결직업" : ({ "기사" }),
   "관계직업" : ({ "투사", "상급기사", "신관기사", "아바타" }),
   "선행직업" : ({ "투사" }) ]),
});

#endif
"""


class TestClassParser:
    def test_parse_sample(self):
        with tempfile.NamedTemporaryFile(suffix=".h", delete=False) as f:
            f.write(SAMPLE_JOB_H.encode("euc-kr"))
            f.flush()
            classes = parse_classes(Path(f.name))

        assert len(classes) == 2

        c1 = classes[0]
        assert c1.id == 1
        assert c1.name == "투사"
        assert c1.hp_gain_min == 6
        assert c1.extensions["next_classes"] == ["전사"]
        assert c1.extensions["related_classes"] == ["기사", "상급기사", "신관기사", "아바타"]
        assert c1.extensions["prerequisite_classes"] == []
        assert c1.extensions["primary_stats"]["힘"] == 1
        assert c1.extensions["primary_stats"]["지혜"] == 0

        c2 = classes[1]
        assert c2.id == 2
        assert c2.name == "전사"
        assert c2.hp_gain_min == 10
        assert c2.extensions["prerequisite_classes"] == ["투사"]

    def test_real_file(self):
        real_path = Path("/home/genos/workspace/10woongi/lib/삽입파일/직업.h")
        if not real_path.exists():
            pytest.skip("10woongi data not available")
        classes = parse_classes(real_path)
        assert len(classes) == 14
        names = [c.name for c in classes]
        assert "투사" in names
        assert "아바타" in names
        assert "시공술사" in names


import pytest
