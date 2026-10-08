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

The vault grammar lives in `skills/wwxd/references/format.md`. If you change it,
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

## Releasing

`.github/workflows/release.yml` publishes to PyPI with trusted publishing, so the repo
holds no PyPI token.

One-time setup:

1. On pypi.org, open [Publishing](https://pypi.org/manage/account/publishing/) in your
   account and add a pending GitHub publisher with these values.

   | Field | Value |
   |---|---|
   | PyPI project name | `wwxd` |
   | Owner | `MSliwa01` |
   | Repository name | `wwxd` |
   | Workflow name | `release.yml` |
   | Environment name | `pypi` |

2. On GitHub, create an environment named `pypi` (Settings > Environments). Add
   yourself as a required reviewer if you want to approve each upload.

The first upload turns the pending publisher into a regular one.

To cut a release:

1. Set the new version in `pyproject.toml` and `src/wwxd/__init__.py` (a test fails
   if they differ), then run `uv lock`.
2. Merge to `main` and wait for CI to pass.
3. Tag the merge commit and push the tag.

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

The workflow checks that the tag matches the version, runs the tests, builds and
uploads. PyPI rejects a version it already has, so fix a bad release with a new
version, not a moved tag. The Claude Code plugin has no version of its own and
tracks `main`.
