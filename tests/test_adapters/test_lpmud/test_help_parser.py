"""Tests for help parser."""

from pathlib import Path

from genos.adapters.lpmud.help_parser import parse_all_help


class TestHelpParser:
    def test_parse_help_files(self, tmp_path):
        help_dir = tmp_path / "도움말"
        help_dir.mkdir()

        (help_dir / "때려.help").write_bytes(
            "선공을 하지 않는 몹을 때리는 방법이다.\n"
            "!C신선 때려!RR로 할수 있다.".encode("euc-kr")
        )
        (help_dir / "도움.help").write_bytes(
            "도움말을 볼 수 있습니다.".encode("euc-kr")
        )

        entries = parse_all_help(help_dir)

        assert len(entries) == 2
        names = {e.keywords[0] for e in entries}
        assert "때려" in names
        assert "도움" in names

        hit_entry = next(e for e in entries if e.keywords[0] == "때려")
        assert "선공" in hit_entry.text
        # Color codes should be stripped
        assert "!C" not in hit_entry.text

    def test_empty_dir(self, tmp_path):
        entries = parse_all_help(tmp_path / "nonexistent")
        assert entries == []

    def test_real_files(self):
        real_dir = Path("/home/genos/workspace/10woongi/lib/도움말")
        if not real_dir.exists():
            return
        entries = parse_all_help(real_dir)
        assert len(entries) >= 70
