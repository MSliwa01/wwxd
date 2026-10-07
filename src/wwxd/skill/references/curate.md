# Curating sources

The wiki is only as faithful as its sources. Prefer fewer, long, first-hand sources
over many clips.

## Approve

- Long-form talks, lectures and essays by a member.
- Interviews and podcasts where a member is the **guest** or a co-host with real
  airtime. The title or description names them.
- Their own channel's long-form uploads (`own`).
- For group channels (`channel` hint): only videos where a member actually speaks.
  Check the title and description (e.g. "with Michael Seibel"). Outside guests on
  the YC channel are not YC partners.

## Reject

- `maybe-about`: summaries, "lessons from X", reactions, animated book
  summaries, compilations by third parties.
- Re-uploads of a talk you already have (same title on a random channel). Keep the
  official upload.
- Clips cut from a full episode you already have.
- Shorts and short highlights (they're usually filtered by `min_duration`).
- Wrong person with the same name.
- Videos where the member has a tiny cameo.

## Ask the user when

- The source is a debate or panel with many speakers (attribution gets hard).
- The member is the **host** interviewing others. Their questions reveal little;
  only approve if they share their own views often.
- The source is very old. It's still useful, but flag it so the timeline in
  `tensions.md` stays honest.

Present the candidates as a short grouped list ("12 own long-form talks:
approve; 7 third-party summaries: reject; 3 panels: your call") rather than
dumping every row.

## Using a cheaper model for triage

Triage only reads titles, channels and durations, so a cheaper, faster model does
it well. In Claude Code, hand the `wwxd sources <slug> --status candidate` output
to a subagent running a small model and ask for one `approve | reject | ask` line
per source. Any agent CLI works the same way (pass the list in the prompt, close
stdin). Review its picks with the user as usual.

Keep the strong model for compiling and answering. Attribution and synthesis are
where a vault stays faithful, and lint can catch an invented quote but not a real
quote credited to the wrong person.
