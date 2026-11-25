# stale-fact-watch

Comparison and review pages state prices, limits and plans. Vendors change them without telling you. This skill checks each claim against the vendor's own page every week and tells you what moved.

## Install

```bash
git clone https://github.com/umerdarazkha-debug/stale-fact-watch ~/.claude/skills/stale-fact-watch
```

Copy to `~/.claude/skills/stale-fact-watch/`. Needs `uv`. Standard library only.

## Use

Ask Claude: "Check my pricing pages for stale facts." Claude extracts `facts.json`, then runs `scripts/watch.py`. See `SKILL.md`. Schedule it weekly yourself if you want a routine. This skill does not create schedules.

## Test

`bash tests/run.sh`. Saved HTML for two weeks: one price changed, one same, one section removed, one struck-through price, a `$9` vs `$99` trap, a missing page, and the history diff between runs. Offline.

## Limits

HTML only. Pages that build prices with JavaScript need a saved copy. Candidates are leads, not proof.

## License

MIT
