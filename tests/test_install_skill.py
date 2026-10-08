from pathlib import Path

from typer.testing import CliRunner

from wwxd.cli import app


def test_install_skill_copies_skill_and_references(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["install-skill", "--project"])
    assert result.exit_code == 0, result.output
    skill = tmp_path / ".claude" / "skills" / "wwxd"
    assert (skill / "SKILL.md").is_file()
    assert (skill / "references" / "format.md").is_file()
