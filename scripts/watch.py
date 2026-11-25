#!/usr/bin/env python3
"""Check claimed vendor facts (price, plan, limit) against the vendor's own page.

Usage:
  uv run --python 3.12 scripts/watch.py --facts facts.json --history history.json [--offline DIR]
      [--today 2026-11-26] [--window 120] [--out report.md] [--json out.json]
"""
import argparse, datetime as dt, html, json, os, re, sys, urllib.request
from urllib.parse import urlparse

NOTICE = "This is a helper, not professional advice. Check the figures before you act."
RETIRED = ["no longer", "previously", "formerly", "legacy", "discontinued", "deprecated", "retired", "sunset", "ended", "was available"]
WEIGHT = {"high": 3, "medium": 2, "low": 1}
BASE = {"CHANGED": 4, "STALE": 3, "NOT FOUND": 3, "FETCH ERROR": 2, "OK": 0}
CUR = r"[$€£]\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s?(?:USD|EUR|GBP|PKR)\b"


def slug(url):
    p = urlparse(url)
    return re.sub(r"[^A-Za-z0-9.]+", "_", (p.netloc + p.path).strip("/")) + ".html"


def to_text(raw):
    raw = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<(del|s|strike)\b[^>]*>(.*?)</\1>", lambda m: " [[STRUCK: %s]] " % re.sub(r"<[^>]+>", "", m.group(2)), raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    t = html.unescape(raw).replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()


