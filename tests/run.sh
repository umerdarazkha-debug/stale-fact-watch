#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
PY="uv run --python 3.12 scripts/watch.py"
F=tests/fixtures
fail=0
python3 tests/build_fixtures.py || exit 1
H="$(mktemp -d)/history.json"
has() { if grep -qF -- "$3" <<<"$2"; then echo "ok   $1"; else echo "FAIL $1: missing '$3'"; fail=1; fi; }
not() { if grep -qF -- "$3" <<<"$2"; then echo "FAIL $1: should not contain '$3'"; fail=1; else echo "ok   $1"; fi; }

# Week 1 (first run)
out=$($PY --facts $F/facts.json --history "$H" --offline $F/week1 --today 2026-11-19)
has w1-same     "$out" "| 0 | OK | acme-pro-price: Acme CRM Pro plan price | \$29 | - | yes |"
has w1-unit-ok  "$out" "| 0 | OK | beta-free-limit: Beta Mail Free plan contact limit | 500 contacts | - | no |"
# \$9 claimed, page says \$99: must be CHANGED, not OK
has w1-9-vs-99  "$out" "| 8 | CHANGED | gamma-starter-price: Gamma Starter plan price | \$9 | \$99 |"
has w1-stale    "$out" "| 6 | STALE | echo-annual-price: Echo Annual plan price | \$20 | \$30 |"
has w1-fetcherr "$out" "| 4 | FETCH ERROR | fox-price"
has w1-first    "$out" "First run. Nothing to compare."
has w1-notice   "$out" "This is a helper, not professional advice. Check the figures before you act."

# Week 2: price changed, one same, one removed
out=$($PY --facts $F/facts.json --history "$H" --offline $F/week2 --today 2026-11-26)
has w2-changed  "$out" "| 12 | CHANGED | acme-pro-price: Acme CRM Pro plan price | \$29 | \$35 | yes |"
has w2-same     "$out" "| 0 | OK | beta-free-limit"
has w2-removed  "$out" "| 3 | NOT FOUND | delta-trial"
# sorted by risk: first data row is the highest risk
first=$(grep -m1 '^| [0-9]' <<<"$out")
has w2-sorted   "$first" "acme-pro-price"
# history diff from week 1 to week 2
has diff-from   "$out" "Compared with the run on 2026-11-19."
has diff-acme   "$out" "- acme-pro-price: OK -> CHANGED (candidates: \$35)"
has diff-delta  "$out" "- delta-trial: OK -> NOT FOUND"
not diff-beta   "$out" "- beta-free-limit:"
not diff-gamma  "$out" "- gamma-starter-price:"
[ "$(jq '.runs|length' "$H")" -eq 2 ] && echo "ok   history-two-runs" || { echo "FAIL history"; fail=1; }

# Same data again: no changes
out=$($PY --facts $F/facts.json --history "$H" --offline $F/week2 --today 2026-12-03)
has nochange "$out" "No status changes."

# Bad facts file (missing fields) must fail
echo '[{"id":"x"}]' > "$(dirname "$H")/bad.json"
$PY --facts "$(dirname "$H")/bad.json" --history "$H" --offline $F/week2 >/dev/null 2>&1 && { echo "FAIL bad-facts accepted"; fail=1; } || echo "ok   bad-facts rejected"

[ $fail -eq 0 ] && echo "ALL PASS" || { echo "FAILED"; exit 1; }
