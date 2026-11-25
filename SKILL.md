---
name: stale-fact-watch
description: Keep claims in your published pages true. Claude extracts checkable facts (price, plan, free tier, limit, trial length) from your pages into facts.json, each with the vendor page that proves it. A script fetches each vendor page (or reads saved HTML with --offline), checks whether the claimed value still sits near the attribute keyword, and flags OK, CHANGED (shows the new candidate value), STALE (value shown struck through or retired), NOT FOUND or FETCH ERROR. A history file shows what changed since last week. Output is a weekly Markdown report sorted by risk. Use when the user says "are my prices still right", "check my comparison pages for outdated facts", "stale pricing watch", "vendor changed their plan", "weekly fact check".
---

# Stale fact watch

## Steps

1. Get the list of pages to protect: published URLs or local HTML or Markdown files. Read each one. If it is a URL, fetch it (WebFetch).
2. Extract claims that can go out of date. Per claim write one entry in `facts.json` (shape in `references/facts-shape.md`):
   - `id`: short unique slug.
   - `entity`: vendor and plan, for example "Acme CRM Pro plan".
   - `attribute`: price, free tier, contact limit, trial length.
   - `value`: the claim exactly as written on the page, with its unit ("$29", "500 contacts", "14-day free trial").
   - `source_url`: the VENDOR's own page that states it. Find it. Do not use a review site.
   - `keywords`: 1 to 3 words printed next to the value on the vendor page (the plan name, "per month"). This keeps the check tight.
   - `our_page`: the file or URL where the claim appears (optional). The report shows whether it still says the claim.
   - `priority`: high, medium or low (optional). High means a money page or heavy traffic.
3. Run from the skill folder:

```bash
uv run --python 3.12 scripts/watch.py --facts facts.json --history history.json --out weekly-report.md
```

   For tests or saved pages use `--offline DIR`. Saved file names are the URL host and path with symbols turned into underscores, for example `acme.example.com_pricing.html`. Keep `history.json` between runs. Run weekly.
4. Show the report. For every CHANGED, STALE or NOT FOUND row: open the vendor page yourself, confirm the new value, then propose the edit for the user's page (old value, new value, the file). Do not edit pages unless asked.
5. For FETCH ERROR (login wall, bot block, timeout): say so. Do not guess. Ask the user to save the page as HTML and rerun with `--offline`.

## Statuses

- OK: the claimed value is near a keyword and not marked old.
- CHANGED: a keyword is on the page, the claimed value is not near it, and a different value of the same kind (money, percent, number with the same unit) is. The report lists up to 3 candidates. A candidate is a lead, not a confirmed replacement.
- STALE: the claimed value is near a keyword but struck through (`<s>`, `<del>`) or beside words like "no longer", "previously", "legacy", "discontinued".
- NOT FOUND: no keyword on the page, or the keyword is there but neither the claimed value nor a replacement is.
- FETCH ERROR: page could not be read.

Matching is whole-number: a claim of `$9` does not match `$99`. Risk = status weight (CHANGED 4, STALE 3, NOT FOUND 3, FETCH ERROR 2, OK 0) x priority weight (high 3, medium 2, low 1).

## Limits

- Prices that load by JavaScript, depend on country, or sit behind a toggle (monthly or annual) may be missed. The script reads the HTML it gets.
- Respect the vendor's robots.txt and terms. The script makes one request per source page.
- This is a helper, not professional advice. Check the figures before you act.
