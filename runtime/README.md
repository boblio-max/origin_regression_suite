# Layer 3: runtime (sVM) tests (roadmap)

Instruction-level tests for the stack VM: hand-assembled bytecode sequences
with expected stack/variable/output state, so a failure here points at the
`sVM` dispatch loop instead of the compiler.

Planned shape per test: `program.obc`-ish payload (or builder script) +
`expected.json`, checked with a small `check_runtime.py` harness. Must stay in
lockstep with the Python, Rust, and Java VM mirrors.

Not started yet — Layer 1 (conformance) is the active suite.