def fetch(url, offline):
    if offline:
        f = os.path.join(offline, slug(url))
        if not os.path.exists(f):
            raise OSError("no saved page %s" % f)
        return open(f, encoding="utf-8", errors="replace").read()
    req = urllib.request.Request(url, headers={"User-Agent": "stale-fact-watch/1.0 (+file-based checker)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")


def value_re(v):
    v = v.strip()
    body = r"\s+".join(re.escape(x) for x in v.split())
    pre = r"(?<![\d.,])" if v[0].isdigit() else ""
    post = r"(?!\d|[.,]\d)" if v[-1].isdigit() else (r"(?![A-Za-z])" if v[-1].isalpha() else "")
    return re.compile(pre + body + post, re.I)


def kind(v):
    v = v.strip()
    if re.match(r"^[$€£]", v) or re.search(r"\b(USD|EUR|GBP|PKR)\b", v):
        return "money", None
    if v.endswith("%"):
        return "percent", None
    m = re.match(r"^\d[\d,\.]*\s*([A-Za-z][A-Za-z/\- ]*)$", v)
    if m:
        return "unit", m.group(1).strip().split()[0]
    if re.match(r"^\d[\d,\.]*$", v):
        return "number", None
    return "text", None


def candidates(window, kd, unit):
    if kd == "money":
        pat = CUR
    elif kd == "percent":
        pat = r"\d+(?:\.\d+)?\s?%"
    elif kd == "unit":
        pat = r"(?<![\d.,])\d[\d,]*(?:\.\d+)?\s?" + re.escape(unit) + r"\b"
    elif kd == "number":
        pat = r"(?<![\d.,$])\d[\d,]*(?:\.\d+)?(?![\d%])"
    else:
        return []
    return [m.group(0).strip() for m in re.finditer(pat, window, re.I)]


def check(fact, text, win):
    kws = fact.get("keywords") or [fact["attribute"], fact["entity"]]
    vr = value_re(fact["value"])
    kd, unit = kind(fact["value"])
    wins, found_kw = [], False
    for kw in kws:
        for m in re.finditer(re.escape(kw), text, re.I):
            found_kw = True
            wins.append(text[max(0, m.start() - win): m.end() + win])
    if not found_kw:
        return "NOT FOUND", [], "None of the keywords %s appear on the source page. The section may have been removed or reworded." % kws
    for w in wins:
        for m in vr.finditer(w):
            ctx = w[max(0, m.start() - 70): m.end() + 70].lower()
            struck = re.search(r"\[\[struck:[^\]]*" + vr.pattern + r"[^\]]*\]\]", w, re.I)
            if struck or any(r in ctx for r in RETIRED):
                cand = [c for ww in wins for c in candidates(ww, kd, unit) if not vr.fullmatch(c)]
                return "STALE", sorted(set(cand), key=cand.index)[:3], "The claimed value is on the page but shown as old (struck through or marked retired)."
            return "OK", [], "Claimed value found near the keyword."
    cand = []
    for w in wins:
        for c in candidates(w, kd, unit):
            if c not in cand and not vr.fullmatch(c):
                cand.append(c)
    if cand:
        return "CHANGED", cand[:3], "Claimed value is not near the keyword. Candidate values there: %s." % ", ".join(cand[:3])
    return "NOT FOUND", [], "Keyword is on the page but the claimed value is not near it and no replacement of the same kind was found."


def our_page_has(fact, base, offline, win):
    op = fact.get("our_page")
    if not op:
        return None
    try:
        if "://" in op:
            raw = fetch(op, offline)
        else:
            raw = open(os.path.join(base, op), encoding="utf-8", errors="replace").read()
    except Exception:
        return "unreadable"
    return "yes" if value_re(fact["value"]).search(to_text(raw)) else "no"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", required=True)
    ap.add_argument("--history", required=True)
    ap.add_argument("--offline")
    ap.add_argument("--today", default=dt.date.today().isoformat())
    ap.add_argument("--window", type=int, default=120)
    ap.add_argument("--out"); ap.add_argument("--json")
    a = ap.parse_args()

    facts = json.load(open(a.facts))
    if isinstance(facts, dict):
        facts = facts.get("facts", [])
    for f in facts:
        for k in ("id", "entity", "attribute", "value", "source_url"):
            if not f.get(k):
                sys.exit("ERROR: fact %s is missing '%s'" % (f.get("id", "?"), k))
    base = os.path.dirname(os.path.abspath(a.facts))
    hist = json.load(open(a.history)) if os.path.exists(a.history) else {"runs": []}
    prev = hist["runs"][-1] if hist["runs"] else None

    cache, res = {}, []
    for f in facts:
        u = f["source_url"]
        if u not in cache:
            try:
                cache[u] = to_text(fetch(u, a.offline))
            except Exception as e:
                cache[u] = e
        t = cache[u]
        if isinstance(t, Exception):
            st, cand, why = "FETCH ERROR", [], "Could not read the source page: %s" % t
        else:
            st, cand, why = check(f, t, a.window)
        w = WEIGHT.get(f.get("priority", "medium"), 2)
        res.append(dict(id=f["id"], entity=f["entity"], attribute=f["attribute"], claimed=f["value"], status=st, candidates=cand,
                        why=why, source_url=u, our_page=f.get("our_page"), on_our_page=our_page_has(f, base, a.offline, a.window),
                        risk=BASE[st] * w, priority=f.get("priority", "medium")))
    res.sort(key=lambda r: (-r["risk"], r["id"]))

    L = ["# Weekly stale fact report", "", "Run date: %s. Facts checked: %d." % (a.today, len(res)), NOTICE, "",
         "Statuses: OK = claimed value is near the keyword. CHANGED = keyword found, claimed value not near it, a different value of the same kind is. STALE = claimed value is on the page but marked old. NOT FOUND = keyword or value gone. FETCH ERROR = page could not be read.", "",
         "| Risk | Status | Fact | Claimed | Page says (candidates) | Our page has claim | Source |", "|---|---|---|---|---|---|---|"]
    for r in res:
        L.append("| %d | %s | %s: %s %s | %s | %s | %s | %s |" % (r["risk"], r["status"], r["id"], r["entity"], r["attribute"], r["claimed"],
                 ", ".join(r["candidates"]) or "-", r["on_our_page"] or "-", r["source_url"]))
    L += ["", "## Details", ""]
    for r in res:
        if r["status"] != "OK":
            L.append("- %s (%s): %s" % (r["id"], r["status"], r["why"]))
    L += ["", "## What changed since last run", ""]
    if not prev:
        L.append("First run. Nothing to compare.")
    else:
        L.append("Compared with the run on %s." % prev["date"])
        ch = 0
        for r in res:
            p = prev["results"].get(r["id"])
            if p is None:
                L.append("- %s: new fact, now %s" % (r["id"], r["status"])); ch += 1
            elif p["status"] != r["status"] or p.get("candidates") != r["candidates"]:
                L.append("- %s: %s -> %s%s" % (r["id"], p["status"], r["status"], (" (candidates: %s)" % ", ".join(r["candidates"])) if r["candidates"] else "")); ch += 1
        for pid in prev["results"]:
            if pid not in {r["id"] for r in res}:
                L.append("- %s: removed from the facts list" % pid); ch += 1
        if not ch:
            L.append("No status changes.")
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        open(a.out, "w").write(text)
    if a.json:
        json.dump(res, open(a.json, "w"), indent=2)
    hist["runs"].append(dict(date=a.today, results={r["id"]: dict(status=r["status"], candidates=r["candidates"]) for r in res}))
    hist["runs"] = hist["runs"][-26:]
    json.dump(hist, open(a.history, "w"), indent=2)


if __name__ == "__main__":
    main()
