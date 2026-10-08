from typer.testing import CliRunner

import wwxd.discover
from wwxd.cli import app
from wwxd.vault import Source
from tests.test_lint import vault  # noqa: F401  (fixture)


def test_update_approves_only_new_candidates_and_fetches(vault, tmp_path, monkeypatch):  # noqa: F811
    talk = tmp_path / "talk.txt"
    talk.write_text("A new talk by PG.")
    vault.save_sources(vault.load_sources() + [
        Source(id="file-old", type="file", url=str(talk), status="candidate", hint="own"),
    ])
    fresh = [
        Source(id="file-new-talk", type="file", url=str(talk), status="candidate", hint="own"),
        Source(id="file-summary", type="file", url=str(talk), status="candidate", hint="maybe-about"),
    ]
    monkeypatch.setattr(wwxd.discover, "discover", lambda v, per_query=None: (fresh, []))
    monkeypatch.setenv("WWXD_DOWNLOAD_DELAY", "0")

    result = CliRunner().invoke(app, ["update", str(vault.path), "--approve-hint", "own", "--fetch"])
    assert result.exit_code == 0, result.output
    assert "Approved 1 new candidate with hint own" in result.output
    status = {s.id: s.status for s in vault.load_sources()}
    assert status["file-new-talk"] == "fetched"
    assert status["file-old"] == "candidate"  # left pending by the user, not auto-approved
    assert status["file-summary"] == "candidate"
    assert vault.raw_path("file-new-talk").exists()
    log = (vault.path / "log.md").read_text()
    assert "auto-approved 1 new candidate (own)" in log and "fetched 1 sources" in log


def test_update_without_options_only_discovers(vault, monkeypatch):  # noqa: F811
    fresh = [Source(id="file-x", type="file", url="/nowhere.txt", status="candidate", hint="own")]
    monkeypatch.setattr(wwxd.discover, "discover", lambda v, per_query=None: (fresh, []))
    result = CliRunner().invoke(app, ["update", str(vault.path)])
    assert result.exit_code == 0, result.output
    assert {s.id: s.status for s in vault.load_sources()}["file-x"] == "candidate"
    assert "Fetched" not in result.output
