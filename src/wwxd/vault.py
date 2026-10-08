from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field
from importlib import resources
from pathlib import Path

import yaml

from wwxd.config import get_settings

STATUSES = ("candidate", "approved", "rejected", "fetched", "compiled", "failed")
TIMESTAMPED_PREFIXES = ("yt-", "pod-")
SOURCE_PREFIXES = ("yt-", "pod-", "web-", "file-")


@dataclass
class Member:
    id: str
    name: str
    aliases: list[str] = field(default_factory=list)

    @property
    def names(self) -> list[str]:
        return [self.name, *self.aliases]


@dataclass
class Source:
    id: str
    type: str  # youtube | web | podcast | file
    url: str
    title: str = ""
    status: str = "candidate"
    hint: str = ""  # own | appearance | maybe-about | manual | unknown
    channel: str = ""
    date: str = ""
    duration: float | None = None
    expected_speakers: list[str] = field(default_factory=list)
    found_via: str = ""
    transcript_url: str = ""  # podcasts: the feed's <podcast:transcript>, used instead of Whisper
    transcript_type: str = ""  # its MIME type as the feed gives it
    error: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in ("", None, [])}


class Vault:
    def __init__(self, path: Path):
        self.path = path
        self.config: dict = yaml.safe_load((path / "vault.yaml").read_text(encoding="utf-8")) or {}

    # --- paths -------------------------------------------------------------
    @property
    def slug(self) -> str:
        return self.config.get("slug") or self.path.name

    @property
    def raw_dir(self) -> Path:
        return self.path / "raw"

    @property
    def wiki_dir(self) -> Path:
        return self.path / "wiki"

    @property
    def derived_dir(self) -> Path:
        return self.path / "derived"

    @property
    def cache_dir(self) -> Path:
        return self.path / ".cache"

    @property
    def layout(self) -> str:
        return self.config.get("layout", "tree")

    @property
    def members(self) -> list[Member]:
        return [
            Member(id=m["id"], name=m["name"], aliases=list(m.get("aliases") or []))
            for m in self.config.get("members") or []
        ]

    @property
    def discovery(self) -> dict:
        return self.config.get("discovery") or {}

    def raw_path(self, source_id: str) -> Path:
        return self.raw_dir / f"{source_id}.md"

    # --- sources -----------------------------------------------------------
    def load_sources(self) -> list[Source]:
        path = self.path / "sources.yaml"
        if not path.exists():
            return []
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return [Source(**item) for item in data.get("sources") or []]

    def save_sources(self, sources: list[Source]) -> None:
        payload = {"sources": [s.to_dict() for s in sources]}
        (self.path / "sources.yaml").write_text(
            "# Managed by `wwxd`. Edit `status` by hand or with `wwxd approve/reject`.\n"
            + yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=120),
            encoding="utf-8",
        )

    def append_log(self, line: str) -> None:
        today = dt.date.today().isoformat()
        with (self.path / "log.md").open("a", encoding="utf-8") as fh:
            fh.write(f"- {today} {line}\n")


def resolve_vault(name_or_path: str) -> Vault:
    candidate = Path(name_or_path)
    if (candidate / "vault.yaml").exists():
        return Vault(candidate.resolve())
    home_path = get_settings().home / name_or_path
    if (home_path / "vault.yaml").exists():
        return Vault(home_path)
    raise FileNotFoundError(
        f"No vault '{name_or_path}' (looked in ./{name_or_path} and {home_path}). "
        "Create one with `wwxd new`."
    )


def list_examples() -> list[str]:
    root = resources.files("wwxd") / "examples"
    return sorted(p.name for p in root.iterdir() if (p / "vault.yaml").is_file())


def example_config(name: str) -> str:
    path = resources.files("wwxd") / "examples" / name / "vault.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Unknown example '{name}'. Available: {', '.join(list_examples())}")
    return path.read_text(encoding="utf-8")


def _template(name: str) -> str:
    return (resources.files("wwxd") / "templates" / name).read_text(encoding="utf-8")


def create_vault(path: Path, config_text: str) -> Vault:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"{path} already exists and is not empty")
    config = yaml.safe_load(config_text)
    for d in ("raw", "derived", "wiki", ".cache"):
        (path / d).mkdir(parents=True, exist_ok=True)
    (path / "vault.yaml").write_text(config_text, encoding="utf-8")
    title = config.get("name", path.name)
    for template, target in (
        ("index.md", "wiki/index.md"),
        ("profile.md", "wiki/profile.md"),
        ("tensions.md", "wiki/tensions.md"),
    ):
        (path / target).write_text(_template(template).replace("{{name}}", title), encoding="utf-8")
    (path / "derived" / "README.md").write_text(_template("derived_readme.md"), encoding="utf-8")
    (path / "log.md").write_text(f"# Log: {title}\n\n", encoding="utf-8")
    vault = Vault(path)
    vault.save_sources([])
    vault.append_log("created vault")
    return vault
