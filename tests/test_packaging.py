from importlib.metadata import version
from pathlib import Path

from typer.testing import CliRunner

import wwxd
from wwxd.cli import app


def test_install_skill_copies_skill_and_references(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["install-skill", "--project"])
    assert result.exit_code == 0, result.output
    skill = tmp_path / ".claude" / "skills" / "wwxd"
    assert (skill / "SKILL.md").is_file()
    assert (skill / "references" / "format.md").is_file()


def test_version_matches_pyproject():
    assert wwxd.__version__ == version("wwxd")


def test_vaults_lists_members(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from wwxd.cli import app
    from wwxd.vault import create_vault

    create_vault(tmp_path / "duo", "name: Duo\nslug: duo\nmembers:\n  - {id: a, name: Ann}\n  - {id: b, name: Bob}\n")
    (tmp_path / "duo" / "wiki" / "thinking").mkdir(parents=True)
    (tmp_path / "duo" / "wiki" / "thinking" / "a.md").write_text("x")
    monkeypatch.setenv("WWXD_HOME", str(tmp_path))
    out = CliRunner().invoke(app, ["vaults"]).output
    assert "duo" in out and "Ann  [thinking page]" in out and "Bob  [no thinking page]" in out
