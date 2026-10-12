# Keep a vault current

People keep publishing, so a vault goes stale. `wwxd update` finds new sources.
`--approve-hint own` approves the new ones from the person's own channels and feeds,
and `--fetch` downloads them. Candidates you left pending before stay pending, and
the other new ones wait for your review.

A weekly cron line covers the CLI part. On Windows use Task Scheduler.

```cron
# Mondays at 7:00
0 7 * * 1  WWXD_HOME=$HOME/vaults $HOME/.local/bin/wwxd update hormozi --approve-hint own --fetch >> $HOME/vaults/hormozi-update.log 2>&1
```

Compiling needs an agent. A Claude Code scheduled agent (`/schedule`) can run the
whole loop. It needs `wwxd` installed and access to the vault. Give it a prompt like
this one.

> Keep the hormozi wwxd vault current. Run
> `wwxd update hormozi --approve-hint own --fetch`, and list the other new
> candidates for me without approving them. Compile every source in
> `wwxd pending hormozi` with the wwxd skill (references/compile.md), running
> `wwxd lint hormozi` and `wwxd mark-compiled` after each one. Then run
> `wwxd health hormozi`, and if it asks for a consolidation pass, follow
> references/consolidate.md. Finish with `wwxd digest hormozi --days 7` and show
> me the digest.

`wwxd digest` writes a markdown note on what's new: the sources compiled, the leaves
created or updated, and new statements grouped by leaf. `--out` saves it, for
example into your notes app's folder.
