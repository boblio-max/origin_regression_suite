#!/usr/bin/env python3
"""Origin regression suite runner — Layer 1: conformance (Origin <-> Python differential).

For every test in ``conformance/T*/`` this runs the Origin program through the
Origin CLI and the Python reference through the Python CLI, then compares
observable stdout.

Why stdout comparison (and not exit codes)? Origin's runner currently exits 0
even on compile errors, so pass/fail is decided on output equality plus an
error-marker scan of Origin's stderr.

Usage:
    python run_suite.py                  # full suite, summary only
    python run_suite.py --verbose        # show stdout diffs on failure
    python run_suite.py --only T001      # run one test (prefix match)
    python run_suite.py --results-json out.json   # also write machine-readable results

Env:
    ORIGIN_REPO  path to an origin-dev checkout
                 (default: ../origin-dev, i.e. a sibling of this repo)

Exit code: 0 when every test passes, 1 otherwise (this is what makes CI red/green).
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

SUITE_ROOT = Path(__file__).resolve().parent
ORIGIN_REPO = Path(os.environ.get("ORIGIN_REPO", SUITE_ROOT.parent / "origin-dev"))
CONFORMANCE_DIR = SUITE_ROOT / "conformance"


def detect_origin_cmd(repo_root):
    """Return the CLI argv prefix that runs an Origin program in *repo_root*.

    Supports both known layouts so the same harness works against either SUT:

    - origin-dev (legacy): ``ORIGIN_CODE/runners/runnerMOD.py <file.or>``
    - origin (v1.7.27+ modular): ``python -m origin <file.or>`` (cwd=repo root)
    - legacy flat layout: ``runner.py <file.or>`` at the repo root
    """
    mod_runner = repo_root / "ORIGIN_CODE" / "runners" / "runnerMOD.py"
    if mod_runner.exists():
        return [sys.executable, str(mod_runner)]
    if (repo_root / "origin" / "runner.py").exists() or (repo_root / "origin" / "__main__.py").exists():
        return [sys.executable, "-m", "origin"]
    flat_runner = repo_root / "runner.py"
    if flat_runner.exists():
        return [sys.executable, str(flat_runner)]
    return None


ORIGIN_CMD_PREFIX = detect_origin_cmd(ORIGIN_REPO)
TIMEOUT_SECONDS = int(os.environ.get("ORIGIN_TEST_TIMEOUT", "30"))

# Origin prints diagnostics containing these markers on failure. The runner's
# exit code cannot be trusted (currently 0 even on syntax errors), so any test
# whose Origin output contains one of these markers is a FAIL.
ORIGIN_FAIL_MARKERS = ("[!]", "Traceback", "Syntax Error", "Unknown keyword")


def normalize(text):
    """Normalize stdout for comparison (CRLF + trailing whitespace)."""
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").splitlines()).strip()


def run_cli(cmd, cwd, stdin_text=None):
    """Run a CLI command; return (stdout, stderr, wall_seconds). Never raises."""
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        return proc.stdout, proc.stderr, time.perf_counter() - start, proc.returncode
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") if isinstance(getattr(e, "stdout", ""), str) else ""
        err = (e.stderr or "") if isinstance(getattr(e, "stderr", ""), str) else ""
        return out, err + "\n[TIMEOUT]", time.perf_counter() - start, 124


def peak_rss_kb():
    """Peak RSS of this process in KiB where the platform exposes it, else None."""
    try:
        import resource

        return resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    except Exception:
        return None


def run_test(test_dir):
    """Run one conformance test. Returns a result dict."""
    or_path = test_dir / "program.or"
    py_path = test_dir / "program.py"
    stdin_path = test_dir / "stdin.txt"
    stdin_text = stdin_path.read_text(encoding="utf-8") if stdin_path.exists() else None

    origin_cmd = ORIGIN_CMD_PREFIX + [str(or_path)]
    py_cmd = [sys.executable, str(py_path)]

    or_out, or_err, or_time, _ = run_cli(origin_cmd, cwd=ORIGIN_REPO, stdin_text=stdin_text)
    py_out, py_err, py_time, py_rc = run_cli(py_cmd, cwd=test_dir, stdin_text=stdin_text)

    or_norm, py_norm = normalize(or_out), normalize(py_out)
    origin_error = any(m in (or_out + or_err) for m in ORIGIN_FAIL_MARKERS)

    if py_rc != 0:
        status, reason = "ERROR", f"python reference exited {py_rc}: {py_err.strip()[:200]}"
    elif origin_error:
        status, reason = "FAIL", "origin runner reported an error"
    elif or_norm != py_norm:
        status, reason = "FAIL", "stdout mismatch"
    else:
        status, reason = "PASS", ""

    return {
        "name": test_dir.name,
        "status": status,
        "reason": reason,
        "origin_stdout": or_out,
        "origin_stderr": or_err,
        "python_stdout": py_out,
        "python_stderr": py_err,
        "origin_time_s": round(or_time, 3),
        "python_time_s": round(py_time, 3),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--only", metavar="PREFIX", help="run tests whose dirname starts with PREFIX")
    parser.add_argument("--results-json", metavar="FILE", help="write machine-readable results JSON")
    args = parser.parse_args()

    global ORIGIN_CMD_PREFIX
    # Re-detect in case ORIGIN_REPO was overridden via env after import.
    ORIGIN_CMD_PREFIX = detect_origin_cmd(ORIGIN_REPO)
    if not ORIGIN_CMD_PREFIX:
        sys.exit(
            f"origin runner not found in {ORIGIN_REPO} "
            "(looked for ORIGIN_CODE/runners/runnerMOD.py, origin/runner.py, runner.py; "
            "set ORIGIN_REPO env var)"
        )

    tests = sorted(p for p in CONFORMANCE_DIR.iterdir() if p.is_dir() and (p / "program.or").exists())
    if args.only:
        tests = [p for p in tests if p.name.startswith(args.only)]
    if not tests:
        sys.exit("no conformance tests found")

    results = [run_test(t) for t in tests]
    passed = [r for r in results if r["status"] == "PASS"]
    failed = [r for r in results if r["status"] != "PASS"]

    for r in results:
        if r["status"] != "PASS" or args.verbose:
            print(f"[{r['status']}] {r['name']}" + (f" — {r['reason']}" if r["reason"] else ""))
            if r["status"] != "PASS" and args.verbose:
                print("  --- origin stdout ---")
                print("  " + (r["origin_stdout"].strip() or "<empty>").replace("\n", "\n  "))
                print("  --- python stdout ---")
                print("  " + (r["python_stdout"].strip() or "<empty>").replace("\n", "\n  "))
                if r["origin_stderr"].strip():
                    print("  --- origin stderr (first 5 lines) ---")
                    print("  " + "\n  ".join(r["origin_stderr"].strip().splitlines()[:5]))

    total_or = sum(r["origin_time_s"] for r in results)
    total_py = sum(r["python_time_s"] for r in results)
    slowest = sorted(results, key=lambda r: r["origin_time_s"], reverse=True)[:5]
    rss = peak_rss_kb()

    print()
    print(f"{len(passed)} passed, {len(failed)} failed, {len(results)} total")
    print(f"wall time: origin {total_or:.1f}s, python {total_py:.1f}s", end="")
    print(f", peak child RSS: {rss} KiB" if rss is not None else " (peak RSS n/a on this platform)")
    print("slowest origin runs:")
    for r in slowest:
        print(f"  {r['origin_time_s']:.2f}s  {r['name']}")
    for r in failed:
        print(f"  FAIL {r['name']}: {r['reason']}")

    if args.results_json:
        import json

        Path(args.results_json).write_text(
            json.dumps({"passed": len(passed), "failed": len(failed), "results": results}, indent=2),
            encoding="utf-8",
        )

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
