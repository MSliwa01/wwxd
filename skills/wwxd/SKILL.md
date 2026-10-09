---
name: wwxd
description: Build and query "What would X do?" vaults, which are cited knowledge wikis of a specific person's (or group's) thinking compiled from their talks, podcasts and writing. Use when the user wants to know what a specific person (Hormozi, Paul Graham, Naval, YC, ...) thinks or would do about something, or to build, update, compile or lint a wwxd vault.
---

# wwxd

A vault (`vaults/<slug>/`) holds one person's or one group's documented thinking:
immutable `raw/` sources, a `wiki/` tree that you maintain, and `derived/` answers.
The `wwxd` CLI does the mechanical work (discover, fetch, lint, search). You do the
judgment work (curate with the user, compile, answer).

Run the CLI as `wwxd`. If it isn't installed, use `uvx --from git+https://github.com/MSliwa01/wwxd wwxd`. Vaults live in
`$WWXD_HOME` (default `./vaults`).

**Before writing anything into a vault, read `references/format.md`.** It is the
exact grammar that `wwxd lint` enforces.

## Pick the workflow

| User wants | Do |
|---|---|
| "What would X say/do about …?" for an existing vault | `references/ask.md` |
| A vault for a new person or group | **Set up** below, then curate, fetch, compile |
| To refresh a vault | `wwxd update <slug>`, then curate, fetch, compile |
| Pending sources compiled | `references/compile.md` |
| A vault health check | `wwxd health <slug>` and `wwxd lint <slug>`, then fix what they report |
| To build or refresh how a member thinks (values, rules, strong views) | `references/thinking.md` |
| To clean up a drifting wiki (health flags it, or ~10 sources since the last pass) | `references/consolidate.md` |

## Set up

1. `wwxd examples` lists bundled recipes. `wwxd new <slug> --example <name>` uses
   one; otherwise `wwxd new <slug> --name "Full Name"`.
2. Fill in `vault.yaml` together with the user. The person's **own** YouTube
   channels, their blog or Substack RSS, podcast feeds, and article index pages
   (`link_indexes` with a URL regex). Look these up yourself; don't make the user
   do it. For a group, list every member with an id and aliases.
3. `wwxd discover <slug>`.

## Curate (always with the user)

`wwxd sources <slug> --status candidate` shows hints:
`own` (their channel or site), `channel` (a group's channel, no member named),
`appearance` (a member is named in the title), `maybe-about` (probably commentary
on them), `unknown`.

Goal: content **by** the members, not **about** them. See `references/curate.md`.
Summarize the candidates for the user in groups, recommend what to approve and
what to reject, and wait for their decision. Then run `wwxd approve <slug> <ids…>`
(or `--hint own`) and `wwxd reject …`.

## Fetch

`wwxd fetch <slug>` (existing captions first; Whisper fallback, which needs
`wwxd[whisper]`). It's fine to fetch in batches with `--limit`.

## Compile

Follow `references/compile.md` for every source in `wwxd pending <slug>`.
After each source: run `wwxd lint <slug>`, fix every error, then
`wwxd mark-compiled <slug> <id> --note "…"`.

## Non-negotiables

- Every quote is verbatim from a raw doc and cited with timestamp, speaker and
  confidence. Lint checks quotes against the raw text. Don't argue with it; fix
  the quote.
- Only statements by a vault member count. Hosts, guests and people being
  quoted are not the member.
- Never write model opinions into `wiki/`. Synthesis that goes beyond the sources
  belongs in `derived/`.
- Answers lead with a verdict and say what it rests on: something they said, a
  principle of theirs applied to this case, or knowledge beyond the vault. Label
  extrapolation, but don't hide the answer behind it.
