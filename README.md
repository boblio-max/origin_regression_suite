# Origin Regression Suite

![regression](https://github.com/boblio-max/origin_regression_suite/actions/workflows/regression.yml/badge.svg)

ok so I built a whole programming language (Origin) and then immediately had the fear every language dev has: "did my last commit secretly break integer addition?" this repo is the answer — 100+ differential tests that run Origin and Python side by side on the same programs and scream if the outputs ever disagree.

```
You change Origin → commit/push → GitHub Actions
→ 100+ Origin <-> Python comparisons → GREEN (keep building) or RED (go fix it)
```

## how it actually works (three layers)

| layer | dir | question it answers | status |
|---|---|---|---|
| 1. conformance | `conformance/` | same observable output as Python? | ✅ 100 tests, active |
| 2. compiler | `compiler/` | source → expected bytecode/IR? | 🔲 roadmap |
| 3. runtime | `runtime/` | does the sVM nail each instruction? | 🔲 roadmap |

each test in `conformance/T*/` is a pair: `program.or` (run via the Origin CLI, auto-detected — `runnerMOD.py` for origin-dev, `python -m origin` for origin) + `program.py` (run via Python) + optional `stdin.txt`. PASS = identical normalized stdout. Origin's exit code can't be trusted (the runner exits 0 even on compile errors lol) so the harness also fails anything with error markers in the output.

## run it

```bash
git clone https://github.com/boblio-max/origin-dev.git
git clone https://github.com/boblio-max/origin_regression_suite.git
cd origin_regression_suite
python run_suite.py                  # full suite
python run_suite.py --only T001      # one test
python run_suite.py --verbose        # diffs on failure
```

`ORIGIN_REPO` env points at the language checkout (defaults to `../origin-dev`, works with `../origin` too).

## CI + email

every push, PR, nightly cron, and `origin-push` dispatch event runs the suite and emails results to the maintainer (Gmail SMTP via `MAIL_USERNAME`/`MAIL_PASSWORD` secrets, `results.json` attached). the `origin` repo has a notifier workflow that fires the dispatch on every `main` push, so new language commits get tested immediately.

## coverage (100 tests)

arithmetic (T001–T012) · variables (T013–T018) · comparisons/logic (T019–T026) · `if/elif/else` (T027–T034) · `while` (T035–T042) · `for`/`range` (T043–T050) · `break`/`continue` (T051–T056) · functions/recursion (T057–T064) · strings (T065–T074) · lists (T075–T086) · compound assignment (T087–T092) · math builtins (T093–T100).

## known gaps + real bugs found

differential testing already paid for itself — found a nested-loop `break` corrupting the outer iterator, double-recursion returning wrong fib values, `const pi` getting shadowed by math.pi, and `true` vs `True` casing. details + untested areas (colon syntax, classes, match/case, lib imports) in the old README sections — growing to 500+ tests is just adding directories, the harness auto-discovers `conformance/T*/`.
