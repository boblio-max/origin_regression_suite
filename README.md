# Origin Regression Suite

![regression](https://github.com/boblio-max/origin_regression_suite/actions/workflows/regression.yml/badge.svg)

Behavioral regression tests for the [Origin programming language](https://github.com/boblio-max/origin-dev):
every commit — plus a nightly run against `origin-dev@main` — gets an automated
check that Origin still behaves like the reference.

The ideal workflow:

```
You change Origin
       |
Commit / push
       |
GitHub Actions
       |
100+ Origin <-> Python comparisons
       |
   +---+---+
   |       |
 GREEN     RED
   |       |
Keep      Inspect
building  failure
```

A green check means: **the current Origin implementation passes the behavioral regression suite.**
A red check tells you exactly which behavior broke, so you spend your hour on
dialects, the sVM, or compiler architecture — not on wondering whether you
broke integer arithmetic in the parser.

## Layout (three layers)

| Layer | Dir | Question it answers | Status |
|---|---|---|---|
| 1. Conformance | `conformance/` | Does Origin produce the same observable result as the reference (Python)? | ✅ 100 tests, active |
| 2. Compiler | `compiler/` | Does source compile to the expected bytecode/IR? | 🔲 roadmap |
| 3. Runtime | `runtime/` | Does the sVM execute individual instructions correctly? | 🔲 roadmap |

A failure's layer tells you where the problem lives: source → compiler test
fails ⇒ compiler; bytecode → sVM test fails ⇒ runtime; output differs ⇒
reference comparison.

## Quick start

```bash
# origin-dev must be checked out next to this repo (or set ORIGIN_REPO)
git clone https://github.com/boblio-max/origin-dev.git
git clone https://github.com/boblio-max/origin_regression_suite.git

cd origin_regression_suite
python run_suite.py                  # full suite
python run_suite.py --only T001      # one test
python run_suite.py --verbose        # show diffs on failure
```

Each test in `conformance/T*/` is a pair:

- `program.or` — the Origin program (run via `ORIGIN_CODE/runners/runnerMOD.py`)
- `program.py` — the Python reference (run via `python`)
- `stdin.txt` — optional piped stdin for both

PASS = identical normalized stdout on both CLIs. Origin's exit code is not
trusted (the runner exits 0 even on compile errors), so the harness also fails
any test whose Origin output contains an error marker.

## Coverage (100 tests, day one)

Arithmetic (T001–T012) · variables (T013–T018) · comparisons/logic (T019–T026) ·
`if/elif/else` (T027–T034) · `while` (T035–T042) · `for`/`range` (T043–T050) ·
`break`/`continue` (T051–T056) · functions/recursion (T057–T064) ·
strings (T065–T074) · lists (T075–T086) · compound assignment (T087–T092) ·
math builtins (T093–T100).

## Known gaps (tracked, not covered yet)

These are broken or unverified in origin-dev today, so no tests depend on them.
Each is a future test batch once the language side is fixed:

- Lines containing `:` (typed `let x: int = ...`, dict literals) — currently
  hijacked by the `origin.toml` `$n:$v` dialect template.
- `class` instantiation (`12_oop` fixture fails with `'str' object is not callable`).
- `match`/`case` (reserved but unimplemented per `grammar/origin.peg.md`).
- `import` of `lib/*.or` modules (needs a lib-resolution story for CLI tests).
- `input`/stdin programs (harness supports `stdin.txt`; no tests yet).

## Bugs discovered while building this suite

The suite already paid for itself — differential testing surfaced two real
origin-dev bugs (reproduced on `runnerMOD.py`, VM mode) plus two behavior notes.
They are documented here instead of covered by tests, so the suite stays green
until origin-dev fixes them:

1. **Nested-loop `break` corrupts the outer loop variable.** In
   `for a in range(1, 3)` with an inner `for b` + `break`, Origin prints
   `11, 31, 32, 33` instead of `11, 21, 22` — the inner `break` advances the
   outer iterator. (T056 covers single-loop `break` instead.)
2. **Double recursion returns wrong values.** `fib` with two recursive calls
   per frame returns `-80` for `fib(10)` (expected `55`), even when the calls
   are split into temp variables. Single-recursion functions (`fact`, `gcd`,
   power in T059) work. (T058/T060/T059 cover those instead.)
3. **`const pi = ...` is silently replaced by math.pi.** Declaring
   `const pi = 3.14` yields `3.141592653589793`. Tests use other const names.
4. **Spelling: `true`, not `True`.** Origin only accepts lowercase `true`/`false`
   (Python accepts both cases for its own literals); tests use `true` in `.or`.

## Scaling up

Today 100 tests. The harness discovers `conformance/T*/` automatically, so
growing to 500 or 1,000+ tests is just adding directories — no harness changes.
