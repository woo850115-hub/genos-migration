"""Tests for command parser."""

from pathlib import Path

from genos.adapters.lpmud.command_parser import parse_all_commands


SAMPLE_CMD = """\
#include <구조.h>
inherit LIB_DAEMON;

string *getCMD()
{
  return ({ "공", "공격", "때려", "쳐" });
}

mixed CMD(string str)
{
  return 1;
}
"""


class TestCommandParser:
    def test_parse_command(self, tmp_path):
        cmd_dir = tmp_path / "명령어" / "플레이어"
        cmd_dir.mkdir(parents=True)

        (cmd_dir / "때려.c").write_bytes(SAMPLE_CMD.encode("euc-kr"))

        commands = parse_all_commands(cmd_dir)

        assert len(commands) == 1
        cmd = commands[0]
        assert cmd.name == "공"
        assert cmd.handler == "때려"
        assert "공격" in cmd.description
        assert "때려" in cmd.description

    def test_empty_dir(self, tmp_path):
        commands = parse_all_commands(tmp_path / "nonexistent")
        assert commands == []

    def test_real_files(self):
        real_dir = Path("/home/genos/workspace/10woongi/lib/명령어/플레이어")
        if not real_dir.exists():
            return
        commands = parse_all_commands(real_dir)
        assert len(commands) >= 50
