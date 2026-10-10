# Changelog

## 0.1.0 (2026-10-11)

First release.

- Build a vault from YouTube videos, podcast feeds, articles and local files:
  `discover`, curate with `approve` and `reject`, `fetch`. Captions first, then
  transcripts published in podcast feeds, then local Whisper (`wwxd[whisper]`).
- A Claude Code skill compiles each source into a tree of cited wiki pages and
  answers "what would X do?" as plain advice with the sources listed underneath.
  It also covers group vaults, thinking pages (how a person decides), panels of
  several people, and keeping a vault current with `update`.
- `wwxd lint` checks every quote against the raw transcripts. `wwxd voice` checks
  who said each quote by voice (`wwxd[voice]`).
- `wwxd estimate` prices compiling and asking per model before you spend anything.
- `wwxd health`, `timeline`, `digest`, `search`, `status`, `doctor`.
- `wwxd bench` runs blind comparisons with any agent as the answerer or the judge.
  Results are in `bench/RESULTS.md`.
- Install as a Claude Code plugin (`/plugin marketplace add MSliwa01/wwxd`) or with
  `wwxd install-skill`.
