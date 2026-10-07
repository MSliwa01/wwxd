# Contributing

Thanks for helping. The most useful contributions, roughly in order:

1. **Gold sets** for the example vaults (`bench/gold/`): questions tied to specific public sources, including `expect: abstain` questions.
2. **Bench results**: tree vs. flat, prompt and skill variants. Open a PR with the numbers and the setup.
3. **Fetchers** for new source types.
4. **Example recipes** (`src/wwxd/examples/<name>/vault.yaml`): source configs only, never content. Prefer people with lots of first-hand, long-form, publicly available material.

## Dev setup

```bash
uv sync --group dev
uv run pytest
uv run wwxd --help
```

The vault grammar lives in `src/wwxd/skill/references/format.md`. If you change it,
change `src/wwxd/lint.py` and the tests in the same PR.

## Fetcher plugins

A fetcher turns an approved source into a raw doc. Plugins are ordinary Python
packages that register under the `wwxd.fetchers` entry point:

```toml
# your plugin's pyproject.toml
[project.entry-points."wwxd.fetchers"]
epub = "wwxd_epub:fetch"
```

```python
# wwxd_epub.py
import datetime as dt
from pathlib import Path

from wwxd.rawdoc import RawDoc


def fetch(source, vault, **options):
    if source.type != "file" or not source.url.endswith(".epub"):
        return None  # not mine; let other fetchers try
    text = my_epub_to_text(Path(source.url))
    return RawDoc(
        meta={
            "id": source.id,
            "type": "file",
            "url": source.url,
            "title": source.title,
            "date": source.date,
            "transcript": "file",
            "expected_speakers": source.expected_speakers,
            "fetched": dt.date.today().isoformat(),
        },
        body=text,
    )
```

Plugins run before the built-in fetchers. Only fetch content the user is allowed
to access. Plugins that pull from piracy sites won't be accepted into this repo
or linked from it.

## Ground rules

- Never commit vault content (`vaults/` is gitignored).
- Keep the CLI deterministic; judgment belongs in the skill.
- Every claim in a vault must stay checkable against `raw/`.
